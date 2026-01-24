// LED Assignment Application
let assignments = {};
let selectedLED = null;
let zoomLevel = 1;
let panOffset = { x: 0, y: 0 };
let isDragging = false;
let dragStart = { x: 0, y: 0 };
let nextLEDId = 1;
let currentSet = 'default';
let mode = 'assign'; // 'assign' or 'trigger'
let pendingPin = null; // Pin number for new LED

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    console.log('Initializing LED assignment application...');

    // Load assignments from config
    await loadAssignments();

    // Setup event listeners
    setupEventListeners();

    // Render LED markers
    renderLEDMarkers();

    // Update LED list
    updateLEDList();

    // Draw neighbor graph
    drawNeighborGraph();

    // Load assignment sets
    await loadAssignmentSets();
}

function setupEventListeners() {
    const svg = document.getElementById('desyplan-svg');
    const container = document.getElementById('svg-container');

    // SVG click to add LED
    svg.addEventListener('click', handleSVGClick);

    // SVG drag for panning
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

    // Mode switch
    document.querySelectorAll('input[name="mode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            handleModeSwitch(e.target.value);
        });
    });

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
        drawNeighborGraph();
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
    drawNeighborGraph();
}

// Load assignments for a specific set
async function loadAssignmentsForSet(setName) {
    try {
        const data = await apiRequest(`led-assignments?set=${setName}`);
        assignments = data.assignments || {};
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

    // In assign mode, add new LED
    if (mode === 'assign') {
        assignments[nextLEDId] = {
            x: Math.round(x),
            y: Math.round(y),
            name: `LED_${nextLEDId}`
        };
        
        nextLEDId++;

        renderLEDMarkers();
        updateLEDList();
        drawNeighborGraph();
        selectLED(ledId);
        showToast(`Added LED ${ledId}. Please assign a pin.`, 'success');
    }
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

// Handle mode switch
function handleModeSwitch(mode) {
    mode = mode;
    
    // Hide pin assignment panel when switching to assign mode
    document.getElementById('pin-assignment-panel').style.display = 'none';
    
    // Update UI based on mode
    renderLEDMarkers();
    updateLEDList();
    drawNeighborGraph();
    
    showToast(`Switched to ${mode} mode`, 'success');
}

// Select LED
function selectLED(ledId) {
    selectedLED = ledId;
    renderLEDMarkers();
    updateLEDList();
    drawNeighborGraph();
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
        drawNeighborGraph();
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
        marker.setAttribute('r', 8);
        
        // Style based on mode and selection
        if (mode === 'trigger') {
            marker.setAttribute('class', 'led-marker trigger-mode');
        } else {
            marker.setAttribute('class', 'led-marker');
        }
        
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
            tooltip.style.left = (e.clientX + 10) + 'px';
            tooltip.style.top = (e.clientY + 10) + 'px';
        });

        marker.addEventListener('mouseleave', () => {
            document.getElementById('tooltip').style.display = 'none';
        });

        // Click handler for trigger mode
        marker.addEventListener('click', (e) => {
            e.stopPropagation();
            
            if (mode === 'trigger') {
                // Trigger the LED
                triggerLED(parseInt(id));
            } else {
                selectLED(parseInt(id));
            }
        });

        markersGroup.appendChild(marker);
        markersGroup.appendChild(label);
    });

    // Update badge
    document.getElementById('led-count-badge').textContent = `${Object.keys(assignments).length} LEDs Assigned`;
}

// Trigger LED (for trigger mode)
async function triggerLED(ledId) {
    const data = assignments[ledId];
    if (!data) return;

    // Get pin number if assigned
    const pin = data.pin !== undefined ? data.pin : null;

    if (pin === null) {
        showToast(`LED ${ledId} has no pin assigned`, 'error');
        return;
    }

    try {
        // Send trigger request to web server
        const response = await fetch('/api/trigger', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pin: pin,
                ledId: ledId,
                name: data.name
            })
        });

        const result = await response.json();
        
        if (response.ok) {
            showToast(`Triggered LED ${ledId} (Pin ${pin})`, 'success');
        } else {
            showToast(`Failed to trigger LED: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to trigger LED:', error);
        showToast(`Error triggering LED: ${error.message}`, 'error');
    }
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

// Draw 2D neighbor graph
function drawNeighborGraph() {
    const canvas = document.getElementById('neighbor-graph');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const ledIds = Object.keys(assignments).map(Number).sort((a, b) => a - b);

    if (ledIds.length === 0) {
        ctx.fillStyle = '#9ca3af';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No LEDs assigned', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Calculate positions
    const positions = {};
    const padding = 40;
    const availableWidth = canvas.width - padding * 2;
    const availableHeight = canvas.height - padding * 2;
    const nodeRadius = 15;

    // Simple layout: distribute nodes in a grid
    const cols = Math.ceil(Math.sqrt(ledIds.length));
    const rows = Math.ceil(ledIds.length / cols);

    ledIds.forEach((id, index) => {
        const col = index % cols;
        const row = Math.floor(index / cols);
        
        positions[id] = {
            x: padding + col * (availableWidth / (cols - 1 || 1)),
            y: padding + row * (availableHeight / (rows - 1 || 1))
        };
    });

    // Draw edges (neighbors within threshold)
    const threshold = 100;
    ctx.strokeStyle = '#d1d5db';
    ctx.lineWidth = 2;

    ledIds.forEach(id1 => {
        ledIds.forEach(id2 => {
            if (id1 < id2) {
                const pos1 = positions[id1];
                const pos2 = positions[id2];
                const dist = Math.sqrt(
                    Math.pow(pos1.x - pos2.x, 2) + 
                    Math.pow(pos1.y - pos2.y, 2)
                );

                if (dist < threshold) {
                    ctx.beginPath();
                    ctx.moveTo(pos1.x, pos1.y);
                    ctx.lineTo(pos2.x, pos2.y);
                    ctx.stroke();
                }
            }
        });
    });

    // Draw nodes
    ledIds.forEach(id => {
        const pos = positions[id];
        const isSelected = selectedLED === id;
        const hasPin = assignments[id].pin !== undefined;

        // Node circle
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2);
        
        if (isSelected) {
            ctx.fillStyle = '#f59e0b';
            ctx.strokeStyle = '#d97706';
            ctx.lineWidth = 3;
        } else if (hasPin) {
            ctx.fillStyle = '#10b981';
            ctx.strokeStyle = '#059669';
            ctx.lineWidth = 2;
        } else {
            ctx.fillStyle = '#3b82f6';
            ctx.strokeStyle = '#2563eb';
            ctx.lineWidth = 2;
        }
        
        ctx.fill();
        ctx.stroke();

        // Node label
        ctx.fillStyle = '#1f2937';
        ctx.font = '10px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(id, pos.x, pos.y);
    });
}

// Zoom functions
function zoomIn() {
    zoomLevel = Math.min(zoomLevel * 1.2, 10);
    updateZoom();
}

function zoomOut() {
    zoomLevel = Math.max(zoomLevel / 1.2, 0.1);
    updateZoom();
}

function resetZoom() {
    zoomLevel = 1;
    panOffset = { x: 0, y: 0 };
    updateZoom();
}

function updateZoom() {
    const svg = document.getElementById('desyplan-svg');
    const container = document.getElementById('svg-container');
    
    // Update zoom level display
    document.getElementById('zoom-level').textContent = `${Math.round(zoomLevel * 100)}%`;
    
    // Apply zoom to the SVG using transform
    // This keeps the viewBox fixed, so the content scales but the coordinate system remains consistent
    svg.style.transform = `scale(${zoomLevel})`;
    svg.style.transformOrigin = 'center center';
    
    // Adjust pan offset to keep center in view
    panOffset.x = (container.offsetWidth - 800) / 2;
    panOffset.y = (container.offsetHeight - 600) / 2;
}

// Mouse drag for panning
function handleMouseDown(event) {
    if (event.target.closest('.led-marker')) return;
    isDragging = true;
    dragStart = { x: event.clientX, y: event.clientY };
    document.getElementById('desyplan-svg').style.cursor = 'grabbing';
}

function handleMouseMove(event) {
    if (!isDragging) return;
    
    const dx = event.clientX - dragStart.x;
    const dy = event.clientY - dragStart.y;
    
    dragStart = { x: event.clientX, y: event.clientY };
    
    // Adjust pan offset
    panOffset.x += dx;
    panOffset.y += dy;
    
    const svg = document.getElementById('desyplan-svg');
    svg.style.transformOrigin = 'center center';
    svg.style.transform = `scale(${zoomLevel}) translate(${panOffset.x}px, ${panOffset.y}px)`;
}

function handleMouseUp() {
    isDragging = false;
    document.getElementById('desyplan-svg').style.cursor = 'grab';
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

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    // Optionally auto-save on unload
    // saveAssignments();
});