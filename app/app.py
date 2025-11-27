from gevent import monkey
monkey.patch_all()
# important for production - gevent is swapping out Python’s blocking I/O functions with cooperative versions,
# so the app can handle thousands of concurrent SSE connections without threads.

import json
import time
import threading
import queue
from flask import Flask, render_template, jsonify, Response, request, stream_with_context
from kubernetes import client, config, watch

from .backend import backend

app = Flask(__name__, template_folder='./templates')
kuyala_backend = backend.Backend()

# Global message queue for SSE broadcasting
message_queue = queue.Queue(maxsize=100)
connected_clients = []
clients_lock = threading.Lock()

config_error = ""
if not kuyala_backend.client:
    config_error = "Configuration error: KUBECONFIG or KUBERNETES_SERVICE_HOST environment variable is not set and not running in-cluster."
    kuyala_backend.logging.error(config_error)


class SSEClient:
    """Represents a single SSE client connection"""
    def __init__(self, client_id):
        self.id = client_id
        self.queue = queue.Queue(maxsize=50)
        self.connected = True


def broadcast_message(message):
    """Broadcast message to all connected SSE clients"""
    with clients_lock:
        for client in connected_clients:
            try:
                if client.connected:
                    client.queue.put_nowait(message)
            except queue.Full:
                kuyala_backend.logging.warning(f"Queue full for client {client.id}, dropping message")


def watch_deployments():
    """
    Watch Kubernetes deployments for changes and broadcast via SSE.
    This runs in a background thread.
    """
    if not kuyala_backend.client:
        kuyala_backend.logging.error("Cannot start deployment watcher: K8s client not initialized")
        return

    kuyala_backend.logging.info("Starting Kubernetes deployment watcher...")

    while True:
        try:
            v1_apps = client.AppsV1Api(kuyala_backend.client)
            w = watch.Watch()

            # Watch all deployments with kuyala annotation across all namespaces
            for event in w.stream(v1_apps.list_deployment_for_all_namespaces, timeout_seconds=0):
                event_type = event['type']  # ADDED, MODIFIED, DELETED
                deployment = event['object']

                # Only process deployments with kuyala.enabled annotation
                annotations = deployment.metadata.annotations or {}
                if "kuyala.enabled" not in annotations:
                    continue

                # Extract deployment data
                replicas_off = int(annotations.get("kuyala.replicasOff", 0))
                replicas_on = int(annotations.get("kuyala.replicasOn", 1))
                replicas_current = getattr(deployment.status, "replicas", 0) or 0

                deployment_data = {
                    "type": event_type,
                    "namespace": deployment.metadata.namespace,
                    "name": deployment.metadata.name,
                    "applicationName": annotations.get("kuyala.applicationName", deployment.metadata.name),
                    "backgroundColor": annotations.get("kuyala.backgroundColor", ""),
                    "textColor": annotations.get("kuyala.textColor", ""),
                    "replicasOff": replicas_off,
                    "replicasOn": replicas_on,
                    "replicasCurrent": replicas_current,
                    "timestamp": time.time()
                }

                kuyala_backend.logging.info(f"Deployment {event_type}: {deployment.metadata.namespace}/{deployment.metadata.name}")

                # Broadcast to all SSE clients
                message = {
                    "event": "deployment_update",
                    "data": deployment_data
                }
                broadcast_message(message)

        except Exception as e:
            kuyala_backend.logging.error(f"Error in deployment watcher: {str(e)}", exc_info=True)
            time.sleep(5)  # Wait before reconnecting
            kuyala_backend.logging.info("Reconnecting deployment watcher...")


# Start the deployment watcher in a background thread
if not config_error:
    watcher_thread = threading.Thread(target=watch_deployments, daemon=True)
    watcher_thread.start()


@app.route('/')
def main():
    return render_template('start.html', config_error=config_error)


@app.route('/events')
def events():
    """SSE endpoint for real-time updates"""

    def event_stream():
        client_id = f"client_{int(time.time())}_{id(threading.current_thread())}"
        sse_client = SSEClient(client_id)

        with clients_lock:
            connected_clients.append(sse_client)

        kuyala_backend.logging.info(f"SSE client connected: {client_id}. Total clients: {len(connected_clients)}")

        # Send initial connection message
        yield f"event: connected\ndata: {json.dumps({'client_id': client_id, 'message': 'Connected to Kuyala', 'server_node_name': kuyala_backend.master_node_name, 'server_node_ip': kuyala_backend.master_node_ip})}\n\n"

        # Send initial deployment list
        initial_data = kuyala_backend.get_current_list()
        if initial_data.get('status') == 'success':
            yield f"event: initial_data\ndata: {json.dumps(initial_data)}\n\n"

        try:
            last_heartbeat = time.time()

            while sse_client.connected:
                try:
                    # Check for messages in client queue (non-blocking with timeout)
                    message = sse_client.queue.get(timeout=1)

                    event_type = message.get('event', 'message')
                    data = message.get('data', message)

                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

                except queue.Empty:
                    # Send heartbeat every 30 seconds
                    current_time = time.time()
                    if current_time - last_heartbeat > 30:
                        yield f"event: heartbeat\ndata: {json.dumps({'timestamp': current_time})}\n\n"
                        last_heartbeat = current_time

        except GeneratorExit:
            # Client disconnected
            sse_client.connected = False
            with clients_lock:
                if sse_client in connected_clients:
                    connected_clients.remove(sse_client)
            kuyala_backend.logging.info(f"SSE client disconnected: {client_id}. Remaining clients: {len(connected_clients)}")
        except Exception as e:
            kuyala_backend.logging.error(f"Error in SSE stream for {client_id}: {str(e)}", exc_info=True)
            sse_client.connected = False
            with clients_lock:
                if sse_client in connected_clients:
                    connected_clients.remove(sse_client)

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )


# @app.route('/list')
# def list():
#     """Legacy endpoint - returns current deployment list"""
#     kuyala_backend.logging.debug("Request received for /list endpoint.")
#     return jsonify(kuyala_backend.get_current_list())
#

@app.route('/action', methods=['POST'])
def action():
    """Scale deployment endpoint"""
    try:
        req_data = request.get_json()

        if not req_data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        namespace = req_data.get('namespace')
        name = req_data.get('name')
        scale = req_data.get('scale')

        if not all([namespace, name, scale is not None]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: namespace, name, scale'
            }), 400

        kuyala_backend.logging.info(f"Action request: {namespace}/{name} -> {scale} replicas")

        result = kuyala_backend.action(req_data)

        if result is None:
            return jsonify({
                'status': 'error',
                'message': 'Failed to scale deployment'
            }), 500

        kuyala_backend.logging.info(f"Action successful: scaled to {result} replicas")

        return jsonify({
            'status': 'success',
            'scaled_to': result,
            'namespace': namespace,
            'name': name
        })

    except Exception as e:
        kuyala_backend.logging.error(f"Error in action endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'connected_clients': len(connected_clients),
        'k8s_connected': kuyala_backend.client is not None,
        'k8s_version': kuyala_backend.kubernetes_version,
        'master_node_ip': kuyala_backend.master_node_ip,
        'master_node_name': kuyala_backend.master_node_name,
        'timestamp': time.time()
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)