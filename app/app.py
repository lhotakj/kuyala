from flask import Flask, render_template, jsonify
from kubernetes import client, config

app = Flask(__name__, template_folder='./templates')

@app.route('/')
def main():
    return render_template('start.html')

@app.route('/list')
def list():
    config.load_kube_config()
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    namespaces = [ns.metadata.name for ns in v1.list_namespace().items]

    result = []
    for ns in namespaces:
        deployments = apps_v1.list_namespaced_deployment(ns)
        for dep in deployments.items:
            annotations = dep.metadata.annotations or {}
            if "kuyala.enabled" in annotations:
                creation_date = dep.metadata.creation_timestamp.isoformat() if dep.metadata.creation_timestamp else None
                condition = None
                if dep.status and dep.status.conditions:
                    condition = [
                        {"type": c.type, "status": c.status}
                        for c in dep.status.conditions
                    ]
                # Read kuyala.replicasOff, default 0
                replicas_off = int(annotations.get("kuyala.replicasOff", 0))
                # Read spec.replicas, default 1
                replicas_on = int(annotations.get("kuyala.replicasOn", 1))
                replicas_current = getattr(dep.status, "replicas", 0)
                if not replicas_current:
                    replicas_current = 0
                result.append({
                    "namespace": ns,
                    "name": dep.metadata.name,
                    "applicationName": annotations.get("kuyala.applicationName", dep.metadata.name),
                    "annotations": annotations,
                    "creationDate": creation_date,
                    "condition": condition,
                    "color": annotations.get("kuyala.color", ""),
                    "replicasOff": replicas_off,
                    "replicasOn": replicas_on,
                    "replicasCurrent": replicas_current
                })

    return jsonify(result)

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