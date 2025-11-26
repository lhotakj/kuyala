// File: app/static/js/apps.js

class KuyalaSSEClient {
    constructor() {
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000;
        this.isConnected = false;
        this.deployments = new Map(); // Store deployments by key: namespace/name
        this.appsGrid = document.getElementById('appsGrid');
        this.statusMessage = document.getElementById('status-message');
    }

    connect() {
        if (this.eventSource) {
            this.disconnect();
        }

        console.log('Connecting to SSE endpoint...');
        this.showStatus('Connecting to server...', 'info');

        try {
            this.eventSource = new EventSource('/events');

            this.eventSource.addEventListener('open', () => {
                console.log('SSE connection established');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.hideStatus();
            });

            this.eventSource.addEventListener('connected', (e) => {
                const data = JSON.parse(e.data);
                console.log('Connected with client ID:', data.client_id);
            });

            this.eventSource.addEventListener('initial_data', (e) => {
                const response = JSON.parse(e.data);
                if (response.status === 'success') {
                    console.log('Received initial data:', response.data.length, 'deployments');
                    this.renderDeployments(response.data);
                } else {
                    this.showStatus(response.message || 'Failed to load deployments', 'error');
                }
            });

            this.eventSource.addEventListener('deployment_update', (e) => {
                const update = JSON.parse(e.data);
                console.log('Deployment update:', update.type, update.namespace + '/' + update.name);
                this.handleDeploymentUpdate(update);
            });

            this.eventSource.addEventListener('heartbeat', (e) => {
                const data = JSON.parse(e.data);
                console.log('Heartbeat received at:', new Date(data.timestamp * 1000).toLocaleTimeString());
            });

            this.eventSource.addEventListener('error', (e) => {
                console.error('SSE connection error:', e);
                this.isConnected = false;
                this.handleReconnect();
            });

        } catch (error) {
            console.error('Failed to create EventSource:', error);
            this.handleReconnect();
        }
    }

    disconnect() {
        if (this.eventSource) {
            console.log('Closing SSE connection');
            this.eventSource.close();
            this.eventSource = null;
            this.isConnected = false;
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.min(this.reconnectAttempts, 5);
            
            console.log(`Reconnecting in ${delay/1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            this.showStatus(`Connection lost. Reconnecting in ${delay/1000}s...`, 'error');

            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.showStatus('Connection lost. Please refresh the page.', 'error', false);
        }
    }

    handleDeploymentUpdate(update) {
        const key = `${update.namespace}/${update.name}`;
        
        switch (update.type) {
            case 'ADDED':
            case 'MODIFIED':
                this.deployments.set(key, update);
                this.updateDeploymentCard(update);
                break;
            case 'DELETED':
                this.deployments.delete(key);
                this.removeDeploymentCard(key);
                break;
        }
    }

    renderDeployments(deployments) {
        // Clear existing grid
        this.appsGrid.innerHTML = '';
        this.deployments.clear();

        if (!deployments || deployments.length === 0) {
            this.appsGrid.innerHTML = '<div class="card"><p class="card-description">No deployments found with kuyala.enabled annotation.</p></div>';
            return;
        }

        deployments.forEach(dep => {
            const key = `${dep.namespace}/${dep.name}`;
            this.deployments.set(key, dep);
            this.createDeploymentCard(dep);
        });
    }

    createDeploymentCard(deployment) {
        const key = `${deployment.namespace}/${deployment.name}`;
        const cardId = `card-${key.replace(/\//g, '-')}`;

        // Remove existing card if present
        const existing = document.getElementById(cardId);
        if (existing) {
            existing.remove();
        }

        const isOn = deployment.replicasCurrent > 0;
        const buttonText = isOn ? 'Turn Off' : 'Turn On';
        const buttonClass = isOn ? 'button-secondary' : 'button-primary';
        const statusText = isOn ? 'Running' : 'Stopped';
        const lozengeClass = deployment.color || (isOn ? '' : 'lozenge-off');

        const card = document.createElement('div');
        card.className = 'card app';
        card.id = cardId;
        card.innerHTML = `
            <div class="lozenge ${lozengeClass}">${statusText}</div>
            <h3 class="card-header">${this.escapeHtml(deployment.applicationName)}</h3>
            <p class="card-description">
                <strong>Namespace:</strong> ${this.escapeHtml(deployment.namespace)}<br>
                <strong>Deployment:</strong> ${this.escapeHtml(deployment.name)}
            </p>
            <p class="card-replica-info">
                Current replicas: ${deployment.replicasCurrent}
                ${isOn ? ` (will scale to ${deployment.replicasOff})` : ` (will scale to ${deployment.replicasOn})`}
            </p>
            <div class="button-group">
                <button class="button ${buttonClass}" 
                        onclick="kuyalaApp.toggleDeployment('${this.escapeHtml(deployment.namespace)}', '${this.escapeHtml(deployment.name)}', ${!isOn})"
                        id="btn-${cardId}">
                    ${buttonText}
                </button>
            </div>
        `;

        this.appsGrid.appendChild(card);
    }

    updateDeploymentCard(deployment) {
        this.createDeploymentCard(deployment);
    }

    removeDeploymentCard(key) {
        const cardId = `card-${key.replace(/\//g, '-')}`;
        const card = document.getElementById(cardId);
        if (card) {
            card.remove();
        }
    }

    async toggleDeployment(namespace, name, turnOn) {
        const deployment = this.deployments.get(`${namespace}/${name}`);
        if (!deployment) {
            this.showStatus('Deployment not found', 'error');
            return;
        }

        const scale = turnOn ? deployment.replicasOn : deployment.replicasOff;
        const action = turnOn ? 'starting' : 'stopping';

        console.log(`${action} deployment ${namespace}/${name} (scale to ${scale})`);

        // Disable button during action
        const cardId = `card-${namespace}-${name}`.replace(/\//g, '-');
        const button = document.getElementById(`btn-${cardId}`);
        if (button) {
            button.disabled = true;
            button.textContent = action === 'starting' ? 'Starting...' : 'Stopping...';
        }

        try {
            const response = await fetch('/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    namespace: namespace,
                    name: name,
                    scale: scale
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                console.log(`Successfully scaled ${namespace}/${name} to ${result.scaled_to} replicas`);
                this.showStatus(
                    `${deployment.applicationName} ${turnOn ? 'started' : 'stopped'} successfully`,
                    'success'
                );
            } else {
                throw new Error(result.message || 'Action failed');
            }

        } catch (error) {
            console.error('Error toggling deployment:', error);
            this.showStatus(`Failed to ${action} deployment: ${error.message}`, 'error');
            
            // Re-enable button
            if (button) {
                button.disabled = false;
                button.textContent = turnOn ? 'Turn On' : 'Turn Off';
            }
        }
    }

    showStatus(message, type = 'info', autoHide = true) {
        this.statusMessage.textContent = message;
        this.statusMessage.className = `alert alert-${type}`;
        this.statusMessage.style.display = 'block';

        if (autoHide) {
            setTimeout(() => {
                this.hideStatus();
            }, 5000);
        }
    }

    hideStatus() {
        this.statusMessage.style.display = 'none';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            deploymentsCount: this.deployments.size
        };
    }
}

// Initialize the application
let kuyalaApp;

document.addEventListener('DOMContentLoaded', () => {
    console.log('Kuyala application initializing...');
    
    kuyalaApp = new KuyalaSSEClient();
    kuyalaApp.connect();

    // Handle page unload
    window.addEventListener('beforeunload', () => {
        kuyalaApp.disconnect();
    });

    // Expose for debugging
    window.kuyalaApp = kuyalaApp;
});