import yaml
import os

class Config:
    """
    Manages environment configuration for the relay controller system.
    Loads settings from config.yaml and provides environment-specific parameters.
    """

    def __init__(self, config_path=None):
        if config_path is None:
            # Default to config.yaml in project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(project_root, 'config.yaml')

        self.config_path = config_path
        self.config = self._load_config()
        self.environment = self.config.get('active_environment', 'production')
        self.env_config = self.config['environments'][self.environment]

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {self.config_path}")
            print("Using default production configuration.")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            print("Using default production configuration.")
            return self._get_default_config()

    def _get_default_config(self):
        """Fallback configuration if file is missing."""
        return {
            'active_environment': 'production',
            'environments': {
                'production': {
                    'hardware': {
                        'num_slaves': 6,
                        'leds_per_slave': 96,
                        'total_leds': 576,
                        'serial_ports': ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyUSB2",
                                        "/dev/ttyUSB3", "/dev/ttyUSB4", "/dev/ttyUSB5"],
                        'serial_baudrate': 115200
                    },
                    'timing': {
                        'min_relay_delay': 0.05
                    }
                }
            }
        }

    @property
    def num_slaves(self):
        return self.env_config['hardware']['num_slaves']

    @property
    def leds_per_slave(self):
        return self.env_config['hardware']['leds_per_slave']

    @property
    def total_leds(self):
        return self.env_config['hardware']['total_leds']

    @property
    def serial_ports(self):
        return self.env_config['hardware']['serial_ports']

    @property
    def serial_baudrate(self):
        return self.env_config['hardware'].get('serial_baudrate', 115200)

    @property
    def min_relay_delay(self):
        return self.env_config['timing']['min_relay_delay']

    @property
    def description(self):
        return self.env_config.get('description', f'{self.environment} environment')

    def get_pin_mapping(self):
        """Get explicit pin mapping if defined (for test environments)."""
        return self.env_config['hardware'].get('pin_mapping', None)

    @property
    def led_assignments(self):
        """Get LED assignments from config."""
        return self.config.get('led_assignments', {})
    
    @led_assignments.setter
    def led_assignments(self, value):
        """Set LED assignments in config."""
        self.config['led_assignments'] = value
    
    def set_led_assignments(self, assignments):
        """Set LED assignments in config (deprecated, use property setter instead)."""
        self.config['led_assignments'] = assignments

    def print_config(self):
        """Print current configuration for debugging."""
        print(f"\n{'='*60}")
        print(f"Active Environment: {self.environment}")
        print(f"Description: {self.description}")
        print(f"{'='*60}")
        print(f"Hardware Configuration:")
        print(f"  Controller Type: {self.env_config['hardware'].get('controller_type', 'Arduino Mega 2560')}")
        print(f"  Number of Slaves: {self.num_slaves}")
        print(f"  LEDs per Slave: {self.leds_per_slave}")
        print(f"  Total LEDs: {self.total_leds}")
        print(f"  Serial Ports: {self.serial_ports}")
        print(f"  Serial Baudrate: {self.serial_baudrate}")
        if self.get_pin_mapping():
            print(f"  Pin Mapping: {self.get_pin_mapping()}")
        print(f"\nTiming Configuration:")
        print(f"  Min Relay Delay: {self.min_relay_delay}s")
        print(f"{'='*60}\n")
