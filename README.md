# Kuyala

Kuyala is a simple web application for managing designated Kubernetes deployments.

## Kubernetes Authentication

The application authenticates to the Kubernetes API using a standard priority order, which provides flexibility for both local development and in-cluster deployment. The application will try the following methods in order until one succeeds:

1.  **In-Cluster Configuration**: If the application is running inside a Kubernetes pod, it will automatically use the pod's service account. This is the standard and recommended method for production deployments.

2.  **Default Kubeconfig Path**: It will look for a kubeconfig file at the default location (`~/.kube/config`). This is useful for local development on a machine where `kubectl` is already configured.

3.  **`KUBECONFIG` Environment Variable**: It will check for a `KUBECONFIG` environment variable that specifies the absolute path to a kubeconfig file. Applicable only for running locally, not in docker.

4.  **`KUBECONFIG_CONTENT` Environment Variable**: It will check for a `KUBECONFIG_CONTENT` environment variable that contains the *raw, base64-encoded content* of a kubeconfig file. This is a secure way to provide credentials in CI/CD environments without writing files to disk.

## Configuration

The application is configured via environment variables.

| Variable               | Description                                                                                                 | Default |
|------------------------|-------------------------------------------------------------------------------------------------------------|---------|
| `KUBECONFIG`           | The absolute path to the Kubernetes configuration file. (See Authentication section).                         | `""`      |
| `KUBECONFIG_CONTENT`   | The base64-encoded content of a kubeconfig file. (See Authentication section).                              | `""`      |
| `LOG_LEVEL`            | The logging level for the application. Supported values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.     | `INFO`  |

## Local build

To run the application using Docker, build the image and run the container with the desired environment variables.

```sh
# Build the image using the provided build script
./docker/docker_build.sh

Run the container with provided raw value fom of kubeconfig. Make sure the path is correct 
```sh
docker run -p 5000:5000 \
  -e LOG_LEVEL=DEBUG \
  -e KUBECONFIG_CONTENT="$(cat ~/.kube/config)" \
  -v ~/.kube:/root/.kube \
  kuyala:latest


```
Alternatively you can mount the config on your host to the container 
```sh
docker run --rm -it -p 5000:5000 \
  -e KUBECONFIG=/home/nonroot/.kube/config \
  -v ~/.kube/config:/home/nonroot/.kube/config:ro \
  kuyala:latest
```

