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
        this.connectionInfo = document.getElementById('connection-info-container');
        this.iconConnected = "<img src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAACfElEQVQ4jZWTz2+TNxzGP7bf5E3SljSlDb8qoVIuiNJBBEeuAwkhmDSu3NjuaBuC/wCBgBNCAolbObEj/wJcQFAQAo20AkQ32oakaUhev47tHex251l65B+Pn8fP15bF3VsAIAQ4D49l5UIrlX+0UnWoU1RlEFS1Hkz0Bu8njbz5szSPpADvgy4htuEQ7o+MPl+spQ1qEkZEYJ1BqT0j0+XZxsuPHxbWmstXLhl7tBCVckt8Z3TH6uJ0qcGMgr0KahJ2SBhzTNbHmZ+d56eTZ+mfOPrD7XKynufRwFp4UBl90dyXTrFPwZiEAgFFAeUKTd1k4dMCH/UKpxunEI1jO+8X5RtrQZkzlR+fTpV+Z1qF2FJAQUAqQ59ISBKM22B5s0k1meD4dINXg3Z97Wv7hVxN1Q1qEsoiFFQEUhFQElCK88o4FCzPOs/JfUZ1apzVkrgudj2sZl8Ppim1GL0kowEhAYDxoAHtIbOUbZnB+ib1JZsnGwVVJBEgCPEloKK4tPVGAoZ+mx/kHSgU6RYoSP5X8+HhZCmY4pFVY3OGPnDOgyXAeMgIMHHdxT0A1jNmnJH1zP1F30cyENs1D3yABgyhDBcP6HvqA7ssd2l7hbZj28TEy9IesgjtIXeBc9H4m2O3ttfkOdN/MtfSr1lzYfNWgsz9Z5A5yCOXeVh1HG7pd+dN/0+pFPzS783PfNEtViz0POQxSe4DTJz3HKxY9n/R7V+/9w4pFf9CouByrzt55LNeZGkI/1joOOj6gI6Dvy0sW+Y+67e/bXYnlAp3qc6cigMJx4f5vf5ALFW77oDadFW/4VWx7fzONZPNrJt3cxv51Yv590tbYoB/ARzpN8MKUY/8AAAAAElFTkSuQmCC' title='connected' alt='connected' style='vertical-align: middle;' />"
        this.iconDisconneted = "<img src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAAB5klEQVQ4jZ2Tz2sTURDHP/t2N5tUypKiCO0GCgFb8OAlaqDoWSjexFv9D1T8RxQsiuBFDJ48t1eFIpReetBD20sslFRN6CZYsz+z6+HNg6V4cmB4783M9zvz5r2xXqPFAgqghBsubHhw14VlgASOp7CTQ8+FfaXjNM4QzAAXnvvwrAlcAhwhtX2fxuoqx0dHfA/DzRKeuIKz14Ec8GBrER4FwAIwB9Q1Kc0goNXtEqys4Ewmt4dhuJZBzwbsezrTiyXYWKpkNuoCWRgyOTykNj/PcrcLo1H7dDy+CmzZ63BtAT4EAlYC8mQ1REWW8bvfx/F9gk6H6WBw8+f5+UflwuMm0BBwTcCeXKEu+zkhHO/uUqYpV3wfD55a7+BbG643JaBeITCNyvRLkAAxMGs0GEURfThwHGg58oxK1K6QGckr/jSKzPUWFf8hFZClcjjJ0R+jQP+HmZQdi2ZiK0SRcw4DlcDnacVpwAkQiSZiyysxU02+ozLYDMVQ/KNhsexT8RVCeqbPL1UJByG8GpoOXyjfaCq+GPgFhPC2hK/2fV3adgxrQNtFv8jFnpiyfwCn8CmFBw4yC0pn7f2ByxHcMg2r9uJMAxnCmxQe2pLIqo6zZO3U9DjfcaCFJjpJ4UsK7y3Yq47zX6TYvT54UNtgAAAAAElFTkSuQmCC' title='disconnected' alt='disconnected' style='vertical-align: middle;' />"
        this.iconReconnecting = "<img src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAACXUlEQVQ4jXWTz0sVURTHPzNzZ+b9kucTn/L8UUYgQlAbizYJQWXkvp3bVln4jxgURdCqpEW0dp0gQbQJaVMtMsl86VPHn29m7r0z0+LOUwu68OVezrnfc773nHusZ3MAYFmQZpClXHJdpn2PCVcwggWxZLV9xJJOmHc9PtkWZJnhCfKlNbguc9VuZmvdUC6DcCBNwRHVerE8Nr66+m32x0rwRFs8cMWpAFqD77PQ6OdOXx1KRbAdsIAkgUpXL32Ni5w5e4Ge2uLM8vL3MSm55Xng3L4BwuXRYIPpwcZJZuGAEOC6oOKAveArntfFyLmrkG2db67v9gMLztQkoz01Xg8NGLJtGZLvm10IEC6kieJgfwUhqgwNj9M+Wr+8sXn41nZdZmrdUCwaspeTfQ8KvoHvQ6kCroDd4ANZKqnXq/geD4Xvcb1cAscB2zbZXHGiAEApsxdLEEWH/Pr5hvZhSKXChBCCYSFMG23bqHAcQy54mErmhe74pQ47zxuw+XdZ/zmfstnOsc+ytWZNa/Mx0hSSHEpBFBsoZWxpDjJINGjNuh1LFtshpEkeQBlCLCEMDWJpbFrndxJohxDFLNlK8SQIoB2Zr6w0xLFBR0Ecg8yDpBmEEewEoBSP7SzjS7DH01YLouiU/OhvSGl8UQSbWxDs8SLL+CwcB5TmfvM3o8DNvjoUCqYTnRpmGOlhCJstaG7wTknuCQHO1KRpj0qYP2rTG0ZcSRJTE6UgVhC2jeTmBrS2eS4ldx3HtP54GvPJm9ne4eXBPtO+zzUhGAZQmjUpeS8Vryz4KMTJOP8BxQ8gUYW+jLYAAAAASUVORK5CYII=' title='reconnecting' alt='reconnecting' style='vertical-align: middle;' />"
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
                console.log(data)
                this.connectionInfo.innerHTML = data.server_node_name + " (" + data.server_node_ip + ") " + this.iconConnected
                console.log('Connected with client ID:', data.client_id);
            });

            this.eventSource.addEventListener('initial_data', (e) => {
                const response = JSON.parse(e.data);
                if (response.status === 'success') {
                    console.log('Received initial data:', response.data.length, 'deployments');
                    console.log('Raw data:', response.data);
                    const sortedData = [...response.data].sort((a, b) => a.applicationName.localeCompare(b.applicationName));
                    this.renderDeployments(sortedData);
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
                this.connectionInfo.innerHTML = this.iconDisconneted
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
            this.connectionInfo.innerHTML = "<i title='reconnecting, refresh the page for hard reconnect'>reconnecting</i> " + this.iconReconnecting

            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.showStatus('Connection lost. Please refresh the page.', 'error', false);
            this.connectionInfo.innerHTML = "<i title='disconnected, refresh the to try to reconnect'>disconnected</i> " + this.iconDisconneted
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
        const buttonClass = isOn ? 'button-turn-off' : 'button-turn-on';
        const statusText = isOn ? 'Running' : 'Stopped';
        const lozengeClass = (isOn ? 'lozenge-light-green' : 'lozenge-light-red');

        const card = document.createElement('div');
        card.className = 'card app';
        //card.style.zIndex = 3;
        const cardHeaderStyle = ("color: " + deployment.textColor  || "") + ("; position: absolute; top: 0; padding-left: 10px; padding-right: 10px; left: 22px; top: 22px; background-color: " + deployment.backgroundColor + "; border-radius: 12px;" || "");
        card.id = cardId;
        card.innerHTML = `            
            <div class="lozenge ${lozengeClass}">${statusText}</div>            
            <span class="card-header" style="${cardHeaderStyle}">${this.escapeHtml(deployment.applicationName)}</span>
            <p class="card-description" style="margin-top: 50px; ">
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

    // updateDeploymentCard(deployment) {
    //     this.createDeploymentCard(deployment);
    // }

    updateDeploymentCard(deployment) {
        const key = `${deployment.namespace}/${deployment.name}`;
        const cardId = `card-${key.replace(/\//g, '-')}`;
        const card = document.getElementById(cardId);

        if (card) {
            // Just update the relevant parts
            const isOn = deployment.replicasCurrent > 0;
            const buttonText = isOn ? 'Turn Off' : 'Turn On';
            const buttonClass = isOn ? 'button-turn-off' : 'button-turn-on';
            const statusText = isOn ? 'Running' : 'Stopped';
            const lozengeClass = isOn ? 'lozenge-light-green' : 'lozenge-light-red';

            card.querySelector('.lozenge').textContent = statusText;
            card.querySelector('.lozenge').className = `lozenge ${lozengeClass}`;
            card.querySelector('.card-replica-info').textContent =
                `Current replicas: ${deployment.replicasCurrent} ${isOn ? `(will scale to ${deployment.replicasOff})` : `(will scale to ${deployment.replicasOn})`}`;

            const button = card.querySelector('button');
            button.textContent = buttonText;
            button.className = `button ${buttonClass}`;
            button.setAttribute('onclick', `kuyalaApp.toggleDeployment('${deployment.namespace}', '${deployment.name}', ${!isOn})`);
        } else {
            // If card doesn’t exist yet, create it
            this.createDeploymentCard(deployment);
        }
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

                // Refresh button state right away
                if (button) {
                    button.disabled = false;
                    button.textContent = turnOn ? 'Turn Off' : 'Turn On';
                }

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