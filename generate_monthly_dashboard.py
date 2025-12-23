#!/usr/bin/env python3
"""
Generate a monthly summary dashboard with Chart.js visualizations from Rachio data.
"""
import json
import argparse
from datetime import datetime
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


def process_events_for_monthly_charts(events: List[Dict]) -> Dict:
    """
    Process events into monthly data structures suitable for Chart.js.
    Aggregates by controller and month.
    Anonymizes controller names using capital letters (A, B, C, etc.).

    Args:
        events: List of event dictionaries

    Returns:
        Dictionary containing processed monthly data for charts
    """
    # Create anonymization mapping
    anon_map, _ = anonymize_controllers(events)

    # Group by month and controller
    monthly_data_by_controller = defaultdict(lambda: defaultdict(int))
    overall_monthly_data = defaultdict(int)
    controller_totals = defaultdict(int)

    for event in events:
        controller = event.get('controller_name', 'Unknown')
        anon_controller = anon_map.get(controller, controller)
        duration = int(event.get('duration_seconds', 0))

        # Controller totals
        controller_totals[anon_controller] += duration

        # Monthly data
        if event.get('end_time'):
            date = datetime.fromtimestamp(int(event['end_time']) / 1000.0)
            # Create month key as "YYYY-MM"
            month_key = date.strftime('%Y-%m')
            monthly_data_by_controller[anon_controller][month_key] += duration
            overall_monthly_data[month_key] += duration

    # Sort monthly data by month
    sorted_overall_monthly = sorted(overall_monthly_data.items())

    return {
        'controller_totals': dict(controller_totals),
        'monthly_data_by_controller': dict(monthly_data_by_controller),
        'overall_monthly_data': sorted_overall_monthly,
        'anonymization_map': anon_map
    }


def generate_monthly_html(data: Dict, output_path: str = "data/monthly_dashboard.html"):
    """
    Generate HTML dashboard with monthly Chart.js visualizations.
    Shows controller-level aggregated monthly data.

    Args:
        data: Processed data dictionary
        output_path: Path to output HTML file
    """
    controller_totals = data['controller_totals']
    monthly_data_by_controller = data['monthly_data_by_controller']
    overall_monthly_data = data['overall_monthly_data']

    # Get all unique months across all controllers
    all_months = sorted(set(month for controller_months in monthly_data_by_controller.values() for month in controller_months.keys()))

    # Sort controllers by total time for consistent ordering
    sorted_controllers = sorted(controller_totals.items(), key=lambda x: x[1], reverse=True)
    controller_labels = [controller for controller, _ in sorted_controllers]

    # Overall monthly data
    monthly_labels = [month for month, _ in overall_monthly_data]
    monthly_values = [duration / 60 for _, duration in overall_monthly_data]  # Convert to minutes

    # Monthly data per controller (for stacked bar chart)
    monthly_datasets = []
    colors = [
        'rgba(102, 126, 234, 0.8)',
        'rgba(118, 75, 162, 0.8)',
        'rgba(237, 100, 166, 0.8)',
        'rgba(255, 154, 158, 0.8)',
        'rgba(250, 208, 196, 0.8)',
        'rgba(46, 213, 115, 0.8)',
        'rgba(0, 148, 255, 0.8)',
        'rgba(255, 71, 87, 0.8)',
        'rgba(255, 177, 66, 0.8)',
        'rgba(94, 84, 142, 0.8)',
        'rgba(153, 128, 250, 0.8)',
        'rgba(18, 203, 196, 0.8)',
        'rgba(253, 203, 110, 0.8)',
        'rgba(214, 48, 49, 0.8)',
        'rgba(9, 132, 227, 0.8)',
        'rgba(108, 92, 231, 0.8)',
        'rgba(255, 118, 117, 0.8)',
        'rgba(253, 121, 168, 0.8)',
        'rgba(99, 110, 114, 0.8)',
        'rgba(87, 101, 116, 0.8)'
    ]

    for i, controller in enumerate(controller_labels):
        # Get data for this controller across all months
        values = [monthly_data_by_controller[controller].get(month, 0) / 60 for month in all_months]
        monthly_datasets.append({
            'label': controller,
            'data': values,
            'backgroundColor': colors[i % len(colors)],
            'borderColor': colors[i % len(colors)].replace('0.8', '1'),
            'borderWidth': 1
        })

    # Calculate date range
    if all_months:
        start_month = all_months[0]
        end_month = all_months[-1]
        num_months = len(all_months)
    else:
        start_month = end_month = "N/A"
        num_months = 0

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monthly Watering Summary</title>
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

        @media (min-width: 768px) {{
            .charts {{
                grid-template-columns: 1fr;
            }}
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
        <h1>Monthly Watering Summary</h1>
        <div class="subtitle">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>
        <div class="subtitle">Data Range: {start_month} to {end_month}</div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(controller_totals)}</div>
                <div class="stat-label">Controllers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{num_months}</div>
                <div class="stat-label">Months of Data</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{int(sum(controller_totals.values()) / 60):,}</div>
                <div class="stat-label">Total Minutes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{int(sum(controller_totals.values()) / 3600):,}</div>
                <div class="stat-label">Total Hours</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <h2 class="chart-title">Overall Monthly Watering Time</h2>
                <canvas id="overallMonthlyChart"></canvas>
            </div>

            <div class="chart-container">
                <h2 class="chart-title">Monthly Watering by Controller (Stacked)</h2>
                <canvas id="monthlyByControllerChart"></canvas>
            </div>
        </div>

        <footer>
            Monthly Watering Summary &copy; {datetime.now().year}
        </footer>
    </div>

    <script>
        // Overall monthly chart (bar chart)
        const overallMonthlyCtx = document.getElementById('overallMonthlyChart').getContext('2d');
        new Chart(overallMonthlyCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(monthly_labels)},
                datasets: [{{
                    label: 'Total Watering Time (minutes)',
                    data: {json.dumps(monthly_values)},
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
                    }}
                }}
            }}
        }});

        // Monthly by controller chart (stacked bar chart)
        const monthlyByControllerCtx = document.getElementById('monthlyByControllerChart').getContext('2d');
        new Chart(monthlyByControllerCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(all_months)},
                datasets: {json.dumps(monthly_datasets)}
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
                        stacked: true
                    }},
                    y: {{
                        stacked: true,
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Minutes'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nMonthly dashboard generated: {output_path}")
    print(f"Open this file in your web browser to view the dashboard.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate monthly summary dashboard from Rachio watering data"
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
        default='data/monthly_dashboard.html',
        help='Output HTML file path (default: data/monthly_dashboard.html)'
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

    # Process events for monthly charts
    print("Processing monthly data...")
    chart_data = process_events_for_monthly_charts(events)

    # Generate HTML dashboard
    print("Generating monthly dashboard...")
    generate_monthly_html(chart_data, args.output)


if __name__ == '__main__':
    main()
