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
        Get zone run events (started, completed, stopped) for a device.

        Filters events to only include zone run related events:
        - DEVICE_ZONE_RUN_STARTED_EVENT
        - DEVICE_ZONE_RUN_COMPLETED_EVENT
        - DEVICE_ZONE_RUN_STOPPED_EVENT

        Args:
            device_id: The unique identifier for the device
            start_time: Start time in Unix epoch milliseconds
            end_time: End time in Unix epoch milliseconds

        Returns:
            List of zone run event dictionaries with relevant fields
        """
        all_events = self.get_device_events(device_id, start_time, end_time)

        zone_run_event_types = {
            'DEVICE_ZONE_RUN_STARTED_EVENT',
            'DEVICE_ZONE_RUN_COMPLETED_EVENT',
            'DEVICE_ZONE_RUN_STOPPED_EVENT'
        }

        zone_events = []
        for event in all_events:
            if event.get('type') in zone_run_event_types:
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
        event_type = event.get('type', '')
        subType = event.get('subType', '')

        # Extract common fields
        parsed = {
            'event_id': event.get('id'),
            'event_type': event_type,
            'sub_type': subType,
            'device_id': event.get('deviceId'),
            'event_date': event.get('eventDate'),
            'create_date': event.get('createDate')
        }

        # Extract zone-specific data from subType object
        if isinstance(subType, dict):
            parsed['zone_id'] = subType.get('zoneId')
            parsed['zone_number'] = subType.get('zoneNumber')
            parsed['zone_name'] = subType.get('zoneName')
            parsed['duration_seconds'] = subType.get('durationSeconds')
            parsed['start_time'] = subType.get('startTime')
            parsed['end_time'] = subType.get('endTime')
            parsed['flow_volume_gallons'] = subType.get('flowVolumeG')

        return parsed


def epoch_ms_to_datetime(epoch_ms: int) -> datetime:
    """Convert Unix epoch milliseconds to datetime object."""
    return datetime.fromtimestamp(epoch_ms / 1000.0)


def datetime_to_epoch_ms(dt: datetime) -> int:
    """Convert datetime object to Unix epoch milliseconds."""
    return int(dt.timestamp() * 1000)
