# Rachio Data Fetch

Automatically collect and store station run time data from Rachio water controllers using the Rachio API.

## Features

- Fetch zone/station run time data from multiple Rachio controllers
- Store data in CSV format for easy analysis
- Support for incremental data collection (only fetch new data)
- Configurable time ranges for historical data retrieval
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

**Note:** To find your `device_id`, you can use the Rachio API or check the device settings in the mobile app.

## Usage

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

Data is saved to CSV files in the `data/` directory (configurable in `config.json`).

CSV files include the following columns:
- `event_id`: Unique identifier for the event
- `event_type`: Type of event (STARTED, COMPLETED, STOPPED)
- `device_id`: Controller device ID
- `zone_id`: Unique zone identifier
- `zone_number`: Zone number (1, 2, 3, etc.)
- `zone_name`: Name of the zone (e.g., "Front Lawn")
- `duration_seconds`: How long the zone ran in seconds
- `start_time`: When the zone started (Unix timestamp in milliseconds)
- `end_time`: When the zone ended (Unix timestamp in milliseconds)
- `event_date`: Event timestamp
- `create_date`: When the event was created
- `flow_volume_gallons`: Water volume in gallons (if flow meter is configured)

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

- Automatic upload to web-hosted SQL database
- Real-time data collection using webhooks
- Data visualization and reporting
- Support for flow meter data analysis
- Water usage analytics

## Project Structure

```
rachio-data-fetch/
├── main.py                  # Main script
├── config.json              # Your configuration (not in git)
├── config.json.example      # Configuration template
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── data/                   # Output CSV files (not in git)
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
Verify that your `device_id` is correct.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

MIT License

## Acknowledgments

- Rachio API documentation: https://rachio.readme.io/
- Data is collected using the official Rachio Public API