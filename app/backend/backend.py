from __future__ import annotations
import os
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from . import __version__

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Backend(metaclass=SingletonMeta):

    kube_config: str | None = None
    client = None
    logging = logging
    kubernetes_version = None
    master_node_ip = None
    master_node_name = None



    def __init__(self):
        # Configure logging
        early_warning = None
        log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
        if log_level_name not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            early_warning = f"Unrecognized log level '{log_level_name}'"
            log_level_name = 'INFO'
        log_level = getattr(self.logging, log_level_name)
        self.logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

        self.logging.info(f"Kuyala application starting up, version {__version__}")

        # Add these lines to specifically suppress DEBUG logs from the K8s client and its HTTP dependency
        self.logging.getLogger("kubernetes").setLevel(self.logging.INFO)
        self.logging.getLogger("urllib3").setLevel(self.logging.INFO)
        # Optionally, for maximum coverage, check the core Python HTTP client logger
        self.logging.getLogger("http.client").setLevel(self.logging.WARNING)

        if early_warning:
            logging.warning(early_warning)
        logging.info(f"Current log level set to: {log_level_name}")

        self.k8s_auth_and_validate()


    def k8s_auth_and_validate(self) -> bool:
        self.client = self.init_k8s_client()
        if not self.client:
            return False
        if not self.validate_connection():
            self.client = None
            return False
        return True

    def validate_connection(self) -> bool:
        """
        Validates the Kubernetes client connection by making a simple API call.
        """
        if not self.client:
            logging.warning("Validation skipped: K8s client not initialized.")
            return False
        try:
            api = client.VersionApi(self.client)
            version_info = api.get_code()
            self.kubernetes_version = f"{version_info.major}.{version_info.minor}"

            v1 = client.CoreV1Api(self.client)
            nodes = v1.list_node()
            for node in nodes.items:
                labels = node.metadata.labels or {}
                if "node-role.kubernetes.io/master" in labels or "node-role.kubernetes.io/control-plane" in labels:
                    for addr in node.status.addresses:
                        if addr.type == "InternalIP":
                            self.master_node_ip = addr.address
                            self.master_node_name = node.metadata.name
                            logging.info(f"Master node {self.master_node_name} has IP {self.master_node_ip}")

            logging.info(f"Successfully validated connection to Kubernetes API server. Version {self.kubernetes_version}")
            return True
        except ApiException as e:
            logging.error(f"Kubernetes API connection validation failed. Reason: {e.reason}", exc_info=True)
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during K8s connection validation: {e}", exc_info=True)
            return False

    def init_k8s_client(self):
        """
        Initialize Kubernetes Python client with the following priority:
        1. Try in-cluster configuration
        2. Try default kubeconfig path (~/.kube/config)
        3. Check KUBECONFIG environment variable (file path)
        4. Check KUBECONFIG_CONTENT environment variable (raw content)
        """

        # 1. Try in-cluster config
        try:
            config.load_incluster_config()
            logging.info("Loaded in-cluster Kubernetes configuration.")
            return client.ApiClient()
        except config.ConfigException:
            logging.info("Not running in a Kubernetes cluster.")

        # 2. Try default kubeconfig path
        default_path = os.path.expanduser("~/.kube/config")
        if os.path.exists(default_path):
            try:
                config.load_kube_config(default_path)
                logging.info(f"Loaded kubeconfig from default path: {default_path}")
                return client.ApiClient()
            except Exception as e:
                logging.error(f"Failed to load kubeconfig from default path: {e}")

        # 3. Check KUBECONFIG environment variable
        kubeconfig_env = os.getenv("KUBECONFIG")
        if kubeconfig_env and os.path.exists(kubeconfig_env):
            try:
                config.load_kube_config(kubeconfig_env)
                logging.info(f"Loaded kubeconfig from KUBECONFIG env: {kubeconfig_env}")
                return client.ApiClient()
            except Exception as e:
                logging.error(f"Failed to load kubeconfig from KUBECONFIG env: {e}")

        # 4. Check KUBECONFIG_CONTENT environment variable
        kubeconfig_content = os.getenv("KUBECONFIG_CONTENT")
        if kubeconfig_content:
            try:
                # Write content to a temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(kubeconfig_content.encode())
                    tmp_path = tmp.name
                config.load_kube_config(tmp_path)
                logging.info(f"Loaded kubeconfig from KUBECONFIG_CONTENT env.")
                return client.ApiClient()
            except Exception as e:
                logging.error(f" Failed to load kubeconfig from KUBECONFIG_CONTENT env: {e}")

        logging.error("Could not initialize Kubernetes client from any source.")
        return None

    def action(self, data):
        if not self.client:
            return {
                "status": "error",
                "message": f"Kubernetes authorization failed."
            }

        namespace = data.get('namespace')
        name = data.get('name')
        scale = int(data.get('scale', 1))

        logging.info(f"Attempting to scale deployment '{name}' in namespace '{namespace}' to {scale} replicas.")
        try:
            apps_v1 = client.AppsV1Api(self.client)
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
        if not self.client:
            return {
                "status": "error",
                "message": f"Kubernetes authorization failed."
            }

        # logging.info("Fetching current list of deployments from Kubernetes.")
        try:
            v1 = client.CoreV1Api(self.client)
            apps_v1 = client.AppsV1Api(self.client)
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
                            "backgroundColor": annotations.get("kuyala.backgroundColor", ""),
                            "textColor": annotations.get("kuyala.textColor", ""),
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
