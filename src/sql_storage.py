"""
SQL Storage module for saving Rachio zone run data to SQLite database.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class SQLStorage:
    """Handles storing zone run data in SQLite database."""

    def __init__(self, database_path: str = "data/rachio_events.db"):
        """
        Initialize SQL storage.

        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path

        # Create directory if it doesn't exist
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database and create tables
        self._init_database()

    def _init_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Create events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zone_events (
                event_id TEXT PRIMARY KEY,
                controller_name TEXT NOT NULL,
                device_id TEXT NOT NULL,
                zone_name TEXT,
                duration_seconds INTEGER,
                end_time INTEGER,
                end_time_datetime TEXT,
                csv_written_datetime TEXT,
                topic TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create index on device_id for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_device_id
            ON zone_events(device_id)
        ''')

        # Create index on end_time for faster time-range queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_end_time
            ON zone_events(end_time)
        ''')

        # Create index on controller_name for faster filtering
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_controller_name
            ON zone_events(controller_name)
        ''')

        conn.commit()
        conn.close()

    def save_zone_events(self, events: List[Dict]) -> int:
        """
        Save zone run events to the database.
        Automatically handles duplicates by ignoring events with existing event_ids.

        Args:
            events: List of parsed zone event dictionaries

        Returns:
            Number of new events inserted
        """
        if not events:
            print("No events to save to database")
            return 0

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        inserted_count = 0
        duplicate_count = 0

        for event in events:
            try:
                cursor.execute('''
                    INSERT INTO zone_events (
                        event_id, controller_name, device_id, zone_name,
                        duration_seconds, end_time, end_time_datetime,
                        csv_written_datetime, topic, summary
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.get('event_id'),
                    event.get('controller_name'),
                    event.get('device_id'),
                    event.get('zone_name'),
                    event.get('duration_seconds'),
                    event.get('end_time'),
                    event.get('end_time_datetime'),
                    event.get('csv_written_datetime'),
                    event.get('topic'),
                    event.get('summary')
                ))
                inserted_count += 1
            except sqlite3.IntegrityError:
                # Event already exists (duplicate event_id)
                duplicate_count += 1
                continue

        conn.commit()
        conn.close()

        if duplicate_count > 0:
            print(f"Filtered out {duplicate_count} duplicate event(s) from database insert")

        print(f"Saved {inserted_count} events to database: {self.database_path}")
        return inserted_count

    def get_latest_event_time(self, device_id: Optional[str] = None) -> Optional[int]:
        """
        Get the timestamp of the most recent event in the database.
        Useful for incremental data fetching.

        Args:
            device_id: Optional device ID to filter by

        Returns:
            Unix epoch milliseconds of the most recent event, or None if no events exist
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        if device_id:
            cursor.execute('''
                SELECT MAX(end_time) FROM zone_events WHERE device_id = ?
            ''', (device_id,))
        else:
            cursor.execute('SELECT MAX(end_time) FROM zone_events')

        result = cursor.fetchone()
        conn.close()

        return result[0] if result and result[0] else None

    def get_events(
        self,
        controller_name: Optional[str] = None,
        device_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Query events from the database with optional filters.

        Args:
            controller_name: Filter by controller name
            device_id: Filter by device ID
            start_time: Filter by start time (Unix epoch milliseconds)
            end_time: Filter by end time (Unix epoch milliseconds)
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        query = "SELECT * FROM zone_events WHERE 1=1"
        params = []

        if controller_name:
            query += " AND controller_name = ?"
            params.append(controller_name)

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)

        if start_time:
            query += " AND end_time >= ?"
            params.append(start_time)

        if end_time:
            query += " AND end_time <= ?"
            params.append(end_time)

        query += " ORDER BY end_time DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_event_count(
        self,
        controller_name: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> int:
        """
        Get the total number of events in the database.

        Args:
            controller_name: Optional filter by controller name
            device_id: Optional filter by device ID

        Returns:
            Total number of events
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        query = "SELECT COUNT(*) FROM zone_events WHERE 1=1"
        params = []

        if controller_name:
            query += " AND controller_name = ?"
            params.append(controller_name)

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)

        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()

        return count

    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics about the events in the database.

        Returns:
            Dictionary with summary statistics
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        # Total events
        cursor.execute("SELECT COUNT(*) FROM zone_events")
        total_events = cursor.fetchone()[0]

        # Total controllers
        cursor.execute("SELECT COUNT(DISTINCT controller_name) FROM zone_events")
        total_controllers = cursor.fetchone()[0]

        # Total zones
        cursor.execute("SELECT COUNT(DISTINCT zone_name) FROM zone_events")
        total_zones = cursor.fetchone()[0]

        # Date range
        cursor.execute("SELECT MIN(end_time), MAX(end_time) FROM zone_events")
        min_time, max_time = cursor.fetchone()

        # Events by controller
        cursor.execute('''
            SELECT controller_name, COUNT(*) as count
            FROM zone_events
            GROUP BY controller_name
            ORDER BY count DESC
        ''')
        events_by_controller = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_events': total_events,
            'total_controllers': total_controllers,
            'total_zones': total_zones,
            'earliest_event': min_time,
            'latest_event': max_time,
            'events_by_controller': events_by_controller
        }

    def export_to_csv(self, output_path: str):
        """
        Export all events from database to CSV file.

        Args:
            output_path: Path to output CSV file
        """
        import csv

        events = self.get_events()

        if not events:
            print("No events to export")
            return

        fieldnames = [
            'controller_name', 'device_id', 'zone_name', 'duration_seconds',
            'end_time', 'end_time_datetime', 'csv_written_datetime',
            'topic', 'summary', 'event_id'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(events)

        print(f"Exported {len(events)} events to {output_path}")
