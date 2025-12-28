"""
HKEX Debenture Holdings Monitoring Script

This script monitors debenture holdings by substantial shareholders, directors, and chief executives
from the HKEX Disclosure of Interests (DI) website. It sends an email alert if any changes are detected.

Dependencies:
- Python 3
- Playwright
- pandas
- datetime
- smtplib
- email.message

Setup Instructions:
1. Install required packages:
   pip install playwright pandas
   playwright install

2. Schedule daily execution using Task Scheduler (Windows) or cron (Linux/Mac).

3. Update the email configuration section with your SMTP server details.
"""

import os
import json
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
from email.message import EmailMessage
import smtplib

# Constants
STOCK_CODE = "488"
COMPANY_NAME = "Lai Sun Development"
BASE_URL = "https://di.hkex.com.hk/di/NSSrchCorp.aspx?src=MAIN&lang=EN&g_lang=en"
DATA_DIR = "data/488HK"
EMAIL_SENDER = "vincentsnews@gmail.com"
EMAIL_RECEIVER = "vincewong99@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_PASSWORD = os.getenv("HKEX_EMAIL_PASS")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_disclosures():
    """Fetch disclosures from the HKEX DI website."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(BASE_URL)

        # Fill in search form
        page.fill("#txtStockCode", STOCK_CODE)
        page.fill("#txtDateFrom", "2025-01-01")
        page.fill("#txtDateTo", datetime.now().strftime("%Y-%m-%d"))
        page.click("#btnSearch")

        # Wait for results table
        page.wait_for_selector("#tblList")

        # Extract main table
        rows = page.query_selector_all("#tblList tr")
        data = []
        for row in rows[1:]:  # Skip header row
            cells = row.query_selector_all("td")
            data.append({
                "Name": cells[0].inner_text().strip(),
                "Capacity": cells[1].inner_text().strip(),
                "Nature of Interest": cells[2].inner_text().strip(),
                "Number of Debentures": cells[3].inner_text().strip(),
                "Interest in Debentures": cells[4].inner_text().strip(),
                "Date of Notice": cells[5].inner_text().strip(),
            })

        main_table = pd.DataFrame(data)

        # Extract debenture detail tables
        debenture_details = []
        for i, row in enumerate(data):
            if row["Interest in Debentures"].lower() == "yes":
                page.click(f"#tblList tr:nth-child({i + 2}) a")  # Click disclosure link
                page.wait_for_selector("#tblDebenture")

                detail_rows = page.query_selector_all("#tblDebenture tr")
                detail_data = []
                for detail_row in detail_rows[1:]:  # Skip header row
                    detail_cells = detail_row.query_selector_all("td")
                    detail_data.append([cell.inner_text().strip() for cell in detail_cells])

                debenture_details.append({
                    "Person": row["Name"],
                    "Stock Code": STOCK_CODE,
                    "Disclosure Date": row["Date of Notice"],
                    "Details": pd.DataFrame(detail_data),
                })

                page.go_back()

        browser.close()

    return main_table, debenture_details

def save_data(main_table, debenture_details):
    """Save extracted data to JSON files."""
    today = datetime.now().strftime("%Y-%m-%d")
    main_table.to_json(os.path.join(DATA_DIR, f"{today}_main.json"), orient="records", indent=4)
    for detail in debenture_details:
        detail["Details"].to_json(
            os.path.join(DATA_DIR, f"{today}_{detail['Person']}_details.json"),
            orient="records",
            indent=4,
        )

def load_previous_data():
    """Load previous day's data if available."""
    yesterday = (datetime.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        main_table = pd.read_json(os.path.join(DATA_DIR, f"{yesterday}_main.json"))
        debenture_details = []
        for file in os.listdir(DATA_DIR):
            if file.startswith(yesterday) and file.endswith("_details.json"):
                person = file.split("_")[1]
                details = pd.read_json(os.path.join(DATA_DIR, file))
                debenture_details.append({"Person": person, "Details": details})
        return main_table, debenture_details
    except FileNotFoundError:
        return None, None

def detect_changes(today_main, today_details, prev_main, prev_details):
    """Detect changes between today's and previous day's data."""
    changes = []

    if prev_main is not None:
        added = today_main[~today_main.isin(prev_main.to_dict(orient="records"))]
        removed = prev_main[~prev_main.isin(today_main.to_dict(orient="records"))]
        if not added.empty:
            changes.append("New persons added:")
            changes.append(added.to_string(index=False))
        if not removed.empty:
            changes.append("Persons removed:")
            changes.append(removed.to_string(index=False))

    for today_detail in today_details:
        prev_detail = next((d for d in prev_details if d["Person"] == today_detail["Person"]), None)
        if prev_detail is not None:
            diff = today_detail["Details"].merge(prev_detail["Details"], indicator=True, how="outer")
            diff = diff[diff["_merge"] != "both"]
            if not diff.empty:
                changes.append(f"Changes for {today_detail['Person']}:")
                changes.append(diff.to_string(index=False))

    return changes

def send_email(changes, main_table, debenture_details):
    """Send email notification."""
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = f"HKEX Debenture Holdings Update – {STOCK_CODE} HK"

    if not changes:
        body = "<p>No change in debenture holdings since the previous day.</p>"
    else:
        body = "<p>Update detected in debenture holdings.</p>"
        body += "<h3>Main Table</h3>"
        body += main_table.to_html(index=False)
        for detail in debenture_details:
            body += f"<h3>Details for {detail['Person']}</h3>"
            body += detail["Details"].to_html(index=False)

    msg.add_alternative(body, subtype="html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, SMTP_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    today_main, today_details = fetch_disclosures()
    save_data(today_main, today_details)

    prev_main, prev_details = load_previous_data()

    # If no previous data exists, initialize with today's data
    if prev_main is None or prev_details is None:
        changes = ["No previous data available. Initialized with today's data."]
    else:
        changes = detect_changes(today_main, today_details, prev_main, prev_details)

    send_email(changes, today_main, today_details)