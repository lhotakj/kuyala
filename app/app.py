import json
import time
import os
import logging
from flask import Flask, render_template, jsonify, Response, request
from kubernetes import client, config

from . import __version__
from .backend import backend

# --- Standard Logging Setup ---
# Get log level from environment variable, default to INFO if not set or invalid
early_warning = None
log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
if log_level_name not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    early_warning = f"Unrecognized log level '{log_level_name}'"
    log_level_name = 'INFO'
log_level = getattr(logging, log_level_name)

# Configure logging
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
# --- End Logging Setup ---

app = Flask(__name__, template_folder='./templates')
kuyala_backend = backend.Backend()

logging.info(f"Kuyala application starting up, version {__version__}")
if early_warning:
    logging.warning(early_warning)
logging.info(f"Current log level set to: {log_level_name}")


@app.route('/')
def main():
    # Log all environment variables at DEBUG level for debugging purposes
    path: str | None = None
    for key, value in os.environ.items():
        if key == 'KUBECONFIG':
            logging.debug(f"Configuration check passed. Using {key}")
            path = os.environ.get('KUBECONFIG')
            break
        if key == 'KUBERNETES_SERVICE_HOST':
            logging.debug(f"Configuration check passed. Using {key}")
            path = os.environ.get('KUBERNETES_SERVICE_HOST')

    config_error: str | None = None
    if not path:
        config_error = "Configuration error: KUBECONFIG or KUBERNETES_SERVICE_HOST environment variable is not set and not running in-cluster."
        logging.error(config_error)

    return render_template('start.html', config_error=config_error)

@app.route('/list')
def list():
    logging.debug("Request received for /list endpoint.")
    return jsonify(kuyala_backend.get_current_list())


@app.route('/list_stream')
def list_stream():
    logging.debug("Request received for /list_stream endpoint.")
    def event_stream():
        while True:
            data = kuyala_backend.get_current_list()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/action', methods=['POST'])
def action():
    req_data = request.get_json()
    logging.info(f"Action request received: {req_data}")
    scale = kuyala_backend.action(req_data)
    logging.info(f"Action successful. Scaled to {scale} replicas.")
    return jsonify({'status': 'success', 'scaled_to': scale})

if __name__ == '__main__':
    app.run(debug=True)
