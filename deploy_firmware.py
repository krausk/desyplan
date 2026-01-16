#!/usr/bin/env python3
"""
Firmware deployment script for desyplan relay controller.
Reads config.yaml and deploys the appropriate firmware to Arduino boards.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add controller directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'controller'))
from config_loader import Config


def find_arduino_cli():
    """Find arduino-cli in PATH."""
    try:
        result = subprocess.run(['which', 'arduino-cli'],
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def compile_firmware(firmware_path, board_fqbn):
    """Compile Arduino firmware."""
    print(f"\n{'='*60}")
    print(f"Compiling firmware: {firmware_path}")
    print(f"Board: {board_fqbn}")
    print(f"{'='*60}\n")

    cmd = [
        'arduino-cli', 'compile',
        '--fqbn', board_fqbn,
        str(firmware_path)
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Compilation successful!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Compilation failed: {e}")
        return False


def upload_firmware(firmware_path, board_fqbn, port, i2c_address=None):
    """Upload compiled firmware to Arduino."""
    address_str = f" (I2C: 0x{i2c_address:02X})" if i2c_address else ""
    print(f"\n{'='*60}")
    print(f"Uploading to: {port}{address_str}")
    print(f"{'='*60}\n")

    cmd = [
        'arduino-cli', 'upload',
        '--fqbn', board_fqbn,
        '--port', port,
        str(firmware_path)
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ Upload successful to {port}!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Upload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Deploy firmware to Arduino boards based on config.yaml"
    )
    parser.add_argument(
        '--compile-only',
        action='store_true',
        help='Only compile, do not upload'
    )
    parser.add_argument(
        '--port',
        type=str,
        help='Serial port for upload (e.g., /dev/ttyUSB0, /dev/ttyACM0)'
    )
    parser.add_argument(
        '--env',
        type=str,
        help='Override environment from config.yaml'
    )
    args = parser.parse_args()

    # Check for arduino-cli
    arduino_cli = find_arduino_cli()
    if not arduino_cli:
        print("Error: arduino-cli not found in PATH")
        print("Install it from: https://arduino.github.io/arduino-cli/")
        return 1

    print(f"Found arduino-cli: {arduino_cli}")

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
            return 1

    # Print configuration
    config.print_config()

    # Get firmware configuration
    firmware_config = config.env_config['firmware']
    firmware_source = firmware_config['source']
    board_fqbn = firmware_config['board']

    # Get project root and firmware path
    project_root = Path(__file__).parent
    firmware_path = project_root / firmware_source

    if not firmware_path.exists():
        print(f"Error: Firmware not found at {firmware_path}")
        return 1

    # Get the directory containing the .ino file
    firmware_dir = firmware_path.parent

    # Compile firmware
    if not compile_firmware(firmware_dir, board_fqbn):
        return 1

    if args.compile_only:
        print("\n✓ Compile-only mode. Skipping upload.")
        return 0

    # Upload firmware
    if not args.port:
        print("\nError: --port is required for upload")
        print("Example: --port /dev/ttyUSB0")
        print("\nAvailable ports:")
        try:
            result = subprocess.run(['arduino-cli', 'board', 'list'],
                                  capture_output=True, text=True)
            print(result.stdout)
        except subprocess.CalledProcessError:
            pass
        return 1

    # For multi-slave setups, remind about I2C address
    if config.num_slaves > 1:
        print("\n" + "="*60)
        print("WARNING: Multi-slave setup detected!")
        print("="*60)
        print(f"This environment uses {config.num_slaves} slaves.")
        print("You need to flash each Arduino with the correct I2C address.")
        print("\nI2C Addresses needed:")
        for i, addr in enumerate(config.i2c_addresses):
            print(f"  Slave {i+1}: 0x{addr:02X}")
        print("\nEdit the firmware before flashing each board:")
        print(f"  {firmware_path}")
        print('  Change: #define I2C_ADDRESS 0x08')
        print("\nPress Enter to continue or Ctrl+C to abort...")
        input()

    # Upload
    if not upload_firmware(firmware_dir, board_fqbn, args.port):
        return 1

    print("\n" + "="*60)
    print("✓ Deployment complete!")
    print("="*60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
