#!/usr/bin/env python3
"""
What CMS - HubSpot Detector
Scans websites from email domains to detect HubSpot usage.
"""

import csv
import argparse
import time
import random
import requests
from urllib.parse import urlparse


def extract_domain_from_email(email: str) -> str | None:
    """Extract domain from an email address."""
    email = email.strip()
    if '@' in email:
        return email.split('@')[-1].lower()
    return None


def read_emails_from_csv(filepath: str) -> list[str]:
    """Read email addresses from a CSV file."""
    emails = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)

        # Find email column index
        email_col = 0
        if header:
            header_lower = [h.lower().strip() for h in header]
            if 'email' in header_lower:
                email_col = header_lower.index('email')
            elif 'e-mail' in header_lower:
                email_col = header_lower.index('e-mail')
            elif 'mail' in header_lower:
                email_col = header_lower.index('mail')
            else:
                # First row might be data, not header
                if header and '@' in header[0]:
                    emails.append(header[0])

        for row in reader:
            if row and len(row) > email_col:
                emails.append(row[email_col])

    return emails


def get_unique_domains(emails: list[str]) -> list[str]:
    """Extract unique domains from email list."""
    domains = set()
    for email in emails:
        domain = extract_domain_from_email(email)
        if domain:
            domains.add(domain)
    return sorted(domains)


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def get_headers() -> dict:
    """Get realistic browser headers to avoid 403 errors."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }


def check_hubspot(domain: str, timeout: int = 10, verbose: bool = False) -> dict:
    """
    Check if a domain's homepage contains HubSpot references.
    Returns dict with domain, has_hubspot, url, and error info.
    """
    result = {
        'domain': domain,
        'has_hubspot': False,
        'url': '',
        'error': ''
    }

    # Try HTTPS first, then HTTP, also try with www prefix
    urls_to_try = [
        f'https://{domain}',
        f'https://www.{domain}',
        f'http://{domain}',
        f'http://www.{domain}'
    ]

    session = requests.Session()
    last_error = None

    for url in urls_to_try:
        try:
            if verbose:
                print(f"  Checking {url}...")

            response = session.get(
                url,
                timeout=timeout,
                headers=get_headers(),
                allow_redirects=True
            )

            # For 403, try next URL variant
            if response.status_code == 403:
                last_error = '403 Forbidden'
                continue

            response.raise_for_status()

            html = response.text.lower()
            result['url'] = response.url

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
                    result['has_hubspot'] = True
                    break

            return result

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

    result['error'] = last_error or 'Unknown Error'
    return result


def write_results_csv(results: list[dict], filepath: str, hubspot_only: bool = True):
    """Write results to CSV file."""
    if hubspot_only:
        results = [r for r in results if r['has_hubspot']]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['domain', 'has_hubspot', 'url', 'error'])
        writer.writeheader()
        writer.writerows(results)


def main():
    parser = argparse.ArgumentParser(
        description='Scan email domains for HubSpot usage'
    )
    parser.add_argument('input_csv', help='Input CSV file with email addresses')
    parser.add_argument('output_csv', help='Output CSV file for results')
    parser.add_argument('--all', action='store_true',
                        help='Include all domains in output (not just HubSpot ones)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed progress')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--timeout', type=int, default=10,
                        help='Request timeout in seconds (default: 10)')

    args = parser.parse_args()

    print(f"Reading emails from {args.input_csv}...")
    emails = read_emails_from_csv(args.input_csv)
    print(f"Found {len(emails)} email addresses")

    domains = get_unique_domains(emails)
    print(f"Extracted {len(domains)} unique domains")

    results = []
    hubspot_count = 0

    for i, domain in enumerate(domains, 1):
        print(f"[{i}/{len(domains)}] Scanning {domain}...", end=' ')

        result = check_hubspot(domain, timeout=args.timeout, verbose=args.verbose)
        results.append(result)

        if result['has_hubspot']:
            hubspot_count += 1
            print("✓ HubSpot detected")
        elif result['error']:
            print(f"✗ Error: {result['error']}")
        else:
            print("- No HubSpot")

        if i < len(domains):
            time.sleep(args.delay)

    print(f"\nWriting results to {args.output_csv}...")
    write_results_csv(results, args.output_csv, hubspot_only=not args.all)

    print(f"\nDone! Found HubSpot on {hubspot_count}/{len(domains)} domains")
    if not args.all:
        print(f"Output contains only domains with HubSpot detected")


if __name__ == '__main__':
    main()
