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
                        'i2c_addresses': [0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D],
                        'i2c_bus': 1
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
    def i2c_addresses(self):
        return self.env_config['hardware']['i2c_addresses']

    @property
    def i2c_bus(self):
        return self.env_config['hardware']['i2c_bus']

    @property
    def min_relay_delay(self):
        return self.env_config['timing']['min_relay_delay']

    @property
    def description(self):
        return self.env_config.get('description', f'{self.environment} environment')

    def get_pin_mapping(self):
        """Get explicit pin mapping if defined (for test environments)."""
        return self.env_config['hardware'].get('pin_mapping', None)

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
        print(f"  I2C Addresses: {[hex(addr) for addr in self.i2c_addresses]}")
        print(f"  I2C Bus: {self.i2c_bus}")
        if self.get_pin_mapping():
            print(f"  Pin Mapping: {self.get_pin_mapping()}")
        print(f"\nTiming Configuration:")
        print(f"  Min Relay Delay: {self.min_relay_delay}s")
        print(f"{'='*60}\n")
