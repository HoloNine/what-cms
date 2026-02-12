#!/usr/bin/env python3
"""
What CMS - HubSpot Detector (Streamlit Web App)
Scans websites from email domains to detect HubSpot usage.
"""

import streamlit as st
import csv
import io
import time
import random
import pandas as pd
from curl_cffi import requests


# Browser impersonation options for curl_cffi
BROWSER_IMPERSONATES = [
    "chrome131",
    "chrome124",
    "chrome123",
    "safari184",
    "safari180",
]


def extract_domain_from_email(email: str) -> str | None:
    """Extract domain from an email address."""
    email = email.strip()
    if '@' in email:
        return email.split('@')[-1].lower()
    return None


def check_hubspot(domain: str, timeout: int = 10) -> tuple[str, str]:
    """
    Check if a domain's homepage contains HubSpot references.
    Returns (scanned_url, hubspot_status).
    """
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
            response = requests.get(
                url,
                timeout=timeout,
                impersonate=impersonate,
                allow_redirects=True
            )

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
            break  # Skip remaining URLs after timeout
        except requests.exceptions.RequestException as e:
            last_error = str(e)[:50]
            continue

    return '', f'Error: {last_error or "Unknown"}'


def process_csv(uploaded_file, timeout: int, delay: float, include_all: bool):
    """Process the uploaded CSV file and scan domains."""
    
    # Read CSV
    content = uploaded_file.getvalue().decode('utf-8')
    csv_reader = csv.reader(io.StringIO(content))
    header = next(csv_reader, None)
    
    if not header:
        st.error("Empty or invalid CSV file")
        return None, None
    
    rows = list(csv_reader)
    
    # Find email column
    email_col = 0
    header_lower = [h.lower().strip() for h in header]
    if 'email' in header_lower:
        email_col = header_lower.index('email')
    elif 'e-mail' in header_lower:
        email_col = header_lower.index('e-mail')
    elif 'mail' in header_lower:
        email_col = header_lower.index('mail')
    
    # Extract unique domains
    domains_to_scan = set()
    for row in rows:
        if len(row) > email_col:
            domain = extract_domain_from_email(row[email_col])
            if domain:
                domains_to_scan.add(domain)
    
    domains_to_scan = sorted(domains_to_scan)
    
    # Create containers for dynamic updates
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.empty()
    
    # Scan domains
    domain_results = {}
    hubspot_count = 0
    
    for i, domain in enumerate(domains_to_scan, 1):
        status_text.text(f"Scanning {i}/{len(domains_to_scan)}: {domain}...")
        
        scanned_url, hubspot_status = check_hubspot(domain, timeout=timeout)
        domain_results[domain] = (scanned_url, hubspot_status)
        
        if hubspot_status == 'Yes':
            hubspot_count += 1
        
        # Update progress
        progress_bar.progress(i / len(domains_to_scan))
        
        # Show interim results
        results_list = []
        for d, (url, status) in domain_results.items():
            results_list.append({'Domain': d, 'URL': url, 'HubSpot': status})
        results_container.dataframe(pd.DataFrame(results_list), use_container_width=True)
        
        if i < len(domains_to_scan):
            time.sleep(delay)
    
    status_text.success(f"✅ Scan complete! Found HubSpot on {hubspot_count}/{len(domains_to_scan)} domains")
    
    # Build output CSV
    output_header = header + ['scanned_url', 'hubspot_status']
    output_rows = []
    
    for row in rows:
        if len(row) > email_col:
            domain = extract_domain_from_email(row[email_col])
            if domain and domain in domain_results:
                scanned_url, hubspot_status = domain_results[domain]
                
                if not include_all and hubspot_status != 'Yes':
                    continue
                
                output_rows.append(row + [scanned_url, hubspot_status])
            elif include_all:
                output_rows.append(row + ['', ''])
    
    # Create CSV for download
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(output_header)
    writer.writerows(output_rows)
    
    return output.getvalue(), domain_results


# Streamlit UI
st.set_page_config(page_title="HubSpot Detector", page_icon="🔍", layout="wide")

st.title("🔍 HubSpot CMS Detector")
st.markdown("Upload a CSV file with email addresses to scan domains for HubSpot usage.")

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    timeout = st.slider("Request timeout (seconds)", 3, 15, 5)
    delay = st.slider("Delay between requests (seconds)", 0.5, 5.0, 1.0, 0.5)
    include_all = st.checkbox("Include all rows in output", value=True, 
                              help="If unchecked, only rows with HubSpot detected will be in the output")
    
    st.markdown("---")
    st.markdown("""
    ### How it works
    1. Upload CSV with email addresses
    2. Domains are extracted from emails
    3. Each domain is scanned for HubSpot
    4. Download results as CSV
    
    ### Detection
    Scans for HubSpot patterns:
    - hubspot references
    - hs-scripts.com
    - js.hsforms.net
    - hbspt.forms/cta
    """)

# File upload
uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

if uploaded_file is not None:
    # Show preview
    df_preview = pd.read_csv(uploaded_file, nrows=5)
    st.subheader("📄 File Preview (first 5 rows)")
    st.dataframe(df_preview, use_container_width=True)
    uploaded_file.seek(0)  # Reset file pointer
    
    # Start scan button
    if st.button("🚀 Start Scanning", type="primary"):
        with st.spinner("Scanning domains..."):
            csv_output, results = process_csv(uploaded_file, timeout, delay, include_all)
            
            if csv_output:
                # Download button
                st.download_button(
                    label="📥 Download Results CSV",
                    data=csv_output,
                    file_name="hubspot_scan_results.csv",
                    mime="text/csv",
                    type="primary"
                )
else:
    st.info("👆 Upload a CSV file to get started")
    
    # Show example
    with st.expander("📋 See example CSV format"):
        st.markdown("""
        Your CSV should have an email column. Example:
        
        ```csv
        name,email,company
        John Doe,john@example.com,Example Corp
        Jane Smith,jane@acme.org,ACME Inc
        ```
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Built with Streamlit • Powered by curl_cffi</p>
    </div>
    """,
    unsafe_allow_html=True
)
