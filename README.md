# Kuyala

Kuyala is a simple web application for managing designated Kubernetes deployments.

## Running the Application

There are several ways to run the application, depending on your needs.

### 1. Local Development (Without Docker)

This method is ideal for development and testing, giving you a live-reloading server.

**Prerequisites:**
- Python 3.8+
- `pip` and `venv`

**Steps:**

1.  **Run the setup script:**
    This script will create a Python virtual environment in a `venv` directory and install all required dependencies from `requirements.txt`.
    ```sh
    ./local_development_setup.sh
    ```

2.  **Activate the virtual environment:**
    You must activate the environment in your shell to use the installed dependencies.
    ```sh
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Run the development server:**
    This script starts a Flask development server with auto-reload enabled.
    ```sh
    ./kuyala_development.sh
    ```
    The application will be available at `http://localhost:5000`.

### 2. Running with Docker

This method packages the application into a container for consistent execution.

**Prerequisites:**
- Docker

**Steps:**

1.  **Build the Docker image:**
    ```sh
    ./docker/docker_build.sh
    ```

2.  **Run the container:**
    You can run the container by providing your kubeconfig file either as a mounted volume or as raw content in an environment variable.

    **Option A: Mount kubeconfig file**
    ```sh
    docker run --rm -p 5000:5000 \
      -v ~/.kube:/root/.kube:ro \
      --name kuyala \
      kuyala:latest
    ```

    **Option B: Use `KUBECONFIG_CONTENT`**
    ```sh
    docker run --rm -p 5000:5000 \
      -e KUBECONFIG_CONTENT="$(cat ~/.kube/config)" \
      --name kuyala \
      kuyala:latest
    ```

### 3. Running with Docker Compose

This is the easiest way to run the application with Docker. See the `docker-compose.yml` file for configuration details.

**Prerequisites:**
- Docker and Docker Compose

**Steps:**

1.  **Create a `.env` file:**
    Create a file named `.env` in the project root and add your environment variables. This file is ignored by Git.
    ```env
    # .env
    LOG_LEVEL=INFO
    # KUBECONFIG_CONTENT="" # Optional: paste kubeconfig content here
    ```

2.  **Run Docker Compose:**
    ```sh
    docker-compose up --build
    ```
    The application will be available at `http://localhost:5000`. To run in the background, add the `-d` flag.

## Deploying to Kubernetes

A sample deployment manifest is provided in the `k8s` directory, consolidating all necessary resources into a single file.

**Prerequisites:**
- A running Kubernetes cluster
- `kubectl` configured to connect to your cluster
- The Docker image `kuyala:latest` pushed to a registry accessible by your cluster.

**Steps:**

1.  **Build and Push the Image:**
    Build the image and push it to your container registry (e.g., Docker Hub, GCR, ECR).
    ```sh
    # Tag the image with your registry's name
    docker build -t your-registry/kuyala:latest -f docker/dockerfile .
    
    # Push the image
    docker push your-registry/kuyala:latest
    ```

2.  **Update the Deployment Manifest:**
    Edit `k8s/kuyala_manifest.yaml` and change `image: kuyala:latest` to `image: your-registry/kuyala:latest`.

3.  **Apply the Manifest:**
    ```sh
    kubectl apply -f k8s/kuyala_manifest.yaml
    ```
    This will create the ServiceAccount, ClusterRole, ClusterRoleBinding, Deployment, and a LoadBalancer Service to expose the application.

## Kubernetes Authentication

The application authenticates to the Kubernetes API using a standard priority order:

1.  **In-Cluster Configuration**: Uses the pod's service account (recommended for production).
2.  **Default Kubeconfig Path**: Uses `~/.kube/config` (for local development).
3.  **`KUBECONFIG` Environment Variable**: Path to a kubeconfig file.
4.  **`KUBECONFIG_CONTENT` Environment Variable**: Raw content of a kubeconfig file.

## Configuration

| Variable             | Description                                                                 | Default |
|----------------------|-----------------------------------------------------------------------------|---------|
| `LOG_LEVEL`          | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.             | `INFO`  |
| `KUBECONFIG`         | Absolute path to the kubeconfig file.                                       | `""`    |
| `KUBECONFIG_CONTENT` | Raw content of the kubeconfig file.                                         | `""`    |
