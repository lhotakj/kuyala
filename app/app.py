import json
import time
import os
import logging
from flask import Flask, render_template, jsonify, Response, request
from kubernetes import client, config

from .backend import backend


app = Flask(__name__, template_folder='./templates')
kuyala_backend = backend.Backend()
config_error = ""
if not kuyala_backend.client:
    config_error = "Configuration error: KUBECONFIG or KUBERNETES_SERVICE_HOST environment variable is not set and not running in-cluster."
    kuyala_backend.logging.error(config_error)

@app.route('/')
def main():
    return render_template('start.html', config_error=config_error)

@app.route('/list')
def list():
    kuyala_backend.logging.debug("Request received for /list endpoint.")
    return jsonify(kuyala_backend.get_current_list())


@app.route('/list_stream')
def list_stream():
    kuyala_backend.logging.debug("Request received for /list_stream endpoint.")
    def event_stream():
        while True:
            data = kuyala_backend.get_current_list()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/action', methods=['POST'])
def action():
    req_data = request.get_json()
    kuyala_backend.logging.info(f"Action request received: {req_data}")
    scale = kuyala_backend.action(req_data)
    kuyala_backend.logging.info(f"Action successful. Scaled to {scale} replicas.")
    return jsonify({'status': 'success', 'scaled_to': scale})

if __name__ == '__main__':
    app.run(debug=True)
