# Get Device Info Utility

This utility script helps you retrieve your Rachio device IDs and information needed for the `config.json` file.

## Purpose

The `get_device_info.py` script queries the Rachio API to:
1. Retrieve your person/account ID
2. Fetch all devices (controllers) associated with your account
3. Display device details including zones
4. Generate a sample `config.json` template

## Requirements

- Python 3.7 or higher
- `requests` library (install via `pip install requests`)
- Valid Rachio API key

## How to Get Your Rachio API Key

1. Open the Rachio mobile app on your phone
2. Tap the "Profile" icon (bottom right)
3. Scroll down and tap "API Key"
4. Tap "Copy" to copy your API key to clipboard

## Usage

### Option 1: Pass API key as command-line argument

```bash
python3 get_device_info.py YOUR_API_KEY_HERE
```

### Option 2: Interactive mode

```bash
python3 get_device_info.py
```

The script will prompt you to enter your API key.

## How It Works

The script performs a two-step process:

1. **Step 1: Get Person ID**
   - Calls `/public/person/info` endpoint with your API key
   - Retrieves your unique person/account ID

2. **Step 2: Get Device Information**
   - Calls `/public/person/{person_id}` endpoint
   - Retrieves complete account information including all devices, zones, and schedules

## Output

The script displays:

- **User Information**: Full name and email
- **Device Count**: Number of controllers found
- **Device Details** for each controller:
  - Device name
  - Device ID (needed for config.json)
  - Model number
  - Serial number
  - Status (ONLINE/OFFLINE)
  - Time zone
- **Zone Information** for each device:
  - Zone number
  - Zone name
  - Status (enabled/disabled)
- **Sample config.json**: Ready-to-use configuration template

## Example Output

```
============================================================
Rachio Device Information Utility
============================================================

Step 1: Fetching person ID...

Person ID: 75b25756-0de9-4d5c-a161-b0bd34ecf8c4

Step 2: Fetching device information...

User: Adrian Jensen
Email: adrianjamesjensen@gmail.com

Found 1 device(s):
============================================================

Device 1:
  Name: Rachio-FE38D6
  Device ID: 799e0755-474e-4f68-b0aa-e482a7b7044a
  Model: GENERATION3_8ZONE_USI
  Serial Number: FF7888793
  Status: ONLINE
  Time Zone: America/Chicago
  Zones (8):
    Zone 1: front (enabled)
    Zone 2: Zone 2 (enabled)
    Zone 3: grass (enabled)
    Zone 4: Zone 4 (disabled)
    Zone 5: Zone 5 (disabled)
    Zone 6: Zone 6 (disabled)
    Zone 7: Zone 7 (disabled)
    Zone 8: Zone 8 (disabled)

============================================================
Sample config.json entry:
============================================================

{
  "controllers": [
    {
      "name": "Rachio-FE38D6",
      "device_id": "799e0755-474e-4f68-b0aa-e482a7b7044a",
      "api_key": "YOUR_API_KEY_HERE"
    }
  ],
  "output_directory": "data",
  "base_url": "https://api.rach.io/1"
}
```

## Next Steps

1. Copy the device ID from the output
2. Create your `config.json` file:
   ```bash
   cp config.json.example config.json
   ```
3. Edit `config.json` and add your device ID and API key
4. Run the main data collection script:
   ```bash
   python3 main.py
   ```

## Troubleshooting

### "Failed to retrieve person ID"
- Verify your API key is correct
- Check that you copied the entire API key without extra spaces
- Regenerate your API key in the Rachio mobile app if needed

### "No devices found in your account"
- Ensure you have at least one Rachio controller set up in your account
- Verify the controller is connected and appears in the Rachio mobile app
- Try logging out and back into the mobile app

### "Permission denied" error
- This usually means the API key is invalid or expired
- Generate a new API key from the mobile app

## API Endpoints Used

1. `GET https://api.rach.io/1/public/person/info`
   - Returns: Person ID
   - Used to identify the authenticated user

2. `GET https://api.rach.io/1/public/person/{person_id}`
   - Returns: Complete account information including devices
   - Requires: Valid person ID from step 1

## Notes

- The script does not modify any data; it only retrieves information
- Your API key is not stored anywhere; it's only used for the API request
- All device and zone information is read-only
