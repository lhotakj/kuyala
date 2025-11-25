let lastApps = {};

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
    const newApps = {};
    apps.forEach(app => {
        newApps[app.namespace + '|' + app.name] = app;
    });

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
        btn.onclick = async function() {
            const data = {
                namespace: btn.dataset.namespace,
                name: btn.dataset.name,
                scale: btn.dataset.scale
            };
            await fetch('/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
        };
    }
}




async function fetchAndRender() {
    try {
        const res = await fetch('/list');
        const apps = await res.json();
        renderApps(apps); // Always update cards, only deltas are changed
    } catch (e) {
        // Optionally handle error
    }
}


setInterval(fetchAndRender, 2000);
window.addEventListener('DOMContentLoaded', fetchAndRender);