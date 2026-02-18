#!/usr/bin/env python3
"""
Generate daily dashboard for the past 90 days with Chart.js visualizations.
"""
import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict

from src.sql_storage import SQLStorage
from src.csv_storage import CSVStorage


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'database_path': 'data/rachio_events.db',
            'output_directory': 'data'
        }


def anonymize_controllers(events: List[Dict]) -> tuple:
    """
    Create anonymous names for controllers using capital letters.

    Args:
        events: List of event dictionaries

    Returns:
        Tuple of (anonymization_map, inverse_map)
    """
    # Get unique controller names from events
    unique_controllers = sorted(set(event.get('controller_name', 'Unknown') for event in events))

    # Create mapping using capital letters A, B, C, etc.
    anonymization_map = {}
    inverse_map = {}
    for i, controller in enumerate(unique_controllers):
        # Convert index to letter(s): 0->A, 1->B, ..., 25->Z, 26->AA, 27->AB, etc.
        anon_name = ''
        num = i
        while True:
            anon_name = chr(65 + (num % 26)) + anon_name
            num = num // 26
            if num == 0:
                break
            num -= 1

        anonymization_map[controller] = anon_name
        inverse_map[anon_name] = controller

    return anonymization_map, inverse_map


def process_events_for_daily_charts(events: List[Dict], days: int = 90) -> Dict:
    """
    Process events into daily data structures per controller for the past N days.
    Anonymizes controller names using capital letters (A, B, C, etc.).

    Args:
        events: List of event dictionaries
        days: Number of days to include (default: 90)

    Returns:
        Dictionary containing processed daily data for charts
    """
    # Create anonymization mapping
    anon_map, _ = anonymize_controllers(events)

    # Calculate cutoff date
    cutoff_date = (datetime.now() - timedelta(days=days)).date()

    # Group by date and controller
    daily_data_by_controller = defaultdict(lambda: defaultdict(int))
    overall_daily_data = defaultdict(int)
    controller_totals = defaultdict(int)

    for event in events:
        controller = event.get('controller_name', 'Unknown')
        anon_controller = anon_map.get(controller, controller)
        duration = int(event.get('duration_seconds', 0))

        # Daily data
        if event.get('end_time'):
            date = datetime.fromtimestamp(int(event['end_time']) / 1000.0).date()

            # Only include events from the past N days
            if date >= cutoff_date:
                daily_data_by_controller[anon_controller][date] += duration
                overall_daily_data[date] += duration
                controller_totals[anon_controller] += duration

    # Sort daily data by date
    sorted_overall_daily = sorted(overall_daily_data.items())

    return {
        'controller_totals': dict(controller_totals),
        'daily_data_by_controller': dict(daily_data_by_controller),
        'overall_daily_data': sorted_overall_daily,
        'anonymization_map': anon_map,
        'days': days,
        'start_date': cutoff_date
    }


def generate_daily_html(data: Dict, output_path: str = "data/daily_dashboard.html"):
    """
    Generate HTML dashboard with daily Chart.js visualizations.
    Shows daily data per controller for the past N days.

    Args:
        data: Processed data dictionary
        output_path: Path to output HTML file
    """
    controller_totals = data['controller_totals']
    daily_data_by_controller = data['daily_data_by_controller']
    overall_daily_data = data['overall_daily_data']
    days = data['days']
    start_date = data['start_date']

    # Get all unique dates
    all_dates = sorted(set(date for controller_dates in daily_data_by_controller.values() for date in controller_dates.keys()))

    # Sort controllers by total time for consistent ordering
    sorted_controllers = sorted(controller_totals.items(), key=lambda x: x[1], reverse=True)
    controller_labels = [controller for controller, _ in sorted_controllers]

    # Overall daily data
    daily_labels = [str(date) for date, _ in overall_daily_data]
    daily_values = [duration / 60 for _, duration in overall_daily_data]  # Convert to minutes

    # Daily data per controller (for stacked area chart)
    daily_datasets = []
    colors = [
        'rgba(102, 126, 234, 0.7)',
        'rgba(118, 75, 162, 0.7)',
        'rgba(237, 100, 166, 0.7)',
        'rgba(255, 154, 158, 0.7)',
        'rgba(250, 208, 196, 0.7)',
        'rgba(46, 213, 115, 0.7)',
        'rgba(0, 148, 255, 0.7)',
        'rgba(255, 71, 87, 0.7)',
        'rgba(255, 177, 66, 0.7)',
        'rgba(94, 84, 142, 0.7)',
        'rgba(153, 128, 250, 0.7)',
        'rgba(18, 203, 196, 0.7)',
        'rgba(253, 203, 110, 0.7)',
        'rgba(214, 48, 49, 0.7)',
        'rgba(9, 132, 227, 0.7)',
        'rgba(108, 92, 231, 0.7)',
        'rgba(255, 118, 117, 0.7)',
        'rgba(253, 121, 168, 0.7)',
        'rgba(99, 110, 114, 0.7)',
        'rgba(87, 101, 116, 0.7)'
    ]

    for i, controller in enumerate(controller_labels):
        # Get data for this controller across all dates
        values = [daily_data_by_controller[controller].get(date, 0) / 60 for date in all_dates]
        # Only add controller if it has data
        if sum(values) > 0:
            daily_datasets.append({
                'label': controller,
                'data': values,
                'backgroundColor': colors[i % len(colors)],
                'borderColor': colors[i % len(colors)].replace('0.7', '1'),
                'borderWidth': 2,
                'tension': 0.4,
                'fill': True
            })

    # Calculate stats
    total_controllers = len([c for c in controller_totals.keys() if controller_totals[c] > 0])
    total_minutes = sum(controller_totals.values())
    total_hours = int(total_minutes / 3600)
    end_date = all_dates[-1] if all_dates else start_date

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Watering Summary - Past {days} Days</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}

        .subtitle {{
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            color: #666;
            margin-top: 5px;
            font-size: 0.9em;
        }}

        .charts {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
        }}

        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .chart-title {{
            font-size: 1.4em;
            margin-bottom: 20px;
            color: #333;
            font-weight: 600;
        }}

        canvas {{
            max-height: 500px;
        }}

        footer {{
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 40px;
            padding: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Daily Watering Summary</h1>
        <div class="subtitle">Past {days} Days</div>
        <div class="subtitle">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        <div class="subtitle">{start_date} to {end_date}</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_controllers}</div>
                <div class="stat-label">Active Controllers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{days}</div>
                <div class="stat-label">Days</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_hours:,}</div>
                <div class="stat-label">Total Hours</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{int(total_minutes / 60):,}</div>
                <div class="stat-label">Total Minutes</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <h2 class="chart-title">Overall Daily Watering Time</h2>
                <canvas id="overallDailyChart"></canvas>
            </div>

            <div class="chart-container">
                <h2 class="chart-title">Daily Watering by Controller (Stacked)</h2>
                <canvas id="dailyByControllerChart"></canvas>
            </div>
        </div>

        <footer>
            Daily Watering Summary &copy; {datetime.now().year}
        </footer>
    </div>

    <script>
        // Overall daily chart (bar chart)
        const overallDailyCtx = document.getElementById('overallDailyChart').getContext('2d');
        new Chart(overallDailyCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(daily_labels)},
                datasets: [{{
                    label: 'Total Watering Time (minutes)',
                    data: {json.dumps(daily_values)},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Minutes'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Date'
                        }}
                    }}
                }}
            }}
        }});

        // Daily by controller chart (stacked area chart)
        const dailyByControllerCtx = document.getElementById('dailyByControllerChart').getContext('2d');
        new Chart(dailyByControllerCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps([str(d) for d in all_dates])},
                datasets: {json.dumps(daily_datasets)}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{
                            boxWidth: 12,
                            padding: 10
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        stacked: true,
                        title: {{
                            display: true,
                            text: 'Date'
                        }}
                    }},
                    y: {{
                        stacked: true,
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Minutes'
                        }}
                    }}
                }},
                elements: {{
                    line: {{
                        tension: 0.4,
                        fill: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nDaily dashboard generated: {output_path}")
    print(f"Open this file in your web browser to view the dashboard.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate daily dashboard for the past N days"
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--source',
        choices=['sql', 'csv'],
        default='sql',
        help='Data source: sql or csv (default: sql)'
    )
    parser.add_argument(
        '--csv-file',
        default='data/events.csv',
        help='Path to CSV file if using csv source (default: data/events.csv)'
    )
    parser.add_argument(
        '--output',
        default='data/daily_dashboard.html',
        help='Output HTML file path (default: data/daily_dashboard.html)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days to include (default: 90)'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Load data
    print(f"Loading data for the past {args.days} days...")
    events = []

    if args.source == 'sql':
        database_path = config.get('database_path', 'data/rachio_events.db')
        db = SQLStorage(database_path)

        # Calculate start time for filtering
        from src.rachio_client import datetime_to_epoch_ms
        start_time = datetime_to_epoch_ms(datetime.now() - timedelta(days=args.days))

        events = db.get_events(start_time=start_time)
        print(f"Loaded {len(events)} events from database")

    else:  # csv
        csv_storage = CSVStorage()
        all_events = csv_storage.read_zone_events(args.csv_file)

        # Filter by days
        from src.rachio_client import datetime_to_epoch_ms
        start_time = datetime_to_epoch_ms(datetime.now() - timedelta(days=args.days))
        events = [e for e in all_events if int(e.get('end_time', 0)) >= start_time]

        print(f"Loaded {len(events)} events from CSV")

    if not events:
        print("No events found in the specified time range.")
        return

    # Process events for daily charts
    print("Processing daily data...")
    chart_data = process_events_for_daily_charts(events, args.days)

    # Generate HTML dashboard
    print("Generating daily dashboard...")
    generate_daily_html(chart_data, args.output)


if __name__ == '__main__':
    main()
