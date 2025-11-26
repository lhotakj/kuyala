let lastApps = {};

function setStatus(message, type) {
    const statusElement = document.getElementById('status-message');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = 'alert alert-' + type; // Types: info, success, error
        statusElement.style.display = 'block';

        // Hide success or info messages after 3 seconds
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                statusElement.style.display = 'none';
            }, 3000);
        }
    }
}

function hexToRgba(hex, alpha = 0.5) {
    hex = hex.replace('#', '');
    if (hex.length === 3) {
        hex = hex.split('').map(x => x + x).join('');
    }
    const num = parseInt(hex, 16);
    const r = (num >> 16) & 255;
    const g = (num >> 8) & 255;
    const b = num & 255;
    return `rgba(${r},${g},${b},${alpha})`;
}

function renderApps(apps) {
    const grid = document.getElementById('appsGrid');
    if (!grid) return; // Exit if the grid isn't on the page

    const newApps = {};
    apps.forEach(app => {
        newApps[app.namespace + '|' + app.name] = app;
    });

    // Update or remove existing cards
    Array.from(grid.children).forEach(card => {
        const key = card.dataset.key;
        if (!(key in newApps)) {
            grid.removeChild(card);
        } else {
            const app = newApps[key];
            card.style.backgroundColor = app.color ? hexToRgba(app.color, 0.5) : '';
            card.innerHTML = getCardHTML(app);
            attachButtonHandler(card, app);
        }
    });

    // Add new cards
    Object.keys(newApps).forEach(key => {
        if (!lastApps[key]) {
            const app = newApps[key];
            const card = document.createElement('div');
            card.className = 'card app';
            card.style.position = 'relative';
            card.dataset.key = key;
            card.style.backgroundColor = app.color ? hexToRgba(app.color, 0.5) : '';
            card.innerHTML = getCardHTML(app);
            grid.appendChild(card);
            attachButtonHandler(card, app);
        }
    });

    lastApps = newApps;
}

function getCardHTML(app) {
    let buttonText, buttonColor, scaleValue;
    if (app.replicasCurrent === app.replicasOn) {
        buttonText = "Turn off";
        buttonColor = "#f44336"; // red
        scaleValue = app.replicasOff;
    } else if (app.replicasCurrent === app.replicasOff) {
        buttonText = "Turn on";
        buttonColor = "#4caf50"; // green
        scaleValue = app.replicasOn;
    } else {
        buttonText = "Toggle";
        buttonColor = "#2196f3"; // blue
        scaleValue = app.replicasOn;
    }
    return `
        <span class="lozenge">${app.namespace}</span>
        <h3 class="card-header">${app.name}</h3>
        <p class="card-description">Created: ${app.creationDate}</p>
        <div class="card-replica-info">
            running ${app.replicasCurrent} / ${app.replicasOn}
        </div>
        <button class="button button-primary" 
            style="position: absolute; right: 10px; bottom: 10px; background: ${buttonColor}; color: #fff;"
            data-scale="${scaleValue}"
            data-namespace="${app.namespace}"
            data-name="${app.name}"
        >${buttonText}</button>
    `;
}

function attachButtonHandler(card, app) {
    const btn = card.querySelector('button.button-primary');
    if (btn) {
        btn.onclick = async function () {
            const data = {
                namespace: btn.dataset.namespace,
                name: btn.dataset.name,
                scale: btn.dataset.scale
            };
            // setStatus('Sending action...', 'info');
            try {
                const response = await fetch('/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                if (response.ok) {
                  //  setStatus('Action successful!', 'success');
                } else {
                    const errorData = await response.json();
                    setStatus(`Action failed: ${errorData.message || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                setStatus(`Action failed: ${error.message}`, 'error');
            }
        };
    }
}

function fetchData() {
    // This function is for the "Refresh Data" button.
    // A simple page reload is the easiest way to force the EventSource to reconnect.
    window.location.reload();
}

// --- Main Execution ---
const evtSource = new EventSource('/list_stream');

evtSource.onopen = function() {
    // setStatus('Connecting to live stream...', 'info');
};

evtSource.onmessage = function (event) {
    const result = JSON.parse(event.data);
    if (result.status === 'success') {
        // setStatus('Data updated.', 'success');
        renderApps(result.data); // Pass the array of apps to the render function
    } else {
        setStatus(`Error: ${result.message}`, 'error');
    }
};

evtSource.onerror = function (err) {
    setStatus('Stream connection failed. Please refresh the page.', 'error');
    console.error("EventSource failed:", err);
};
