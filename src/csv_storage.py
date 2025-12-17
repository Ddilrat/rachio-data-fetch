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

        # Define CSV columns (only useful fields)
        fieldnames = [
            'controller_name',
            'device_id',
            'zone_name',
            'duration_seconds',
            'end_time',
            'end_time_datetime',
            'csv_written_datetime',
            'topic',
            'summary',
            'event_id'
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
        Filters out events with IDs that already exist in the file.

        Args:
            events: List of parsed zone event dictionaries
            filepath: Path to existing CSV file

        Returns:
            Path to the updated CSV file
        """
        if not events:
            print("No events to append")
            return filepath

        # Get existing event IDs to prevent duplicates
        existing_event_ids = set()
        if os.path.isfile(filepath):
            existing_events = self.read_zone_events(filepath)
            existing_event_ids = {event.get('event_id') for event in existing_events if event.get('event_id')}

        # Filter out events that already exist
        new_events = [event for event in events if event.get('event_id') not in existing_event_ids]

        if not new_events:
            print("No new events to append (all events already exist)")
            return filepath

        duplicate_count = len(events) - len(new_events)
        if duplicate_count > 0:
            print(f"Filtered out {duplicate_count} duplicate event(s)")

        # Define CSV columns (same as save_zone_events)
        fieldnames = [
            'controller_name',
            'device_id',
            'zone_name',
            'duration_seconds',
            'end_time',
            'end_time_datetime',
            'csv_written_datetime',
            'topic',
            'summary',
            'event_id'
        ]

        # Check if file exists
        file_exists = os.path.isfile(filepath)

        # Append to CSV
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

            # Write header only if file doesn't exist
            if not file_exists:
                writer.writeheader()

            writer.writerows(new_events)

        print(f"Appended {len(new_events)} events to {filepath}")
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

        # Find the maximum end_time
        max_time = 0
        for event in events:
            # If device_id is specified, only consider events from that device
            if device_id and event.get('device_id') != device_id:
                continue

            event_time = event.get('end_time')
            if event_time:
                try:
                    time_val = int(event_time)
                    max_time = max(max_time, time_val)
                except (ValueError, TypeError):
                    pass

        return max_time if max_time > 0 else None
