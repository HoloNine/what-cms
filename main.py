#!/usr/bin/env python3
"""
What CMS - HubSpot Detector
Scans websites from email domains to detect HubSpot usage.
"""

import csv
import argparse
import time
import random
from curl_cffi import requests


def extract_domain_from_email(email: str) -> str | None:
    """Extract domain from an email address."""
    email = email.strip()
    if '@' in email:
        return email.split('@')[-1].lower()
    return None


def read_csv_with_rows(filepath: str) -> tuple[list[str], list[list[str]], int]:
    """
    Read CSV file preserving all columns.
    Returns (header, rows, email_col_index).
    """
    rows = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)

        if not header:
            return [], [], 0

        # Find email column index
        email_col = 0
        header_lower = [h.lower().strip() for h in header]
        if 'email' in header_lower:
            email_col = header_lower.index('email')
        elif 'e-mail' in header_lower:
            email_col = header_lower.index('e-mail')
        elif 'mail' in header_lower:
            email_col = header_lower.index('mail')

        for row in reader:
            if row:
                rows.append(row)

    return header, rows, email_col


# Browser impersonation options for curl_cffi
BROWSER_IMPERSONATES = [
    "chrome131",
    "chrome124",
    "chrome123",
    "safari184",
    "safari180",
]


def check_hubspot(domain: str, timeout: int = 10, verbose: bool = False) -> tuple[str, str]:
    """
    Check if a domain's homepage contains HubSpot references.
    Returns (scanned_url, hubspot_status).
    """
    # Try HTTPS first, then HTTP, also try with www prefix
    urls_to_try = [
        f'https://{domain}',
        f'https://www.{domain}',
        f'http://{domain}',
        f'http://www.{domain}'
    ]

    last_error = None
    impersonate = random.choice(BROWSER_IMPERSONATES)

    for url in urls_to_try:
        try:
            if verbose:
                print(f"  Checking {url} (as {impersonate})...")

            response = requests.get(
                url,
                timeout=timeout,
                impersonate=impersonate,
                allow_redirects=True
            )

            # For 403, try next URL variant
            if response.status_code == 403:
                last_error = '403 Forbidden'
                continue

            response.raise_for_status()

            html = response.text.lower()
            scanned_url = response.url

            # Check for HubSpot indicators
            hubspot_patterns = [
                'hubspot',
                'hs-scripts.com',
                'js.hs-scripts.com',
                'js.hsforms.net',
                'hbspt.forms',
                'hbspt.cta'
            ]

            for pattern in hubspot_patterns:
                if pattern in html:
                    return scanned_url, 'Yes'

            return scanned_url, 'No'

        except requests.exceptions.SSLError:
            last_error = 'SSL Error'
            continue
        except requests.exceptions.ConnectionError:
            last_error = 'Connection Error'
            continue
        except requests.exceptions.Timeout:
            last_error = 'Timeout'
            continue
        except requests.exceptions.RequestException as e:
            last_error = str(e)[:50]
            continue

    return '', f'Error: {last_error or "Unknown"}'


def main():
    parser = argparse.ArgumentParser(
        description='Scan email domains for HubSpot usage'
    )
    parser.add_argument('input_csv', help='Input CSV file with email addresses')
    parser.add_argument('output_csv', help='Output CSV file for results')
    parser.add_argument('--all', action='store_true',
                        help='Include all rows in output (not just HubSpot ones)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed progress')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--timeout', type=int, default=10,
                        help='Request timeout in seconds (default: 10)')

    args = parser.parse_args()

    print(f"Reading CSV from {args.input_csv}...")
    header, rows, email_col = read_csv_with_rows(args.input_csv)

    if not header:
        print("Error: Empty or invalid CSV file")
        return

    print(f"Found {len(rows)} rows")

    # Build domain -> scan result cache (to avoid scanning same domain multiple times)
    domain_results: dict[str, tuple[str, str]] = {}
    domains_to_scan = set()

    for row in rows:
        if len(row) > email_col:
            domain = extract_domain_from_email(row[email_col])
            if domain:
                domains_to_scan.add(domain)

    domains_to_scan = sorted(domains_to_scan)
    print(f"Scanning {len(domains_to_scan)} unique domains...")

    hubspot_count = 0
    try:
        for i, domain in enumerate(domains_to_scan, 1):
            print(f"[{i}/{len(domains_to_scan)}] Scanning {domain}...", end=' ')

            scanned_url, hubspot_status = check_hubspot(domain, timeout=args.timeout, verbose=args.verbose)
            domain_results[domain] = (scanned_url, hubspot_status)

            if hubspot_status == 'Yes':
                hubspot_count += 1
                print("✓ HubSpot detected")
            elif hubspot_status.startswith('Error'):
                print(f"✗ {hubspot_status}")
            else:
                print("- No HubSpot")

            if i < len(domains_to_scan):
                time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\n\n⚠ Scan interrupted by user. Saving partial results...")

    # Write output with all original columns plus the two new ones
    print(f"\nWriting results to {args.output_csv}...")
    output_header = header + ['scanned_url', 'hubspot_status']

    with open(args.output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(output_header)

        for row in rows:
            if len(row) > email_col:
                domain = extract_domain_from_email(row[email_col])
                if domain and domain in domain_results:
                    scanned_url, hubspot_status = domain_results[domain]

                    # Filter if --all not specified
                    if not args.all and hubspot_status != 'Yes':
                        continue

                    writer.writerow(row + [scanned_url, hubspot_status])
                elif args.all:
                    # No valid domain extracted, include row with empty values if --all
                    writer.writerow(row + ['', ''])

    scanned_count = len(domain_results)
    print(f"\nDone! Scanned {scanned_count}/{len(domains_to_scan)} domains, found HubSpot on {hubspot_count}")
    if not args.all:
        print("Output contains only rows with HubSpot detected")


if __name__ == '__main__':
    main()
