#!/usr/bin/env python3
"""
Script to fetch all device information from Rachio controllers and save to JSON.

This script retrieves detailed device information for each configured controller
and stores it in a structured JSON file in the data directory.
"""
import json
import sys
import argparse
import os
from datetime import datetime
from typing import List, Dict

from src.rachio_client import RachioClient


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Please copy 'config.json.example' to 'config.json' and add your API keys.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)


def fetch_all_device_info(config: dict) -> List[Dict]:
    """
    Fetch detailed device information for all configured controllers.

    Args:
        config: Configuration dictionary

    Returns:
        List of device information dictionaries
    """
    base_url = config.get('base_url', 'https://api.rach.io/1')
    controllers = config.get('controllers', [])

    if not controllers:
        print("Error: No controllers configured in config.json")
        sys.exit(1)

    all_devices = []

    print(f"Fetching device information for {len(controllers)} controller(s)...")
    print("=" * 60)

    for controller in controllers:
        name = controller.get('name', 'Unknown')
        device_id = controller.get('device_id')
        api_key = controller.get('api_key')

        if not device_id or not api_key:
            print(f"Warning: Skipping {name} - missing device_id or api_key")
            continue

        print(f"\nFetching: {name}")
        print(f"Device ID: {device_id}")

        try:
            # Initialize client
            client = RachioClient(api_key, base_url)

            # Get device info
            device_info = client.get_device_info(device_id)

            # Add metadata
            device_info['config_name'] = name
            device_info['fetched_at'] = datetime.now().isoformat()

            all_devices.append(device_info)

            # Display summary
            print(f"  Name: {device_info.get('name', 'N/A')}")
            print(f"  Model: {device_info.get('model', 'N/A')}")
            print(f"  Status: {device_info.get('status', 'N/A')}")
            zones = device_info.get('zones', [])
            print(f"  Zones: {len(zones)}")

        except Exception as e:
            print(f"Error fetching {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    return all_devices


def save_devices_to_json(devices: List[Dict], output_dir: str, filename: str = "devices.json"):
    """
    Save device information to JSON file.

    Args:
        devices: List of device information dictionaries
        output_dir: Directory to save the file
        filename: Name of the output file (default: devices.json)
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, filename)

    # Create output structure with metadata
    output = {
        "metadata": {
            "total_devices": len(devices),
            "generated_at": datetime.now().isoformat(),
            "description": "Device information from Rachio API for all configured controllers"
        },
        "devices": devices
    }

    # Write to file
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Successfully saved {len(devices)} device(s) to: {filepath}")
    print(f"{'=' * 60}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch Rachio device information and save to JSON"
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--output',
        default='devices.json',
        help='Output filename (default: devices.json)'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Fetch device information
    devices = fetch_all_device_info(config)

    if not devices:
        print("\nNo device information retrieved.")
        sys.exit(1)

    # Save to JSON
    output_dir = config.get('output_directory', 'data')
    save_devices_to_json(devices, output_dir, args.output)


if __name__ == '__main__':
    main()
