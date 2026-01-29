# What CMS

A Python CLI tool that scans websites (derived from email domains in a CSV) to detect if they use HubSpot CMS/marketing tools.

## Setup

1. **Create a local virtual environment**

   ```sh
   py -m venv ./venv
   ```

2. **Enable the Virtual Environment**

   On Windows:

   ```sh
   .\venv\Scripts\activate
   ```

   On macOS/Linux:

   ```sh
   source venv/bin/activate
   ```

3. **Install the requirements**

   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. **Prepare your input CSV file** with email addresses (must have an `email` column or emails in the first column)

2. **Run the scanner**

   ```sh
   python main.py input.csv output.csv
   ```

3. **Check the results** in the output CSV file

### Options

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Show detailed progress |
| `--all` | Include all domains in output (not just HubSpot ones) |
| `--delay SECONDS` | Delay between requests (default: 1.0) |
| `--timeout SECONDS` | Request timeout (default: 10) |

### Examples

```sh
# Basic usage
python main.py emails.csv hubspot_results.csv

# Verbose output with all domains
python main.py emails.csv results.csv --verbose --all

# Custom delay and timeout
python main.py emails.csv results.csv --delay 2.0 --timeout 15
```

### Output Format

The output CSV contains the following columns:
- `domain` - The domain scanned
- `has_hubspot` - Whether HubSpot was detected (True/False)
- `url` - The final URL after redirects
- `error` - Any error encountered during scanning

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
