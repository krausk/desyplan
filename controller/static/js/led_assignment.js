// LED Assignment Application
let assignments = {};
let selectedLED = null;
let zoomLevel = 1;
let panOffset = { x: 0, y: 0 };
let isDragging = false;
let dragStart = { x: 0, y: 0 };

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
        const data = await apiRequest('led-assignments');
        assignments = data.assignments || {};
        showToast('LED assignments loaded', 'success');
    } catch (error) {
        console.error('Failed to load assignments:', error);
        assignments = {};
    }
}

// Save assignments to config
async function saveAssignments() {
    try {
        await apiRequest('led-assignments', 'POST', { assignments });
        showToast('LED assignments saved successfully', 'success');
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

// SVG Click Handler
function handleSVGClick(event) {
    const svg = document.getElementById('desyplan-svg');
    const rect = svg.getBoundingClientRect();
    
    // Calculate click position in SVG coordinates
    // Account for viewBox and display size
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
    const ledId = Date.now();
    assignments[ledId] = {
        x: Math.round(x),
        y: Math.round(y),
        name: `LED_${ledId}`
    };

    renderLEDMarkers();
    updateLEDList();
    drawNeighborGraph();
    selectLED(ledId);
    showToast(`Added LED ${ledId}`, 'success');
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

        // Add tooltip with full ID
        marker.addEventListener('mouseenter', (e) => {
            const tooltip = document.getElementById('tooltip');
            tooltip.textContent = `ID: ${id}\nName: ${data.name}\nPosition: (${data.x}, ${data.y})`;
            tooltip.style.display = 'block';
            tooltip.style.left = (e.clientX + 10) + 'px';
            tooltip.style.top = (e.clientY + 10) + 'px';
        });

        marker.addEventListener('mouseleave', () => {
            document.getElementById('tooltip').style.display = 'none';
        });

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
        return `
            <div class="led-item ${isSelected ? 'selected' : ''}" data-led-id="${id}">
                <span class="led-item-number">${id}</span>
                <span class="led-item-name">${data.name}</span>
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

        // Node circle
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, nodeRadius, 0, Math.PI * 2);
        
        if (isSelected) {
            ctx.fillStyle = '#f59e0b';
            ctx.strokeStyle = '#d97706';
            ctx.lineWidth = 3;
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
    zoomLevel = Math.min(zoomLevel * 1.2, 5);
    updateZoom();
}

function zoomOut() {
    zoomLevel = Math.max(zoomLevel / 1.2, 0.2);
    updateZoom();
}

function resetZoom() {
    zoomLevel = 1;
    panOffset = { x: 0, y: 0 };
    updateZoom();
}

function updateZoom() {
    const svg = document.getElementById('desyplan-svg');
    svg.style.transform = `scale(${zoomLevel})`;
    svg.style.transformOrigin = 'center center';
    document.getElementById('zoom-level').textContent = `${Math.round(zoomLevel * 100)}%`;
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
    
    // Adjust pan offset by zoom level for smooth panning
    panOffset.x += dx / zoomLevel;
    panOffset.y += dy / zoomLevel;
    
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
