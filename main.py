#!/usr/bin/env python3
"""
Main script for collecting Rachio station run time data.

This script fetches zone run events from Rachio controllers and stores them in CSV files.
It can be run manually or scheduled to collect data periodically.
"""
import json
import sys
import argparse
from datetime import datetime, timedelta
from typing import Optional

from src.rachio_client import RachioClient, datetime_to_epoch_ms
from src.csv_storage import CSVStorage


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


def fetch_and_save_data(
    config: dict,
    days: int = 7,
    incremental: bool = False
):
    """
    Fetch zone run data from all configured controllers and save to a single CSV file.

    Args:
        config: Configuration dictionary
        days: Number of days of historical data to fetch (default: 7)
        incremental: If True, only fetch new data since last run (default: False)
    """
    storage = CSVStorage(config.get('output_directory', 'data'))
    base_url = config.get('base_url', 'https://api.rach.io/1')

    controllers = config.get('controllers', [])
    if not controllers:
        print("Error: No controllers configured in config.json")
        sys.exit(1)

    # Single CSV file for all controllers
    csv_filename = "rachio_zone_runs.csv"
    csv_filepath = f"{config.get('output_directory', 'data')}/{csv_filename}"

    print(f"Fetching data for {len(controllers)} controller(s)...")
    print(f"Output file: {csv_filepath}")

    all_events = []
    summary_by_controller = {}

    for controller in controllers:
        name = controller.get('name', 'Unknown')
        device_id = controller.get('device_id')
        api_key = controller.get('api_key')

        if not device_id or not api_key:
            print(f"Warning: Skipping {name} - missing device_id or api_key")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {name}")
        print(f"{'='*60}")

        try:
            # Initialize client
            client = RachioClient(api_key, base_url)

            # Get device info
            device_info = client.get_device_info(device_id)
            print(f"Device Name: {device_info.get('name', 'N/A')}")
            print(f"Model: {device_info.get('model', 'N/A')}")
            print(f"Status: {device_info.get('status', 'N/A')}")

            # Determine time range
            end_time = datetime_to_epoch_ms(datetime.now())

            if incremental:
                # Get last event time for this specific device from the shared CSV
                last_event_time = storage.get_latest_event_time(csv_filepath, device_id)
                if last_event_time:
                    start_time = last_event_time + 1  # Start from 1ms after last event
                    print(f"Incremental fetch from {datetime.fromtimestamp(start_time/1000)}")
                else:
                    start_time = datetime_to_epoch_ms(datetime.now() - timedelta(days=days))
                    print(f"No existing data found for this controller, fetching last {days} days")
            else:
                start_time = datetime_to_epoch_ms(datetime.now() - timedelta(days=days))
                print(f"Fetching last {days} days of data")

            print(f"Time range: {datetime.fromtimestamp(start_time/1000)} to {datetime.fromtimestamp(end_time/1000)}")

            # Fetch zone run events
            print("Fetching zone run events...")
            zone_events = client.get_zone_run_events(device_id, start_time, end_time)
            print(f"Found {len(zone_events)} zone run events")

            if zone_events:
                # Parse events and add controller name
                parsed_events = [client.parse_zone_event(event) for event in zone_events]
                for event in parsed_events:
                    event['controller_name'] = name

                all_events.extend(parsed_events)

                # Build summary
                zone_summary = {}
                for event in parsed_events:
                    zone_name = event.get('zone_name', 'Unknown')
                    zone_summary[zone_name] = zone_summary.get(zone_name, 0) + 1

                summary_by_controller[name] = {
                    'total_events': len(parsed_events),
                    'zones': zone_summary
                }

                print(f"\nFound {len(parsed_events)} events:")
                for zone_name, count in sorted(zone_summary.items()):
                    print(f"  {zone_name}: {count} events")
            else:
                print("No zone run events found in the specified time range")
                summary_by_controller[name] = {
                    'total_events': 0,
                    'zones': {}
                }

        except Exception as e:
            print(f"Error processing {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    # Save all events to single CSV file
    if all_events:
        print(f"\n{'='*60}")
        print(f"Saving {len(all_events)} total events to CSV...")
        print(f"{'='*60}")

        if incremental and storage.get_latest_event_time(csv_filepath):
            storage.append_zone_events(all_events, csv_filepath)
        else:
            storage.save_zone_events(all_events, "all_controllers", csv_filename)

        # Print overall summary
        print("\n" + "="*60)
        print("Summary by Controller:")
        print("="*60)
        for controller_name, summary in summary_by_controller.items():
            print(f"\n{controller_name}: {summary['total_events']} events")
            for zone_name, count in sorted(summary['zones'].items()):
                print(f"  {zone_name}: {count} events")
    else:
        print("\nNo events to save.")

    print(f"\n{'='*60}")
    print("Data collection complete!")
    print(f"{'='*60}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch Rachio station run time data and save to CSV"
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days of historical data to fetch (default: 7)'
    )
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Only fetch new data since last run (appends to existing CSV)'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Fetch and save data
    fetch_and_save_data(config, args.days, args.incremental)


if __name__ == '__main__':
    main()
