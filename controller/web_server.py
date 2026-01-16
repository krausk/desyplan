#!/usr/bin/env python3
"""
Web interface for relay/LED controller.
Provides a simple web UI to control individual outputs and select animations.
"""

from flask import Flask, render_template, jsonify, request
import threading
import time
from display_manager import DisplayManager
from config_loader import Config
from animation import RandomTwinkle, ScanningChase, LarsonScanner, RelayTest

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
        global animation_running
        while self.running and animation_running:
            try:
                self.animation.step()
            except Exception as e:
                print(f"Animation error: {e}")
                break

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
        'led_states': led_states,
        'manual_mode': manual_mode,
        'animation_running': animation_running,
        'current_animation': current_animation,
        'config_description': config.description
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

    # Create animation instance
    animations = {
        'random_twinkle': RandomTwinkle(display_manager, speed=0.1, density=0.05),
        'scanning_chase': ScanningChase(display_manager, speed=0.08, width=1),
        'larson_scanner': LarsonScanner(display_manager, speed=0.08, width=3),
        'relay_test': RelayTest(display_manager, speed=1.0)
    }

    if animation_name not in animations:
        return jsonify({'error': 'Unknown animation'}), 400

    manual_mode = False
    animation_running = True
    current_animation = animation_name

    # Start animation thread
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

    if animation_running and animation_thread:
        animation_running = False
        animation_thread.stop()
        animation_thread.join(timeout=2.0)
        animation_thread = None
        current_animation = None

    manual_mode = True

    # Clear all LEDs
    display_manager.clear()
    display_manager.show()

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
