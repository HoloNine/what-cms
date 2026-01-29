# 🔍 HubSpot CMS Detector

A web application that scans website domains (extracted from email addresses) to detect HubSpot CMS usage.

## Features

- 🌐 **Web Interface** - Easy-to-use Streamlit web app
- 📊 **Real-time Progress** - Watch the scan progress live
- 🎯 **Accurate Detection** - Scans for multiple HubSpot indicators
- 📥 **CSV Export** - Download results as CSV
- 🔒 **Browser Impersonation** - Uses curl_cffi to avoid blocks
- ⚡ **Fast Scanning** - Configurable timeout and delays

## Usage

### Web App (Streamlit)

```bash
streamlit run app.py
```

Then upload your CSV file with email addresses and click "Start Scanning".

### Command Line

```bash
python3 main.py emails.csv output.csv [--all] [--verbose] [--delay 1.0] [--timeout 10]
```

Options:

- `--all`: Include all rows in output (not just HubSpot ones)
- `--verbose`, `-v`: Show detailed progress
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--timeout`: Request timeout in seconds (default: 10)

## Installation

```bash
pip install -r requirements.txt
```

## CSV Format

Your input CSV should have an email column. Example:

```csv
name,email,company
John Doe,john@example.com,Example Corp
Jane Smith,jane@acme.org,ACME Inc
```

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file path to `app.py`
5. Deploy!

## Detection Methods

The scanner looks for these HubSpot indicators:

- "hubspot" text references
- `hs-scripts.com` domain
- `js.hs-scripts.com` scripts
- `js.hsforms.net` forms
- `hbspt.forms` JavaScript
- `hbspt.cta` JavaScript

## Requirements

- Python 3.9+
- curl_cffi >= 0.14.0
- streamlit >= 1.28.0
- pandas >= 2.0.0

## License

MIT
