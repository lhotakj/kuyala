from gevent import monkey
monkey.patch_all()
# important for production - gevent is swapping out Python’s blocking I/O functions with cooperative versions,
# so the app can handle thousands of concurrent SSE connections without threads.

import json
import time
import threading
import queue
from contextlib import contextmanager
from flask import Flask, render_template, jsonify, Response, request, stream_with_context
from kubernetes import client, config, watch

from .backend import backend, __version__ as kuyala_version

app = Flask(__name__, template_folder='./templates')
kuyala_backend = backend.Backend()

# Global message queue for SSE broadcasting
message_queue = queue.Queue(maxsize=100)
connected_clients = []
clients_lock = threading.Lock()
# New queue for delayed stats updates
delayed_stats_queue = queue.Queue()


config_error = ""
if not kuyala_backend.client:
    config_error = "Configuration error: KUBECONFIG or KUBERNETES_SERVICE_HOST environment variable is not set and not running in-cluster."
    kuyala_backend.logging.error(config_error)


@app.context_processor
def inject_version():
    """Injects the application version into all templates."""
    return dict(kuyala_version=kuyala_version)


@contextmanager
def k8s_client_session(thread_name: str):
    """A context manager to ensure a valid K8s client is available for a thread."""
    is_valid = False
    try:
        kuyala_backend.k8s_auth_and_validate()
        if kuyala_backend.client:
            is_valid = True
        else:
            kuyala_backend.logging.error(f"{thread_name}: K8s client is not valid.")
    except Exception as e:
        kuyala_backend.logging.error(f"Error creating K8s session for {thread_name}: {e}", exc_info=True)
    
    yield is_valid


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
    kuyala_backend.logging.info("Starting Kubernetes deployment watcher...")
    while True:
        with k8s_client_session("Watcher") as is_ready:
            if not is_ready:
                time.sleep(30)
                continue
            
            try:
                v1_apps = client.AppsV1Api(kuyala_backend.client)
                w = watch.Watch()
                for event in w.stream(v1_apps.list_deployment_for_all_namespaces, timeout_seconds=0):
                    event_type = event['type']
                    deployment = event['object']

                    annotations = deployment.metadata.annotations or {}
                    if "kuyala.enabled" not in annotations:
                        continue

                    replicas_current = getattr(deployment.status, "replicas", 0) or 0

                    deployment_data = {
                        "type": event_type,
                        "namespace": deployment.metadata.namespace,
                        "name": deployment.metadata.name,
                        "applicationName": annotations.get("kuyala.applicationName", deployment.metadata.name),
                        "backgroundColor": annotations.get("kuyala.backgroundColor", ""),
                        "textColor": annotations.get("kuyala.textColor", ""),
                        "replicasOff": int(annotations.get("kuyala.replicasOff", 0)),
                        "replicasOn": int(annotations.get("kuyala.replicasOn", 1)),
                        "replicasCurrent": replicas_current,
                        "timestamp": time.time()
                    }

                    broadcast_message({
                        "event": "deployment_update",
                        "data": deployment_data
                    })
            except Exception as e:
                kuyala_backend.logging.error(f"Error in deployment watcher stream: {e}", exc_info=True)
                time.sleep(5)


def stats_updater():
    """Periodically fetches and broadcasts cluster stats."""
    kuyala_backend.logging.info("Starting stats updater thread...")
    while True:
        with k8s_client_session("StatsUpdater") as is_ready:
            if is_ready:
                try:
                    stats = kuyala_backend.get_cluster_stats()
                    if stats:
                        kuyala_backend.logging.info(f"Broadcasting stats update: {stats}")
                        broadcast_message({"event": "stats_update", "data": stats})
                except Exception as e:
                    kuyala_backend.logging.error(f"Error during stats calculation: {e}", exc_info=True)
        
        time.sleep(30)

def delayed_stats_trigger():
    """Waits for a signal, then triggers a stats update after a delay."""
    kuyala_backend.logging.info("Starting delayed stats trigger thread...")
    while True:
        try:
            # Wait for a signal from the action endpoint
            delayed_stats_queue.get()
            kuyala_backend.logging.info("Received signal for delayed stats update. Waiting 5 seconds...")
            time.sleep(5) # Wait for pods to potentially start/stop

            with k8s_client_session("DelayedStatsTrigger") as is_ready:
                if is_ready:
                    stats = kuyala_backend.get_cluster_stats()
                    if stats:
                        kuyala_backend.logging.info(f"Broadcasting delayed stats update: {stats}")
                        broadcast_message({"event": "stats_update", "data": stats})
        except Exception as e:
            kuyala_backend.logging.error(f"Error in delayed stats trigger: {e}", exc_info=True)


# Start the background threads
if not config_error:
    watcher_thread = threading.Thread(target=watch_deployments, daemon=True)
    watcher_thread.start()
    stats_thread = threading.Thread(target=stats_updater, daemon=True)
    stats_thread.start()
    delayed_stats_thread = threading.Thread(target=delayed_stats_trigger, daemon=True)
    delayed_stats_thread.start()


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

        yield f"event: connected\ndata: {json.dumps({'client_id': client_id, 'message': 'Connected to Kuyala', 'server_node_name': kuyala_backend.master_node_name, 'server_node_ip': kuyala_backend.master_node_ip})}\n\n"

        initial_data = kuyala_backend.get_current_list()
        if initial_data.get('status') == 'success':
            yield f"event: initial_data\ndata: {json.dumps(initial_data)}\n\n"
        
        initial_stats = kuyala_backend.get_cluster_stats()
        if initial_stats:
            yield f"event: stats_update\ndata: {json.dumps(initial_stats)}\n\n"

        try:
            last_heartbeat = time.time()
            while sse_client.connected:
                try:
                    message = sse_client.queue.get(timeout=1)
                    event_type = message.get('event', 'message')
                    data = message.get('data', message)
                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                except queue.Empty:
                    current_time = time.time()
                    if current_time - last_heartbeat > 30:
                        yield f"event: heartbeat\ndata: {json.dumps({'timestamp': current_time})}\n\n"
                        last_heartbeat = current_time
        except GeneratorExit:
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
            return jsonify({'status': 'error', 'message': 'Missing required fields: namespace, name, scale'}), 400

        kuyala_backend.logging.info(f"Action request: {namespace}/{name} -> {scale} replicas")
        result = kuyala_backend.action(req_data)

        if result is None:
            return jsonify({'status': 'error', 'message': 'Failed to scale deployment'}), 500

        kuyala_backend.logging.info(f"Action successful: scaled to {result} replicas")
        
        # Trigger a delayed stats update
        delayed_stats_queue.put("trigger")

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
        'timestamp': time.time(),
        'kuyala_version': kuyala_version
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
