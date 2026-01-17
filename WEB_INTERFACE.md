# Web Interface Documentation

The relay/LED controller includes a modern, responsive web interface for easy control and monitoring.

## Overview

The web interface provides a user-friendly way to:
- Control individual LEDs/relays with a click
- Select and run animations from a dropdown menu
- Monitor system status in real-time
- Switch between manual and animation modes

## Quick Start

### Starting the Web Server

**Simplest method:**
```bash
./start_web.sh
```

The script will:
- Check dependencies and install if needed
- Display the local and network URLs
- Start the Flask server on port 5000

**With environment override:**
```bash
./start_web.sh --env test
./start_web.sh --env production
```

**Direct Python execution:**
```bash
python3 controller/web_server.py --host 0.0.0.0 --port 5000
```

### Accessing the Interface

Once started, open a web browser and navigate to:
- **Local access**: `http://localhost:5000`
- **Network access**: `http://[raspberry-pi-ip]:5000`

The startup script displays the exact URLs to use.

## Interface Features

### 1. Status Bar (Top)
- **Environment Badge**: Shows active environment (TEST or PRODUCTION)
- **Mode Badge**: Indicates current mode (Manual or Animation)

### 2. Animation Control Panel

**Animation Selection**
- Dropdown menu lists all available animations
- Hover over selection to see description
- Click "Start Animation" to begin
- Click "Stop Animation" to halt and return to manual mode

**Available Animations:**
- **Random Twinkle**: Random LEDs twinkle on and off
- **Scanning Chase**: Single LED scanning across the display
- **Larson Scanner**: KITT/Cylon style scanner effect
- **Diagnostic Test**: Sequential test pattern for hardware verification

### 3. Manual Control Panel

**Bulk Controls**
- **All On**: Turn all LEDs/relays on simultaneously
- **All Off**: Turn all LEDs/relays off simultaneously

**Individual LED Grid**
- Each LED has its own button showing:
  - LED index number (0-N)
  - Current state (ON/OFF)
- Click any LED button to toggle its state
- Active LEDs glow yellow
- Inactive LEDs are gray

### 4. System Status Panel

Real-time display of:
- **Environment**: Current configuration (test/production)
- **Description**: Environment description from config
- **Total Outputs**: Number of LEDs/relays
- **Mode**: Manual or Animation
- **Current Animation**: Name of running animation (if any)

## Behavior and Modes

### Manual Mode
- Default mode on startup
- All LEDs are off initially
- Click individual LEDs to toggle them
- Use "All On" or "All Off" for bulk control
- LED states persist until changed

### Animation Mode
- Activated when starting an animation
- Manual controls are disabled
- LEDs update automatically based on animation
- Click "Stop Animation" to return to manual mode
- Stopping an animation clears all LEDs

### Mode Switching
- Starting an animation automatically stops manual control
- Stopping an animation returns to manual mode with all LEDs off
- Toggling an LED while animation runs will stop the animation

## Real-Time Updates

The interface updates automatically:
- **During animations**: Updates every 500ms for smooth visual feedback
- **In manual mode**: Updates every 2 seconds to reflect current state
- **Status changes**: All mode and animation changes update immediately

## Responsive Design

The interface adapts to different screen sizes:
- **Desktop**: Full layout with large LED grid
- **Tablet**: Optimized spacing and controls
- **Mobile**: Stacked layout, smaller LED buttons, touch-friendly

## REST API

The web server exposes a REST API for integration with other systems:

### GET /api/status
Get current system status including:
- Environment configuration
- LED states array
- Current mode (manual/animation)
- Running animation name

**Response:**
```json
{
  "environment": "test",
  "total_leds": 3,
  "led_states": [0, 1, 0],
  "manual_mode": true,
  "animation_running": false,
  "current_animation": null,
  "config_description": "Test setup with 1 Arduino UNO..."
}
```

### POST /api/led/<index>
Toggle or set a specific LED state.

**Request body:**
```json
{
  "state": 1  // 1 for ON, 0 for OFF, or omit to toggle
}
```

**Response:**
```json
{
  "success": true,
  "index": 0,
  "state": 1
}
```

### POST /api/all_leds
Set all LEDs to the same state.

**Request body:**
```json
{
  "state": 1  // 1 for ON, 0 for OFF
}
```

### GET /api/animations
Get list of available animations.

**Response:**
```json
{
  "animations": [
    {
      "id": "random_twinkle",
      "name": "Random Twinkle",
      "description": "Random LEDs twinkle on and off"
    },
    ...
  ]
}
```

### POST /api/animation/start
Start an animation.

**Request body:**
```json
{
  "animation": "random_twinkle"
}
```

**Response:**
```json
{
  "success": true,
  "animation": "random_twinkle",
  "running": true
}
```

### POST /api/animation/stop
Stop the current animation.

**Response:**
```json
{
  "success": true,
  "running": false
}
```

## Running as a System Service

To have the web interface start automatically on boot:

### 1. Edit the Service File
```bash
nano relay-controller-web.service
```

Update the following fields:
- `User=`: Your username (default: pi)
- `WorkingDirectory=`: Full path to controller directory
- `ExecStart=`: Full path to web_server.py

### 2. Install the Service
```bash
sudo cp relay-controller-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable relay-controller-web
sudo systemctl start relay-controller-web
```

### 3. Manage the Service
```bash
# Check status
sudo systemctl status relay-controller-web

# Stop service
sudo systemctl stop relay-controller-web

# Restart service
sudo systemctl restart relay-controller-web

# View logs
sudo journalctl -u relay-controller-web -f
```

## Troubleshooting

### Web Server Won't Start

**Port already in use:**
```bash
# Check what's using port 5000
sudo lsof -i :5000

# Use a different port
python3 controller/web_server.py --port 8080
```

**Flask not installed:**
```bash
pip3 install flask
# Or install all dependencies
pip3 install -r requirements.txt
```

### Can't Access from Network

**Firewall blocking:**
```bash
# Allow port 5000 through firewall
sudo ufw allow 5000/tcp
```

**Wrong IP address:**
```bash
# Find your Raspberry Pi's IP
hostname -I
```

### LEDs Not Responding

1. Check USB connection: `ls -l /dev/ttyUSB*`
2. Run `python3 controller/main.py --scan` to verify all slaves are detected.
3. Verify Arduino is running (check Serial Monitor).
4. Check web server logs for errors.
5. Ensure `config.yaml` matches your hardware setup.

### Browser Shows Old Interface

Clear browser cache:
- Chrome/Edge: Ctrl+Shift+Delete
- Firefox: Ctrl+Shift+Delete
- Or use hard refresh: Ctrl+F5

## Security Considerations

The web server is designed for local network use:

- **No authentication**: Anyone on the network can access the interface
- **Bind to localhost only** for single-user access:
  ```bash
  python3 controller/web_server.py --host 127.0.0.1
  ```
- **Use reverse proxy** (nginx/Apache) for public access
- **Add authentication** using Flask-Login or similar for multi-user scenarios

## Development

### File Structure
```
controller/
├── web_server.py           # Flask application and API
├── templates/
│   └── index.html          # Main HTML template
└── static/
    ├── css/
    │   └── style.css       # Stylesheet
    └── js/
        └── app.js          # JavaScript application
```

### Adding New Animations

1. Add animation class to `controller/animation.py`
2. Update `web_server.py` to include it in the `animations` dict
3. Add entry to the animations list in `get_animations()` endpoint

### Modifying the UI

- **HTML**: Edit `controller/templates/index.html`
- **CSS**: Edit `controller/static/css/style.css`
- **JavaScript**: Edit `controller/static/js/app.js`

Changes to static files may require a browser cache clear (Ctrl+F5).

## Performance

- **Lightweight**: Minimal CPU usage, suitable for Raspberry Pi Zero and up
- **Efficient polling**: Update frequency adapts based on mode
- **Thread-safe**: Animation runs in separate thread from Flask
- **Scales**: Tested with 3 LEDs (test) and 576 relays (production)

## Browser Compatibility

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Android)

Uses modern JavaScript (ES6+) and CSS Grid. No frameworks required.
