#!/usr/bin/env python3
"""
Add pin numbers to LED assignments in config.yaml.
"""

import yaml
import sys

def add_pins_to_assignments():
    """Add pin numbers to all LED assignments that are missing them."""
    
    config_path = 'config.yaml'
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    led_assignments = config['led_assignments']
    
    # Find the next available pin number
    used_pins = set()
    for key, value in led_assignments.items():
        if key != 'default' and 'pin' in value:
            used_pins.add(value['pin'])
    
    next_pin = 0
    if used_pins:
        next_pin = max(used_pins) + 1
    
    # Add pin numbers to missing assignments
    added_count = 0
    for key, value in led_assignments.items():
        if key != 'default' and 'pin' not in value:
            value['pin'] = next_pin
            next_pin += 1
            added_count += 1
            print(f"Added pin {value['pin']} to {key}")
    
    if added_count > 0:
        # Save the updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"\n✓ Added {added_count} pin numbers to LED assignments")
        print(f"✓ Updated config.yaml")
        return True
    else:
        print("\n✓ All LED assignments already have pin numbers")
        return False

if __name__ == '__main__':
    success = add_pins_to_assignments()
    sys.exit(0 if success else 1)