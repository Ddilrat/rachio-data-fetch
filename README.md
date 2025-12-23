# Rachio Data Fetch

Automatically collect and store station run time data from Rachio water controllers using the Rachio API.

## Features

- Fetch zone/station run time data from multiple Rachio controllers
- Store event data in CSV format for easy analysis
- Fetch and store comprehensive device information in JSON format
- Support for incremental data collection (only fetch new data)
- Configurable time ranges for historical data retrieval
- Automatic request chunking to handle API time range limits
- Duplicate event detection and prevention
- Device discovery utility to find controller IDs
- Designed for easy migration to SQL database in the future

## Prerequisites

- Python 3.7 or higher
- Rachio account with one or more controllers
- API key(s) from the Rachio mobile app

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd rachio-data-fetch
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Create your configuration file:
```bash
cp config.json.example config.json
```

4. Edit `config.json` and add your Rachio API credentials

## Getting Your Rachio API Key

1. Open the Rachio mobile app on your phone
2. Tap the "Profile" icon (bottom right)
3. Scroll down and tap "API Key"
4. Tap "Copy" to copy your API key to clipboard

## Configuration

Edit `config.json` with your controller information:

```json
{
  "controllers": [
    {
      "name": "Front Yard Controller",
      "device_id": "your-device-id-here",
      "api_key": "your-api-key-here"
    }
  ],
  "output_directory": "data",
  "base_url": "https://api.rach.io/1"
}
```

### Finding Your Device ID

To find your `device_id`, use the included utility script:

```bash
python3 get_device_info.py
```

This will prompt you for your API key and display all your devices with their IDs, names, models, and zone information.

## Usage

### Fetch Device Information

Fetch detailed device information for all configured controllers and save to JSON:

```bash
python fetch_devices.py
```

This will create a `data/devices.json` file containing comprehensive information about each controller including:
- Device ID, name, model, and status
- Zone configuration and details
- Scheduling information
- Hardware specifications
- Location and timezone data

### Basic Usage

Fetch the last 7 days of zone run data for all configured controllers:

```bash
python main.py
```

### Custom Time Range

Fetch data for a specific number of days:

```bash
python main.py --days 30
```

**Note:** The Rachio API has a 35-day maximum time range limit per request. The script automatically chunks larger requests into multiple API calls, so you can safely request any time range (e.g., `--days 365`).

### Incremental Updates

Fetch only new data since the last run (appends to existing CSV):

```bash
python main.py --incremental
```

### Custom Configuration File

Use a different configuration file:

```bash
python main.py --config /path/to/config.json
```

### Combine Options

```bash
python main.py --days 14 --incremental
```

## Output

### Event Data (CSV)

All event data from all controllers is saved to a **single CSV file**: `data/events.csv` (directory configurable in `config.json`).

This single-file approach makes it easy to:
- Query across all controllers and zones
- Import into databases (single table)
- Analyze watering patterns across your entire system
- No file size concerns (CSV files can handle millions of rows)

#### CSV Columns

- `controller_name`: Name of the controller (from config.json)
- `device_id`: Controller device ID
- `zone_name`: Name of the zone (e.g., "Front Lawn", "Zone 2")
- `duration_seconds`: How long the zone ran in seconds
- `end_time`: When the zone ended (Unix timestamp in milliseconds)
- `end_time_datetime`: Human-readable end time (YYYY-MM-DD HH:MM:SS)
- `csv_written_datetime`: When this data was written to CSV (YYYY-MM-DD HH:MM:SS)
- `topic`: Event topic category (e.g., "WATERING")
- `summary`: Human-readable event summary from API
- `event_id`: Unique identifier for the event

### Device Information (JSON)

Device information is saved to `data/devices.json` with the following structure:

```json
{
  "metadata": {
    "total_devices": 15,
    "generated_at": "2025-12-17T23:52:01.392142",
    "description": "Device information from Rachio API for all configured controllers"
  },
  "devices": [
    {
      "id": "device-id-here",
      "name": "Controller Name",
      "model": "GENERATION3_8ZONE",
      "status": "ONLINE",
      "zones": [...],
      "schedules": [...],
      "config_name": "Name from config.json",
      "fetched_at": "2025-12-17T23:52:01.392142"
    }
  ]
}
```

Each device includes comprehensive information such as:
- Device metadata (ID, name, model, serial number, status)
- All zone configurations with detailed settings
- Schedule information
- Location and timezone data
- Hardware and firmware details

## Scheduling Automatic Data Collection

### Using Cron (Linux/Mac)

Add to your crontab to run daily at 2 AM:

```bash
crontab -e
```

Add this line:
```
0 2 * * * cd /path/to/rachio-data-fetch && python main.py --incremental
```

### Using Task Scheduler (Windows)

Create a scheduled task to run `python main.py --incremental` daily.

## API Rate Limits

The Rachio API allows a maximum of **3,500 requests per day** across all endpoints. This script is designed to minimize API calls, but be mindful when fetching large time ranges or running frequently.

## Future Enhancements

- Automatic upload to web-hosted SQL database (single table design ready)
- Real-time data collection using webhooks
- Data visualization and reporting
- Support for flow meter data analysis
- Water usage analytics
- Automated anomaly detection (e.g., leaks, unusual watering patterns)

## Project Structure

```
rachio-data-fetch/
├── main.py                  # Main script for fetching zone run events
├── fetch_devices.py         # Script to fetch all device information to JSON
├── get_device_info.py       # Device discovery utility
├── config.json              # Your configuration (not in git)
├── config.json.example      # Configuration template
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── data/                   # Output files (not in git)
│   ├── events.csv          # All controller events (single file)
│   └── devices.json        # All device information
└── src/
    ├── __init__.py
    ├── rachio_client.py    # Rachio API client
    └── csv_storage.py      # CSV storage handler
```

## Troubleshooting

### "Configuration file not found"
Make sure you've copied `config.json.example` to `config.json` and added your API keys.

### "Authentication failed" or 401 errors
Verify that your API key is correct. You can regenerate it in the Rachio mobile app.

### "Device not found" or 404 errors
Verify that your `device_id` is correct. Use `python3 get_device_info.py` to find the correct device ID.

### HTTP 400 errors with large time ranges
The script automatically handles this by chunking requests into 35-day segments. If you still see errors, try a smaller time range.

### Zone names appear as "Zone 1", "Zone 2", etc.
The API event data only provides zone names as they were at the time of the event. If you renamed a zone, historical events will show the old name. The zone_name field reflects what the Rachio API returns in the event summary.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License

## Acknowledgments

- Rachio API documentation: https://rachio.readme.io/
- Data is collected using the official Rachio Public API