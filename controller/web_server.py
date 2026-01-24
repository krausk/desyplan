#!/usr/bin/env python3
"""
Web interface for relay/LED controller.
Provides a simple web UI to control individual outputs and select animations.
"""

from flask import Flask, render_template, jsonify, request
import threading
import time
import logging
import os
from display_manager import DisplayManager
from config_loader import Config
from animation import RandomTwinkle, ScanningChase, LarsonScanner, RelayTest, CircleAnimation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state
display_manager = None
config = None
animation_thread = None
animation_running = False
current_animation = None
manual_mode = True  # Start in manual mode
led_states = []


class AnimationThread(threading.Thread):
    """Thread to run animations continuously."""
    def __init__(self, animation):
        super().__init__(daemon=True)
        self.animation = animation
        self.running = True

    def run(self):
        print(f"Animation thread started for {self.animation.__class__.__name__}")
        while self.running:
            try:
                self.animation.step()
            except Exception as e:
                print(f"Animation error: {e}")
                break
        print(f"Animation thread stopped for {self.animation.__class__.__name__}")

    def stop(self):
        self.running = False


def init_controller(config_obj=None):
    """Initialize the display manager and state."""
    global display_manager, config, led_states

    config = config_obj if config_obj else Config()
    display_manager = DisplayManager(config)
    led_states = [0] * display_manager.total_leds

    # Clear all LEDs on startup
    display_manager.clear()
    display_manager.show()

    print(f"Web server initialized for {config.environment} environment")
    print(f"Total LEDs: {display_manager.total_leds}")


@app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current system status."""
    return jsonify({
        'environment': config.environment,
        'total_leds': display_manager.total_leds,
        'leds_per_slave': display_manager.controller.LEDS_PER_SLAVE,
        'slave_online': display_manager.get_slave_status(),
        'led_states': led_states,
        'manual_mode': manual_mode,
        'animation_running': animation_running,
        'current_animation': current_animation,
        'config_description': config.description
    })


@app.route('/api/scan', methods=['POST'])
def scan_slaves():
    """Manually trigger a re-scan of serial ports."""
    found = display_manager.controller.scan_bus()
    return jsonify({
        'success': True,
        'found_count': len(found),
        'slave_online': display_manager.get_slave_status()
    })


@app.route('/api/led/<int:index>', methods=['POST'])
def toggle_led(index):
    """Toggle a specific LED on/off."""
    global led_states, manual_mode, animation_running

    if index < 0 or index >= display_manager.total_leds:
        return jsonify({'error': 'Invalid LED index'}), 400

    # Stop animation if running
    if animation_running:
        stop_animation()

    manual_mode = True

    data = request.get_json()
    state = data.get('state', None)

    if state is None:
        # Toggle
        led_states[index] = 1 - led_states[index]
    else:
        # Set specific state
        led_states[index] = 1 if state else 0

    # Update display
    display_manager.clear()
    for i, s in enumerate(led_states):
        if s:
            display_manager.set_led(i, 1)
    display_manager.show()

    return jsonify({
        'success': True,
        'index': index,
        'state': led_states[index]
    })


@app.route('/api/all_leds', methods=['POST'])
def set_all_leds():
    """Set all LEDs to the same state."""
    global led_states, manual_mode, animation_running

    # Stop animation if running
    if animation_running:
        stop_animation()

    manual_mode = True

    data = request.get_json()
    state = data.get('state', 0)

    led_states = [1 if state else 0] * display_manager.total_leds

    # Update display
    display_manager.clear()
    if state:
        for i in range(display_manager.total_leds):
            display_manager.set_led(i, 1)
    display_manager.show()

    return jsonify({
        'success': True,
        'state': state
    })


@app.route('/api/animation/start', methods=['POST'])
def start_animation():
    """Start an animation."""
    global animation_thread, animation_running, current_animation, manual_mode

    data = request.get_json()
    animation_name = data.get('animation', None)

    if not animation_name:
        return jsonify({'error': 'No animation specified'}), 400

    # Stop current animation if running
    if animation_running:
        stop_animation()

    # Create animation instances on demand
    animations = {
        'random_twinkle': RandomTwinkle(display_manager, speed=0.1, density=0.05),
        'scanning_chase': ScanningChase(display_manager, speed=0.08, width=1),
        'circle_animation': CircleAnimation(display_manager, speed=0.1),
        'larson_scanner': LarsonScanner(display_manager, speed=0.08, width=3),
        'relay_test': RelayTest(display_manager, speed=1.0)
    }

    if animation_name not in animations:
        return jsonify({'error': 'Unknown animation'}), 400

    manual_mode = False
    
    # Start animation thread
    animation_running = True
    current_animation = animation_name
    animation_thread = AnimationThread(animations[animation_name])
    animation_thread.start()

    return jsonify({
        'success': True,
        'animation': animation_name,
        'running': True
    })


@app.route('/api/animation/stop', methods=['POST'])
def stop_animation():
    """Stop the current animation."""
    global animation_thread, animation_running, current_animation, manual_mode

    if animation_thread:
        animation_thread.stop()
        animation_thread.join(timeout=3.0)
        if animation_thread.is_alive():
            print("Warning: Animation thread failed to stop gracefully")
        animation_thread = None
        
    animation_running = False
    current_animation = None

    manual_mode = True

    # Clear all LEDs and reset buffers
    display_manager.reset_hardware()

    # Reset state
    global led_states
    led_states = [0] * display_manager.total_leds

    return jsonify({
        'success': True,
        'running': False
    })


@app.route('/api/animations')
def get_animations():
    """Get list of available animations."""
    animations = [
        {
            'id': 'random_twinkle',
            'name': 'Random Twinkle',
            'description': 'Random LEDs twinkle on and off'
        },
        {
            'id': 'scanning_chase',
            'name': 'Scanning Chase',
            'description': 'Single LED scanning across the display'
        },
        {
            'id': 'circle_animation',
            'name': 'Circle Animation',
            'description': 'Sequence through all LEDs in a loop'
        },
        {
            'id': 'larson_scanner',
            'name': 'Larson Scanner',
            'description': 'KITT/Cylon style scanner effect'
        },
        {
            'id': 'relay_test',
            'name': 'Diagnostic Test',
            'description': 'Sequential test pattern for diagnostics'
        }
    ]

    return jsonify({'animations': animations})


@app.route('/api/led-assignments')
def get_led_assignments():
    """Get LED assignments from config."""
    # Check if a specific set is requested via query parameter
    set_name = request.args.get('set')
    
    if set_name:
        # Load assignments for a specific set
        try:
            import yaml
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
            
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            led_assignments = config_data.get('led_assignments', {})
            
            # Check if the set exists
            if set_name in led_assignments:
                # If it's a set with assignments, return those
                if isinstance(led_assignments[set_name], dict) and 'assignments' in led_assignments[set_name]:
                    return jsonify({'assignments': led_assignments[set_name]['assignments']})
                # If it's a flat assignment dict, return it directly
                elif isinstance(led_assignments[set_name], dict):
                    return jsonify({'assignments': led_assignments[set_name]})
                # If it's the default set, return the assignments
                elif set_name == 'default':
                    return jsonify({'assignments': led_assignments})
            else:
                return jsonify({'assignments': {}}), 404
        except Exception as e:
            logger.error(f"Failed to load assignments for set {set_name}: {e}")
            return jsonify({'assignments': {}}), 500
    else:
        # Return all assignments from the Config object
        assignments = config.led_assignments if hasattr(config, 'led_assignments') else {}
        return jsonify({'assignments': assignments})


@app.route('/api/led-assignment-sets')
def get_led_assignment_sets():
    """Get list of LED assignment sets from config."""
    try:
        import yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        led_assignments = config_data.get('led_assignments', {})
        
        # Extract set names and metadata
        sets = []
        for key, value in led_assignments.items():
            if key == 'default':
                sets.append({
                    'name': 'default',
                    'display_name': 'Default Assignment',
                    'description': 'Default LED assignment set',
                    'is_default': True
                })
            elif isinstance(value, dict) and 'assignments' in value:
                sets.append({
                    'name': key,
                    'display_name': value.get('name', key),
                    'description': value.get('description', ''),
                    'is_default': False
                })
        
        return jsonify({'sets': sets})
    except Exception as e:
        logger.error(f"Failed to get LED assignment sets: {e}")
        return jsonify({'sets': []}), 500


@app.route('/api/led-assignment-sets', methods=['POST'])
def create_led_assignment_set():
    """Create a new LED assignment set."""
    try:
        import yaml
        data = request.get_json()
        set_name = data.get('name')
        
        if not set_name:
            return jsonify({'error': 'Set name required'}), 400
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        led_assignments = config_data.get('led_assignments', {})
        
        # Create new set
        led_assignments[set_name] = {
            'name': set_name,
            'description': f'LED assignment set: {set_name}',
            'assignments': {}
        }
        
        config_data['led_assignments'] = led_assignments
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        return jsonify({'success': True, 'name': set_name})
    except Exception as e:
        logger.error(f"Failed to create LED assignment set: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/led-assignment-sets/<set_name>', methods=['DELETE'])
def delete_led_assignment_set(set_name):
    """Delete an LED assignment set."""
    try:
        import yaml
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        led_assignments = config_data.get('led_assignments', {})
        
        if set_name not in led_assignments:
            return jsonify({'error': 'Set not found'}), 404
        
        # Don't delete default set
        if set_name == 'default':
            return jsonify({'error': 'Cannot delete default set'}), 400
        
        del led_assignments[set_name]
        config_data['led_assignments'] = led_assignments
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Failed to delete LED assignment set: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/led-assignments', methods=['POST'])
def save_led_assignments():
    """Save LED assignments to config."""
    data = request.get_json()
    assignments = data.get('assignments', {})
    set_name = data.get('set', 'default')
    
    # Save to config
    config.set_led_assignments(assignments)
    
    # Persist to file
    try:
        import yaml
        # Get config path
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Get existing led_assignments structure
        led_assignments = config_data.get('led_assignments', {})
        
        # If set_name is 'default', save directly to root
        if set_name == 'default':
            config_data['led_assignments'] = assignments
        else:
            # Save to specific assignment set
            if not isinstance(led_assignments, dict):
                led_assignments = {}
            
            # Ensure the set has the proper structure
            if not isinstance(led_assignments[set_name], dict):
                led_assignments[set_name] = {
                    'name': set_name,
                    'description': f'LED assignment set: {set_name}',
                    'assignments': {}
                }
            
            # Add assignments to the set
            led_assignments[set_name]['assignments'] = assignments
            config_data['led_assignments'] = led_assignments
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        
        return jsonify({'success': True, 'assignments': assignments, 'set': set_name})
    except Exception as e:
        logger.error(f"Failed to save assignments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trigger', methods=['POST'])
def trigger_led():
    """Trigger a specific LED via its assigned pin."""
    global led_states, manual_mode, animation_running
    
    data = request.get_json()
    pin = data.get('pin')
    led_id = data.get('ledId')
    name = data.get('name', 'Unknown')
    
    if pin is None:
        return jsonify({'error': 'Pin number required'}), 400
    
    if led_id is None:
        return jsonify({'error': 'LED ID required'}), 400
    
    # Stop animation if running
    if animation_running:
        stop_animation()
    
    manual_mode = True
    
    # Update LED state
    if 0 <= led_id < len(led_states):
        led_states[led_id] = 1
    
    # Update display
    display_manager.clear()
    for i, s in enumerate(led_states):
        if s:
            display_manager.set_led(i, 1)
    display_manager.show()
    
    logger.info(f"Triggered LED {led_id} (Pin {pin}) - {name}")
    
    return jsonify({
        'success': True,
        'led_id': led_id,
        'pin': pin,
        'name': name
    })


@app.route('/led-assignment')
def led_assignment():
    """Serve the LED assignment page."""
    return render_template('led_assignment.html')


def run_server(host='0.0.0.0', port=5000, config_obj=None):
    """Run the Flask web server."""
    init_controller(config_obj)
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Web interface for relay/LED controller")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--env', type=str, help='Override environment from config.yaml')
    args = parser.parse_args()

    # Load configuration
    config = Config()

    # Override environment if specified
    if args.env:
        if args.env in config.config['environments']:
            config.environment = args.env
            config.env_config = config.config['environments'][args.env]
            print(f"Environment overridden to: {args.env}")
        else:
            print(f"Error: Environment '{args.env}' not found in config.yaml")
            exit(1)

    config.print_config()

    print(f"\nStarting web server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop\n")

    try:
        run_server(host=args.host, port=args.port, config_obj=config)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if display_manager:
            display_manager.clear()
            display_manager.show()
            display_manager.close()
