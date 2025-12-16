#!/usr/bin/env python3
"""
Utility script to retrieve your Rachio device IDs and information.

This helps you find the device_id needed for config.json.
"""
import sys
import requests
import json


def get_user_devices(api_key: str) -> dict:
    """Get information about the user's devices."""
    url = "https://api.rach.io/1/public/person/info"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def main():
    """Main entry point."""
    print("=" * 60)
    print("Rachio Device Information Utility")
    print("=" * 60)
    print()

    # Get API key from user
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        print("Enter your Rachio API key:")
        print("(Get it from the Rachio mobile app: Profile -> API Key)")
        print()
        api_key = input("API Key: ").strip()

    if not api_key:
        print("Error: API key is required")
        sys.exit(1)

    print()
    print("Fetching your device information...")
    print()

    # Get user info and devices
    user_info = get_user_devices(api_key)

    if not user_info:
        print("Failed to retrieve device information.")
        print("Please check your API key and try again.")
        sys.exit(1)

    # Display user information
    person = user_info.get('person', {})
    print(f"User: {person.get('fullName', 'N/A')}")
    print(f"Email: {person.get('username', 'N/A')}")
    print()

    # Display devices
    devices = user_info.get('devices', [])

    if not devices:
        print("No devices found in your account.")
        sys.exit(0)

    print(f"Found {len(devices)} device(s):")
    print("=" * 60)
    print()

    for idx, device in enumerate(devices, 1):
        print(f"Device {idx}:")
        print(f"  Name: {device.get('name', 'N/A')}")
        print(f"  Device ID: {device.get('id', 'N/A')}")
        print(f"  Model: {device.get('model', 'N/A')}")
        print(f"  Serial Number: {device.get('serialNumber', 'N/A')}")
        print(f"  Status: {device.get('status', 'N/A')}")
        print(f"  Time Zone: {device.get('timeZone', 'N/A')}")

        # Display zones
        zones = device.get('zones', [])
        if zones:
            print(f"  Zones ({len(zones)}):")
            for zone in zones:
                zone_num = zone.get('zoneNumber', 'N/A')
                zone_name = zone.get('name', 'N/A')
                enabled = "enabled" if zone.get('enabled') else "disabled"
                print(f"    Zone {zone_num}: {zone_name} ({enabled})")

        print()

    # Generate sample config
    print("=" * 60)
    print("Sample config.json entry:")
    print("=" * 60)
    print()

    sample_config = {
        "controllers": []
    }

    for device in devices:
        sample_config["controllers"].append({
            "name": device.get('name', 'My Controller'),
            "device_id": device.get('id'),
            "api_key": "YOUR_API_KEY_HERE"
        })

    sample_config["output_directory"] = "data"
    sample_config["base_url"] = "https://api.rach.io/1"

    print(json.dumps(sample_config, indent=2))
    print()


if __name__ == '__main__':
    main()
