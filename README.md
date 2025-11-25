# Kuyala

Kuyala is a simple web application for managing designated Kubernetes deployments.

## Configuration

The application is configured via environment variables.

| Variable      | Description                                                                                                 | Default |
|---------------|-------------------------------------------------------------------------------------------------------------|---------|
| `KUBECONFIG`  | The absolute path to the Kubernetes configuration file. Not required if running inside a cluster.             | `""`      |
| `LOG_LEVEL`   | The logging level for the application. Supported values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.     | `INFO`  |

## Running with Docker

To run the application using Docker, build the image and run the container with the desired environment variables.

```sh
# Build the image
docker build -t kuyala .

# Run the container
docker run -p 5000:5000 \
  -e LOG_LEVEL=DEBUG \
  -e KUBECONFIG=/root/.kube/config \
  -v ~/.kube:/root/.kube \
  kuyala
```
