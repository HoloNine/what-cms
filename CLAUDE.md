# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**what-cms** is a Python CLI tool that scans websites (derived from email domains in a CSV) to detect if they use HubSpot CMS/marketing tools.

## How It Works

1. Read a CSV file containing email addresses
2. Extract the domain from each email (e.g., `user@example.com` → `example.com`)
3. Fetch the homepage HTML for each domain
4. Check if the page source contains "hubspot" (case-insensitive)
5. Output a new CSV with domains that have HubSpot detected

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scanner
python main.py input.csv output.csv

# Run with verbose output
python main.py input.csv output.csv --verbose

# Include all domains in output (not just HubSpot ones)
python main.py input.csv output.csv --all

# Custom delay and timeout
python main.py input.csv output.csv --delay 2.0 --timeout 15
```

## Architecture

- `main.py` - Main entry point and CLI interface
- Uses `requests` for HTTP fetching with appropriate timeout and error handling
- Uses `csv` module for reading/writing CSV files
- Domains are deduplicated before scanning to avoid redundant requests

## Input/Output Format

**Input CSV:** Must have an `email` column (or first column if no header)

**Output CSV:** Contains columns: `domain`, `has_hubspot`, `url`, `error`

## Key Considerations

- Handle HTTP errors gracefully (timeouts, SSL errors, unreachable domains)
- Rate limiting: add delay between requests to avoid being blocked
- Check both HTTP and HTTPS versions of domains
- Search for "hubspot" case-insensitively in the HTML source
