"""
CSV Storage module for saving Rachio zone run data.
"""
import csv
import os
from datetime import datetime
from typing import List, Dict
from pathlib import Path


class CSVStorage:
    """Handles storing zone run data in CSV format."""

    def __init__(self, output_directory: str = "data"):
        """
        Initialize CSV storage.

        Args:
            output_directory: Directory where CSV files will be stored
        """
        self.output_directory = output_directory
        Path(output_directory).mkdir(parents=True, exist_ok=True)

    def save_zone_events(
        self,
        events: List[Dict],
        controller_name: str,
        filename: str = None
    ) -> str:
        """
        Save zone run events to a CSV file.

        Args:
            events: List of parsed zone event dictionaries
            controller_name: Name of the controller (used in default filename)
            filename: Optional custom filename (without extension)

        Returns:
            Path to the created CSV file
        """
        if not events:
            print(f"No events to save for {controller_name}")
            return None

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{controller_name}_zone_runs_{timestamp}.csv"
        elif not filename.endswith('.csv'):
            filename = f"{filename}.csv"

        filepath = os.path.join(self.output_directory, filename)

        # Define CSV columns
        fieldnames = [
            'controller_name',
            'event_id',
            'event_type',
            'device_id',
            'zone_id',
            'zone_number',
            'zone_name',
            'duration_seconds',
            'start_time',
            'end_time',
            'event_date',
            'create_date',
            'flow_volume_gallons',
            'sub_type'
        ]

        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(events)

        print(f"Saved {len(events)} events to {filepath}")
        return filepath

    def append_zone_events(
        self,
        events: List[Dict],
        filepath: str
    ) -> str:
        """
        Append zone run events to an existing CSV file.

        Args:
            events: List of parsed zone event dictionaries
            filepath: Path to existing CSV file

        Returns:
            Path to the updated CSV file
        """
        if not events:
            print("No events to append")
            return filepath

        # Define CSV columns (same as save_zone_events)
        fieldnames = [
            'controller_name',
            'event_id',
            'event_type',
            'device_id',
            'zone_id',
            'zone_number',
            'zone_name',
            'duration_seconds',
            'start_time',
            'end_time',
            'event_date',
            'create_date',
            'flow_volume_gallons',
            'sub_type'
        ]

        # Check if file exists
        file_exists = os.path.isfile(filepath)

        # Append to CSV
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

            # Write header only if file doesn't exist
            if not file_exists:
                writer.writeheader()

            writer.writerows(events)

        print(f"Appended {len(events)} events to {filepath}")
        return filepath

    def read_zone_events(self, filepath: str) -> List[Dict]:
        """
        Read zone run events from a CSV file.

        Args:
            filepath: Path to CSV file

        Returns:
            List of event dictionaries
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        events = []
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                events.append(row)

        return events

    def get_latest_event_time(self, filepath: str, device_id: str = None) -> int:
        """
        Get the timestamp of the most recent event in a CSV file.
        Useful for incremental data fetching.

        Args:
            filepath: Path to CSV file
            device_id: Optional device ID to filter by (for single-file mode)

        Returns:
            Unix epoch milliseconds of the most recent event, or None if file doesn't exist
        """
        if not os.path.isfile(filepath):
            return None

        events = self.read_zone_events(filepath)
        if not events:
            return None

        # Find the maximum event_date or create_date
        max_time = 0
        for event in events:
            # If device_id is specified, only consider events from that device
            if device_id and event.get('device_id') != device_id:
                continue

            event_time = event.get('event_date') or event.get('create_date')
            if event_time:
                try:
                    time_val = int(event_time)
                    max_time = max(max_time, time_val)
                except (ValueError, TypeError):
                    pass

        return max_time if max_time > 0 else None
