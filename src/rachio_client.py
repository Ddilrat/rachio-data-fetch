"""
Rachio API Client for fetching device events and run time data.
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time


class RachioClient:
    """Client for interacting with the Rachio API."""

    def __init__(self, api_key: str, base_url: str = "https://api.rach.io/1"):
        """
        Initialize the Rachio API client.

        Args:
            api_key: OAuth2 token from Rachio mobile app
            base_url: Base URL for Rachio API (default: https://api.rach.io/1)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def get_device_info(self, device_id: str) -> Dict:
        """
        Get information about a specific device.

        Args:
            device_id: The unique identifier for the device

        Returns:
            Dict containing device information
        """
        url = f"{self.base_url}/public/device/{device_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_device_events(
        self,
        device_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """
        Get events for a device within a time range.

        Args:
            device_id: The unique identifier for the device
            start_time: Start time in Unix epoch milliseconds (defaults to 7 days ago)
            end_time: End time in Unix epoch milliseconds (defaults to now)

        Returns:
            List of event dictionaries
        """
        # Default to last 7 days if not specified
        if end_time is None:
            end_time = int(time.time() * 1000)
        if start_time is None:
            start_time = int((time.time() - (7 * 24 * 60 * 60)) * 1000)

        url = f"{self.base_url}/public/device/{device_id}/event"
        params = {
            'startTime': start_time,
            'endTime': end_time
        }

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_zone_run_events(
        self,
        device_id: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[Dict]:
        """
        Get zone run completion events for a device.

        Filters events to only include completed zone runs (ZONE_COMPLETED)
        which contain the actual runtime duration information.

        Automatically chunks requests into 35-day segments to work around
        Rachio API's undocumented time range limit.

        Args:
            device_id: The unique identifier for the device
            start_time: Start time in Unix epoch milliseconds
            end_time: End time in Unix epoch milliseconds

        Returns:
            List of zone run completion event dictionaries with runtime data
        """
        # Calculate time range in days
        RACHIO_MAX_DAYS = 35  # Rachio API limit (undocumented)
        MAX_TIME_RANGE_MS = RACHIO_MAX_DAYS * 24 * 60 * 60 * 1000

        # Set defaults if not provided
        if end_time is None:
            end_time = int(time.time() * 1000)
        if start_time is None:
            start_time = int((time.time() - (7 * 24 * 60 * 60)) * 1000)

        time_range_ms = end_time - start_time

        # If range is within limit, make single request
        if time_range_ms <= MAX_TIME_RANGE_MS:
            all_events = self.get_device_events(device_id, start_time, end_time)
        else:
            # Chunk into multiple requests
            print(f"Time range exceeds {RACHIO_MAX_DAYS} days, chunking into multiple requests...")
            all_events = []
            current_start = start_time
            chunk_count = 0

            while current_start < end_time:
                current_end = min(current_start + MAX_TIME_RANGE_MS, end_time)
                chunk_count += 1

                print(f"  Fetching chunk {chunk_count}: {datetime.fromtimestamp(current_start/1000)} to {datetime.fromtimestamp(current_end/1000)}")
                chunk_events = self.get_device_events(device_id, current_start, current_end)
                all_events.extend(chunk_events)

                # Move to next chunk (add 1ms to avoid overlap)
                current_start = current_end + 1

        zone_events = []
        for event in all_events:
            if event.get('type') == 'ZONE_STATUS' and event.get('subType') == 'ZONE_COMPLETED':
                zone_events.append(event)

        return zone_events

    def parse_zone_event(self, event: Dict) -> Dict:
        """
        Parse a zone run event into a standardized format.

        Args:
            event: Raw event dictionary from API

        Returns:
            Parsed event with standardized fields
        """
        import re

        event_type = event.get('type', '')
        subType = event.get('subType', '')
        summary = event.get('summary', '')

        # Extract common fields
        parsed = {
            'event_id': event.get('id'),
            'event_type': event_type,
            'sub_type': subType,
            'device_id': event.get('deviceId'),
            'event_date': event.get('eventDate'),
            'create_date': event.get('createDate'),
            'zone_id': None,
            'zone_number': None,
            'zone_name': None,
            'duration_seconds': None,
            'start_time': None,
            'end_time': None,
            'flow_volume_gallons': None,
            'topic': event.get('topic'),
            'summary': summary
        }

        # Parse zone information from summary text
        # Examples:
        # "grass completed watering at 07:10 AM (CST) for 3 minutes."
        # "Zone 2 began watering at 07:01 AM (CST)."
        # "front began watering at 06:58 AM (CST)."

        # Extract zone name (everything before "completed" or "began")
        zone_match = re.match(r'^(.+?)\s+(completed|began)\s+watering', summary)
        if zone_match:
            parsed['zone_name'] = zone_match.group(1).strip()

        # Extract duration from "for X minutes"
        duration_match = re.search(r'for\s+(\d+)\s+minutes?', summary)
        if duration_match:
            duration_minutes = int(duration_match.group(1))
            parsed['duration_seconds'] = duration_minutes * 60

        # For ZONE_STARTED events, use eventDate as start_time
        if subType == 'ZONE_STARTED':
            parsed['start_time'] = event.get('eventDate')

        # For ZONE_COMPLETED events, use eventDate as end_time
        if subType == 'ZONE_COMPLETED':
            end_time_ms = event.get('eventDate')
            parsed['end_time'] = end_time_ms
            # Add human-readable datetime
            if end_time_ms:
                parsed['end_time_datetime'] = epoch_ms_to_datetime(end_time_ms).strftime('%Y-%m-%d %H:%M:%S')

        return parsed


def epoch_ms_to_datetime(epoch_ms: int) -> datetime:
    """Convert Unix epoch milliseconds to datetime object."""
    return datetime.fromtimestamp(epoch_ms / 1000.0)


def datetime_to_epoch_ms(dt: datetime) -> int:
    """Convert datetime object to Unix epoch milliseconds."""
    return int(dt.timestamp() * 1000)
