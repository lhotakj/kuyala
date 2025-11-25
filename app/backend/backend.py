from __future__ import annotations

import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

class Backend:

    kube_config: str | None = None



    def action(self, data):
        namespace = data.get('namespace')
        name = data.get('name')
        scale = int(data.get('scale', 1))

        logging.info(f"Attempting to scale deployment '{name}' in namespace '{namespace}' to {scale} replicas.")
        try:
            config.load_kube_config(config_file=self.kube_config)
            apps_v1 = client.AppsV1Api()
            body = {'spec': {'replicas': scale}}
            apps_v1.patch_namespaced_deployment_scale(name, namespace, body)
            logging.info(f"Successfully scaled deployment '{name}'.")
            return scale
        except ApiException as e:
            logging.error(f"Kubernetes API error while scaling deployment '{name}': {e.reason}")
            # Optionally re-raise or handle the error appropriately
            return None # Indicate failure
        except Exception as e:
            logging.error(f"An unexpected error occurred during scaling action: {str(e)}")
            return None # Indicate failure


    def get_current_list(self):
        # logging.info("Fetching current list of deployments from Kubernetes.")
        try:
            config.load_kube_config(config_file=self.kube_config)
            v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            namespaces = [ns.metadata.name for ns in v1.list_namespace().items]

            result_data = []
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
                        replicas_off = int(annotations.get("kuyala.replicasOff", 0))
                        replicas_on = int(annotations.get("kuyala.replicasOn", 1))
                        replicas_current = getattr(dep.status, "replicas", 0)
                        if not replicas_current:
                            replicas_current = 0
                        result_data.append({
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
            
            # logging.info(f"Successfully fetched {len(result_data)} Kuyala-enabled deployments.")
            return {
                "status": "success",
                "data": result_data
            }

        except ApiException as e:
            logging.error(f"Kubernetes API error while fetching deployments: {e.reason}")
            return {
                "status": "error",
                "message": f"Kubernetes API error: {e.reason}"
            }
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching deployments: {str(e)}")
            return {
                "status": "error",
                "message": f"An unexpected error occurred: {str(e)}"
            }
