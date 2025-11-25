import json
from datetime import time

from flask import Flask, render_template, jsonify
from kubernetes import client, config
from flask import Response
from backend import backend

app = Flask(__name__, template_folder='./templates')
kuyala_backend = backend.Backend()

@app.route('/')
def main():
    return render_template('start.html')

@app.route('/list')
def list():
    return jsonify(kuyala_backend.get_current_list())

@app.route('/list_stream')
def list_stream():
    def event_stream():
        while True:
            data = kuyala_backend.get_current_list() # Your function to get data
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(2)  # Adjust interval as needed
    return Response(event_stream(), mimetype="text/event-stream")

from flask import request

# Use the actual deployment name, not the display name from annotations
@app.route('/action', methods=['POST'])
def action():
    data = request.get_json()
    namespace = data.get('namespace')
    name = data.get('name')  # This must match the deployment metadata.name exactly
    scale = int(data.get('scale', 1))

    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    body = {'spec': {'replicas': scale}}
    apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
    return jsonify({'status': 'success', 'scaled_to': scale})


if __name__ == '__main__':
    app.run(debug=True)