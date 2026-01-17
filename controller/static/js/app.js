// Global state
let systemStatus = null;
let statusUpdateInterval = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing application...');

    // Set up event listeners
    setupEventListeners();

    // Load animations list
    await loadAnimations();

    // Initial status update
    await updateStatus();

    // Start periodic status updates
    startStatusUpdates();
}

function setupEventListeners() {
    // Animation controls
    document.getElementById('start-animation-btn').addEventListener('click', startAnimation);
    document.getElementById('stop-animation-btn').addEventListener('click', stopAnimation);
    document.getElementById('animation-select').addEventListener('change', onAnimationSelect);

    // Manual controls
    document.getElementById('all-on-btn').addEventListener('click', () => setAllLEDs(true));
    document.getElementById('all-off-btn').addEventListener('click', () => setAllLEDs(false));
    document.getElementById('scan-slaves-btn').addEventListener('click', scanSlaves);
}

// API Communication
async function apiRequest(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(`/api/${endpoint}`, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Request failed');
        }

        return result;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        showToast(`Error: ${error.message}`, 'error');
        throw error;
    }
}

// Status Updates
async function updateStatus() {
    try {
        const status = await apiRequest('status');
        systemStatus = status;
        updateUI(status);
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

function updateUI(status) {
    // Update badges
    document.getElementById('environment-badge').textContent =
        `${status.environment.toUpperCase()} Environment`;
    document.getElementById('mode-badge').textContent =
        status.manual_mode ? 'Manual Mode' : 'Animation Mode';

    // Update status info
    document.getElementById('env-name').textContent = status.environment;
    document.getElementById('env-description').textContent = status.config_description;
    document.getElementById('total-leds').textContent = status.total_leds;
    document.getElementById('current-mode').textContent =
        status.manual_mode ? 'Manual' : 'Animation';
    document.getElementById('current-animation').textContent =
        status.current_animation ? formatAnimationName(status.current_animation) : 'None';

    // Update LED grid (only create once)
    if (!document.querySelector('.led-button')) {
        createLEDGrid(status.total_leds);
    }

    // Update LED states
    updateLEDStates(status.led_states, status.slave_online, status.leds_per_slave);

    // Update button states
    updateButtonStates(status);
}

function createLEDGrid(totalLEDs) {
    const grid = document.getElementById('led-grid');
    grid.innerHTML = '';

    for (let i = 0; i < totalLEDs; i++) {
        const button = document.createElement('button');
        button.className = 'led-button';
        button.dataset.index = i;
        button.innerHTML = `
            <span class="led-index">LED ${i}</span>
            <span class="led-status">OFF</span>
        `;
        button.addEventListener('click', () => toggleLED(i));
        grid.appendChild(button);
    }
}

function updateLEDStates(states, slaveOnline, ledsPerSlave) {
    states.forEach((state, index) => {
        const button = document.querySelector(`.led-button[data-index="${index}"]`);
        if (button) {
            // Check if corresponding slave is online
            const slaveIndex = Math.floor(index / ledsPerSlave);
            const isOnline = slaveOnline[slaveIndex];

            if (!isOnline) {
                button.classList.add('disconnected');
                button.disabled = true;
                button.querySelector('.led-status').textContent = 'OFFLINE';
            } else {
                button.classList.remove('disconnected');
                button.disabled = false;
                if (state) {
                    button.classList.add('active');
                    button.querySelector('.led-status').textContent = 'ON';
                } else {
                    button.classList.remove('active');
                    button.querySelector('.led-status').textContent = 'OFF';
                }
            }
        }
    });
}

function updateButtonStates(status) {
    const startBtn = document.getElementById('start-animation-btn');
    const stopBtn = document.getElementById('stop-animation-btn');
    const animationSelect = document.getElementById('animation-select');
    const allOnBtn = document.getElementById('all-on-btn');
    const allOffBtn = document.getElementById('all-off-btn');

    if (status.animation_running) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        animationSelect.disabled = true;
        allOnBtn.disabled = true;
        allOffBtn.disabled = true;
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        animationSelect.disabled = false;
        allOnBtn.disabled = false;
        allOffBtn.disabled = false;
    }
}

// Animation Functions
async function loadAnimations() {
    try {
        const data = await apiRequest('animations');
        const select = document.getElementById('animation-select');

        data.animations.forEach(anim => {
            const option = document.createElement('option');
            option.value = anim.id;
            option.textContent = anim.name;
            option.dataset.description = anim.description;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load animations:', error);
    }
}

function onAnimationSelect(event) {
    const select = event.target;
    const selectedOption = select.options[select.selectedIndex];
    const infoBox = document.getElementById('animation-info');

    if (select.value) {
        infoBox.textContent = selectedOption.dataset.description;
        infoBox.classList.add('visible');
    } else {
        infoBox.classList.remove('visible');
    }
}

async function startAnimation() {
    const select = document.getElementById('animation-select');
    const animationId = select.value;

    if (!animationId) {
        showToast('Please select an animation first', 'error');
        return;
    }

    try {
        await apiRequest('animation/start', 'POST', { animation: animationId });
        showToast(`Started: ${formatAnimationName(animationId)}`, 'success');
        await updateStatus();
    } catch (error) {
        console.error('Failed to start animation:', error);
    }
}

async function stopAnimation() {
    try {
        await apiRequest('animation/stop', 'POST');
        showToast('Animation stopped', 'success');
        await updateStatus();
    } catch (error) {
        console.error('Failed to stop animation:', error);
    }
}

function formatAnimationName(id) {
    return id.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

// LED Control Functions
async function toggleLED(index) {
    try {
        const result = await apiRequest(`led/${index}`, 'POST', {});
        await updateStatus();
    } catch (error) {
        console.error(`Failed to toggle LED ${index}:`, error);
    }
}

async function setAllLEDs(state) {
    try {
        await apiRequest('all_leds', 'POST', { state: state ? 1 : 0 });
        showToast(state ? 'All LEDs turned ON' : 'All LEDs turned OFF', 'success');
        await updateStatus();
    } catch (error) {
        console.error('Failed to set all LEDs:', error);
    }
}

async function scanSlaves() {
    try {
        const btn = document.getElementById('scan-slaves-btn');
        btn.disabled = true;
        btn.textContent = 'Scanning...';

        const result = await apiRequest('scan', 'POST');
        showToast(`Scan complete. Found ${result.found_count} online slaves.`, 'success');

        btn.textContent = 'Re-scan Slaves';
        btn.disabled = false;
        await updateStatus();
    } catch (error) {
        console.error('Failed to scan slaves:', error);
        document.getElementById('scan-slaves-btn').textContent = 'Re-scan Slaves';
        document.getElementById('scan-slaves-btn').disabled = false;
    }
}

// Status Update Loop
function startStatusUpdates() {
    // Update every 500ms when animation is running, 2s otherwise
    const updateFrequency = () => {
        return systemStatus && systemStatus.animation_running ? 500 : 2000;
    };

    const scheduleNextUpdate = () => {
        statusUpdateInterval = setTimeout(async () => {
            await updateStatus();
            scheduleNextUpdate();
        }, updateFrequency());
    };

    scheduleNextUpdate();
}

// UI Helpers
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (statusUpdateInterval) {
        clearTimeout(statusUpdateInterval);
    }
});
