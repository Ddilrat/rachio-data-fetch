#!/usr/bin/env python3
"""
Generate weekly per-household dashboard with separate charts for each year.
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


def get_week_key(date):
    """
    Get ISO week key in format 'YYYY-WW'.
    Week starts on Monday.
    """
    iso_cal = date.isocalendar()
    return f"{iso_cal[0]}-W{iso_cal[1]:02d}"


def process_events_for_weekly_charts(events: List[Dict]) -> Dict:
    """
    Process events into weekly data structures per controller, grouped by year.
    Anonymizes controller names using capital letters (A, B, C, etc.).

    Args:
        events: List of event dictionaries

    Returns:
        Dictionary containing processed weekly data for charts
    """
    # Create anonymization mapping
    anon_map, _ = anonymize_controllers(events)

    # Group by year, week, and controller
    # Structure: {year: {controller: {week: duration}}}
    yearly_weekly_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for event in events:
        controller = event.get('controller_name', 'Unknown')
        anon_controller = anon_map.get(controller, controller)
        duration = int(event.get('duration_seconds', 0))

        # Weekly data
        if event.get('end_time'):
            date = datetime.fromtimestamp(int(event['end_time']) / 1000.0)
            year = date.year
            week_key = get_week_key(date)

            yearly_weekly_data[year][anon_controller][week_key] += duration

    return {
        'yearly_weekly_data': dict(yearly_weekly_data),
        'anonymization_map': anon_map
    }


def generate_weekly_html(data: Dict, output_path: str = "data/weekly_dashboard.html"):
    """
    Generate HTML dashboard with weekly Chart.js visualizations.
    Shows separate charts for each year with weekly data per controller.

    Args:
        data: Processed data dictionary
        output_path: Path to output HTML file
    """
    yearly_weekly_data = data['yearly_weekly_data']

    # Get all unique controllers across all years
    all_controllers = set()
    for year_data in yearly_weekly_data.values():
        all_controllers.update(year_data.keys())
    all_controllers = sorted(all_controllers)

    # Sort years in descending order (most recent first)
    sorted_years = sorted(yearly_weekly_data.keys(), reverse=True)

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

    # Prepare chart data for each year
    charts_html = ""
    charts_js = ""

    for year in sorted_years:
        year_data = yearly_weekly_data[year]

        # Get all weeks for this year
        all_weeks = set()
        for controller_weeks in year_data.values():
            all_weeks.update(controller_weeks.keys())
        all_weeks = sorted(all_weeks)

        if not all_weeks:
            continue

        # Create datasets for each controller
        datasets = []
        for i, controller in enumerate(all_controllers):
            values = [year_data[controller].get(week, 0) / 60 for week in all_weeks]
            # Only add controller if it has data this year
            if sum(values) > 0:
                datasets.append({
                    'label': controller,
                    'data': values,
                    'backgroundColor': colors[i % len(colors)],
                    'borderColor': colors[i % len(colors)].replace('0.7', '1'),
                    'borderWidth': 2,
                    'tension': 0.4
                })

        # Calculate total for this year
        year_total = sum(sum(weeks.values()) for weeks in year_data.values())
        year_total_hours = int(year_total / 3600)

        # Add chart container
        charts_html += f'''
            <div class="chart-container">
                <h2 class="chart-title">{year} - Weekly Watering by Controller ({year_total_hours:,} hours total)</h2>
                <canvas id="weeklyChart{year}"></canvas>
            </div>
        '''

        # Add chart JavaScript
        charts_js += f'''
        // {year} Weekly chart
        const weeklyCtx{year} = document.getElementById('weeklyChart{year}').getContext('2d');
        new Chart(weeklyCtx{year}, {{
            type: 'line',
            data: {{
                labels: {json.dumps(all_weeks)},
                datasets: {json.dumps(datasets)}
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
                            text: 'Week'
                        }}
                    }}
                }}
            }}
        }});
        '''

    # Calculate overall stats
    total_controllers = len(all_controllers)
    total_years = len(sorted_years)
    total_minutes = sum(sum(sum(weeks.values()) for weeks in year_data.values()) for year_data in yearly_weekly_data.values())
    total_hours = int(total_minutes / 3600)

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly Watering Summary by Year</title>
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
            max-height: 400px;
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
        <h1>Weekly Watering Summary by Year</h1>
        <div class="subtitle">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_controllers}</div>
                <div class="stat-label">Controllers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_years}</div>
                <div class="stat-label">Years of Data</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_hours:,}</div>
                <div class="stat-label">Total Hours</div>
            </div>
        </div>

        <div class="charts">
            {charts_html}
        </div>

        <footer>
            Weekly Watering Summary &copy; {datetime.now().year}
        </footer>
    </div>

    <script>
        {charts_js}
    </script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nWeekly dashboard generated: {output_path}")
    print(f"Open this file in your web browser to view the dashboard.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate weekly per-household dashboard with separate charts per year"
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
        default='data/weekly_dashboard.html',
        help='Output HTML file path (default: data/weekly_dashboard.html)'
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Load data
    print("Loading data...")
    events = []

    if args.source == 'sql':
        database_path = config.get('database_path', 'data/rachio_events.db')
        db = SQLStorage(database_path)
        events = db.get_events()
        print(f"Loaded {len(events)} events from database")

    else:  # csv
        csv_storage = CSVStorage()
        events = csv_storage.read_zone_events(args.csv_file)
        print(f"Loaded {len(events)} events from CSV")

    if not events:
        print("No events found. Please run 'python main.py' first to collect data.")
        return

    # Process events for weekly charts
    print("Processing weekly data...")
    chart_data = process_events_for_weekly_charts(events)

    # Generate HTML dashboard
    print("Generating weekly dashboard...")
    generate_weekly_html(chart_data, args.output)


if __name__ == '__main__':
    main()
