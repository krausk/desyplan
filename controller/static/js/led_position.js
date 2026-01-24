// LED Position Application
let assignments = {};
let selectedLED = null;
let zoomLevel = 1;
let panOffset = { x: 0, y: 0 };
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let nextLEDId = 1;
let currentSet = 'default';
let pendingPin = null; // Pin number for new LED
let panzoom = null; // Panzoom instance

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing LED position application...');

    // Load assignments from config
    await loadAssignments();

    // Setup event listeners
    setupEventListeners();

    // Setup touch handlers for mobile
    setupTouchHandlers();

    // Render LED markers
    renderLEDMarkers();

    // Update LED list
    updateLEDList();

    // Load assignment sets
    await loadAssignmentSets();
}

function setupEventListeners() {
    const svg = document.getElementById('desyplan-svg');
    const container = document.getElementById('svg-container');

    // Initialize Panzoom for zoom and pan
    panzoom = Panzoom(svg, {
        minScale: 0.1,
        maxScale: 10,
        step: 0.2,
        contain: 'center',
        disablePan: false,
        disableZoom: false,
        startScale: 1,
        startX: 0,
        startY: 0
    });

    // SVG click to add LED
    svg.addEventListener('click', handleSVGClick);

    // SVG drag for panning (handled by Panzoom)
    svg.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    // Zoom controls
    document.getElementById('zoom-in-btn').addEventListener('click', zoomIn);
    document.getElementById('zoom-out-btn').addEventListener('click', zoomOut);
    document.getElementById('zoom-reset-btn').addEventListener('click', resetZoom);

    // Action buttons
    document.getElementById('save-btn').addEventListener('click', saveAssignments);
    document.getElementById('clear-btn').addEventListener('click', clearAssignments);

    // Pin assignment
    document.getElementById('confirm-pin-btn').addEventListener('click', confirmPinAssignment);
    document.getElementById('pin-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            confirmPinAssignment();
        }
    });

    // Assignment set selector
    document.getElementById('assignment-set-select').addEventListener('change', handleSetChange);
    document.getElementById('create-set-btn').addEventListener('click', createNewSet);
    document.getElementById('delete-set-btn').addEventListener('click', deleteCurrentSet);

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyDown);
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

// Load assignments from config
async function loadAssignments() {
    try {
        // Load assignments for the current set
        await loadAssignmentsForSet(currentSet);
        showToast('LED assignments loaded', 'success');
    } catch (error) {
        console.error('Failed to load assignments:', error);
        assignments = {};
    }
}

// Save assignments to config
async function saveAssignments() {
    try {
        // Save assignments to the current set
        await apiRequest('led-assignments', 'POST', { assignments, set: currentSet });
        showToast(`LED assignments saved successfully to "${currentSet}"`, 'success');
    } catch (error) {
        console.error('Failed to save assignments:', error);
    }
}

// Clear all assignments
async function clearAssignments() {
    if (Object.keys(assignments).length === 0) {
        showToast('No assignments to clear', 'error');
        return;
    }

    if (confirm('Are you sure you want to clear all LED assignments?')) {
        assignments = {};
        renderLEDMarkers();
        updateLEDList();
        showToast('All assignments cleared', 'success');
    }
}

// Load assignment sets
async function loadAssignmentSets() {
    try {
        const data = await apiRequest('led-assignment-sets');
        const sets = data.sets || [];
        
        const select = document.getElementById('assignment-set-select');
        select.innerHTML = '';
        
        sets.forEach(set => {
            const option = document.createElement('option');
            option.value = set.name;
            option.textContent = set.display_name;
            select.appendChild(option);
        });

        // Set current set
        currentSet = select.value;
    } catch (error) {
        console.error('Failed to load assignment sets:', error);
    }
}

// Handle assignment set change
async function handleSetChange(e) {
    currentSet = e.target.value;
    await loadAssignmentsForSet(currentSet);
    renderLEDMarkers();
    updateLEDList();
}

// Load assignments for a specific set
async function loadAssignmentsForSet(setName) {
    try {
        const data = await apiRequest(`led-assignments?set=${setName}`);
        assignments = data.assignments || {};
        
        // Find the maximum LED ID and set nextLEDId to max + 1
        const ledIds = Object.keys(assignments).map(Number);
        if (ledIds.length > 0) {
            const maxId = Math.max(...ledIds);
            nextLEDId = maxId + 1;
        }
        
        showToast(`Loaded set: ${setName}`, 'success');
    } catch (error) {
        console.error(`Failed to load set ${setName}:`, error);
        assignments = {};
    }
}

// Create new assignment set
async function createNewSet() {
    const name = prompt('Enter new set name:');
    if (!name) return;

    try {
        await apiRequest('led-assignment-sets', 'POST', { name });
        showToast(`Set "${name}" created`, 'success');
        await loadAssignmentSets();
    } catch (error) {
        console.error('Failed to create set:', error);
    }
}

// Delete current assignment set
async function deleteCurrentSet() {
    if (currentSet === 'default') {
        showToast('Cannot delete default set', 'error');
        return;
    }

    if (confirm(`Delete set "${currentSet}"?`)) {
        try {
            await apiRequest(`led-assignment-sets/${currentSet}`, 'DELETE');
            showToast(`Set "${currentSet}" deleted`, 'success');
            await loadAssignmentSets();
            currentSet = 'default';
            await loadAssignmentsForSet('default');
        } catch (error) {
            console.error('Failed to delete set:', error);
        }
    }
}

// SVG Click Handler
function handleSVGClick(event) {
    const svg = document.getElementById('desyplan-svg');
    const rect = svg.getBoundingClientRect();
    
    // Calculate click position in SVG coordinates
    const viewBoxWidth = 800;
    const viewBoxHeight = 600;
    const scaleX = viewBoxWidth / rect.width;
    const scaleY = viewBoxHeight / rect.height;
    
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;

    // Check if clicking on existing LED marker
    const clickedMarker = event.target.closest('.led-marker');
    if (clickedMarker) {
        const ledId = parseInt(clickedMarker.dataset.ledId);
        selectLED(ledId);
        return;
    }

    // Add new LED
    assignments[nextLEDId] = {
        x: Math.round(x),
        y: Math.round(y),
        name: `LED_${nextLEDId}`
    };
    
    nextLEDId++;

    renderLEDMarkers();
    updateLEDList();
    selectLED(ledId);
    showToast(`Added LED ${nextLEDId - 1}. Please assign a pin.`, 'success');
}

// Confirm pin assignment
async function confirmPinAssignment() {
    const pinInput = document.getElementById('pin-input');
    const pin = parseInt(pinInput.value);

    if (isNaN(pin)) {
        showToast('Please enter a valid pin number', 'error');
        return;
    }

    if (pendingPin !== null) {
        assignments[pendingPin].pin = pin;
        showToast(`Pin ${pin} assigned to LED ${pendingPin}`, 'success');
        
        // Hide pin assignment panel
        document.getElementById('pin-assignment-panel').style.display = 'none';
        
        // Save assignments
        await saveAssignments();
        
        // Clear pending pin
        pendingPin = null;
    }
}

// Select LED
function selectLED(ledId) {
    selectedLED = ledId;
    renderLEDMarkers();
    updateLEDList();
}

// Remove LED
async function removeLED(ledId) {
    if (confirm(`Remove LED ${ledId}?`)) {
        delete assignments[ledId];
        if (selectedLED === ledId) {
            selectedLED = null;
        }
        renderLEDMarkers();
        updateLEDList();
        showToast(`LED ${ledId} removed`, 'success');
    }
}

// Update LED name
async function updateLEDName(ledId, newName) {
    if (assignments[ledId]) {
        assignments[ledId].name = newName;
        updateLEDList();
    }
}

// Render LED markers on SVG
function renderLEDMarkers() {
    const markersGroup = document.getElementById('led-markers');
    markersGroup.innerHTML = '';

    Object.entries(assignments).forEach(([id, data]) => {
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        marker.setAttribute('cx', data.x);
        marker.setAttribute('cy', data.y);
        marker.setAttribute('r', 4);
        marker.setAttribute('class', 'led-marker');
        marker.dataset.ledId = id;

        // Add label with truncated ID
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', data.x);
        label.setAttribute('y', data.y - 12);
        label.setAttribute('class', 'led-label');
        
        // Truncate long IDs for display
        const displayName = String(id).length > 10 
            ? String(id).substring(0, 8) + '...' 
            : data.name;
        label.textContent = displayName;

        // Add tooltip with full ID and pin info
        marker.addEventListener('mouseenter', (e) => {
            const tooltip = document.getElementById('tooltip');
            const pin = data.pin !== undefined ? `Pin: ${data.pin}` : 'Pin: Not assigned';
            tooltip.innerHTML = `ID: ${id}<br>Name: ${data.name}<br>Position: (${data.x}, ${data.y})<br>${pin}`;
            tooltip.style.display = 'block';
            // Position tooltip below the LED marker
            tooltip.style.left = (data.x - 50) + 'px';
            tooltip.style.top = (data.y + 15) + 'px';
        });

        marker.addEventListener('mouseleave', () => {
            document.getElementById('tooltip').style.display = 'none';
        });

        // Click handler
        marker.addEventListener('click', (e) => {
            e.stopPropagation();
            selectLED(parseInt(id));
        });

        markersGroup.appendChild(marker);
        markersGroup.appendChild(label);
    });

    // Update badge
    document.getElementById('led-count-badge').textContent = `${Object.keys(assignments).length} LEDs Assigned`;
}

// Update LED list in controls panel
function updateLEDList() {
    const list = document.getElementById('led-list');
    const ledIds = Object.keys(assignments).map(Number).sort((a, b) => a - b);

    if (ledIds.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                No LEDs assigned yet.<br>Click on the plan to add LEDs.
            </div>
        `;
        return;
    }

    list.innerHTML = ledIds.map(id => {
        const data = assignments[id];
        const isSelected = selectedLED === id;
        const pinInfo = data.pin !== undefined ? ` (Pin ${data.pin})` : ' (No pin)';
        
        return `
            <div class="led-item ${isSelected ? 'selected' : ''}" data-led-id="${id}">
                <span class="led-item-number">${id}</span>
                <span class="led-item-name">${data.name}${pinInfo}</span>
                <div class="led-item-actions">
                    <button class="btn-icon delete" onclick="removeLED(${id})">×</button>
                </div>
            </div>
        `;
    }).join('');

    // Add click handlers to list items
    list.querySelectorAll('.led-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (!e.target.classList.contains('delete')) {
                const ledId = parseInt(item.dataset.ledId);
                selectLED(ledId);
            }
        });
    });
}

// Zoom functions using Panzoom
function zoomIn() {
    if (panzoom) {
        panzoom.zoomIn();
        updateZoomDisplay();
    }
}

function zoomOut() {
    if (panzoom) {
        panzoom.zoomOut();
        updateZoomDisplay();
    }
}

function resetZoom() {
    if (panzoom) {
        panzoom.reset();
        updateZoomDisplay();
    }
}

function updateZoomDisplay() {
    if (panzoom) {
        const scale = panzoom.getScale();
        document.getElementById('zoom-level').textContent = `${Math.round(scale * 100)}%`;
    }
}

// Mouse drag for panning (handled by Panzoom)
function handleMouseDown(event) {
    if (event.target.closest('.led-marker')) return;
    // Panzoom handles panning automatically
}

function handleMouseMove(event) {
    // Panzoom handles panning automatically
}

function handleMouseUp() {
    // Panzoom handles panning automatically
}

// Keyboard shortcuts
function handleKeyDown(event) {
    if (event.key === 'Delete' || event.key === 'Backspace') {
        if (selectedLED !== null) {
            removeLED(selectedLED);
        }
    }
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

// Haptic feedback for mobile devices
function triggerHapticFeedback(type = 'light') {
    if (navigator.vibrate) {
        switch (type) {
            case 'light':
                navigator.vibrate(10);
                break;
            case 'medium':
                navigator.vibrate(30);
                break;
            case 'heavy':
                navigator.vibrate([50, 50, 50]);
                break;
            case 'success':
                navigator.vibrate([50, 30, 50]);
                break;
            case 'error':
                navigator.vibrate([100, 50, 100]);
                break;
        }
    }
}

// Touch event handlers for mobile
function setupTouchHandlers() {
    const svg = document.getElementById('desyplan-svg');
    
    // Add touch feedback for LED markers
    svg.querySelectorAll('.led-marker').forEach(marker => {
        marker.addEventListener('touchstart', () => {
            triggerHapticFeedback('light');
        });
        
        marker.addEventListener('touchend', () => {
            triggerHapticFeedback('medium');
        });
    });
    
    // Add touch feedback for buttons
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('touchstart', () => {
            triggerHapticFeedback('light');
        });
        
        button.addEventListener('touchend', () => {
            triggerHapticFeedback('medium');
        });
    });
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    // Optionally auto-save on unload
    // saveAssignments();
});
