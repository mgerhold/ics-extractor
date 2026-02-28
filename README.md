# ICS Extractor

Extract therapy appointments from PDF files and generate ICS calendar files with optional Google Calendar upload.

## Features

- Extract appointment data from PDF files
- Parse date, time, therapy kind, and therapist name
- Generate ICS calendar files
- Optional upload to Google Calendar via OAuth 2.0

## Installation

```bash
uv sync
```

## Usage

1. Place your PDF files in the `input/` directory
2. Run the program:

```bash
uv run main.py
```

3. ICS files will be generated in the `output/` directory

## Configuration

The `config.json` file will be automatically created on first run with default values:

```json
{
    "therapy_practice_address": [
        "Therapiezentrum am Stadtpark",
        "Stadtpark 1",
        "12345 Musterstadt"
    ],
    "therapy_kind_mapping": {
        "KG ZNS": "Krankengymnastik",
        "O60": "Osteopathie"
    },
    "appointment_duration_minutes": 30,
    "enable_google_calendar_upload": false,
    "google_calendar_id": "primary"
}
```

### Configuration Options

- **therapy_practice_address**: Address lines for the therapy practice (used as location in calendar events)
- **therapy_kind_mapping**: Map therapy codes to display names
- **appointment_duration_minutes**: Duration of each appointment (default: 30)
- **enable_google_calendar_upload**: Enable/disable Google Calendar upload (default: false)
- **google_calendar_id**: Which calendar to upload to (default: "primary")

## Google Calendar Integration

To upload appointments to Google Calendar:

### 1. Set up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Calendar API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (app name, user support email, developer email)
   - Add scope: `https://www.googleapis.com/auth/calendar.events`
   - Add yourself as a test user
4. Select "Desktop app" as application type
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in the project root directory

### 3. Enable Upload in Config

Edit `config.json` and set:

```json
{
    "enable_google_calendar_upload": true
}
```

### 4. First Run - OAuth Flow

On first run with Google Calendar upload enabled:

1. The program will open a browser window
2. Sign in with your Google account
3. Grant permission to access your calendar
4. The authorization token will be saved to `token.json`

Subsequent runs will use the saved token (it will be automatically refreshed when needed).

### Notes

- The `token.json` file is automatically created and should not be committed to git
- The `credentials.json` file contains your OAuth client credentials and should not be shared
- Both files are in `.gitignore` by default
- Events are checked for duplicates before upload (based on summary and start time)

## Testing

```bash
uv run pytest test.py
```

## Development

The project uses:
- **pypdf**: PDF text extraction
- **icalendar**: ICS file generation
- **pydantic**: Configuration management
- **google-api-python-client**: Google Calendar API
- **google-auth-oauthlib**: OAuth 2.0 authentication
