import os
import smtplib
from email.message import EmailMessage
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json

# Email configuration
EMAIL_SENDER = "vincentsnews@gmail.com"
EMAIL_RECEIVER = "vincewong99@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_PASSWORD = os.getenv("HKEX_EMAIL_PASS")


def send_test_email():
    """Send a test email with the word 'hello'."""
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "hello"

    msg.set_content("hello")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, SMTP_PASSWORD)
        server.send_message(msg)
        print("Email sent successfully")


def fetch_disclosures_via_url(stock_code, start_date, end_date):
    """
    Fetch disclosures from the HKEX DI website using the structured URL.

    Args:
        stock_code (str): The stock code to search for.
        start_date (str): The start date for the search in 'YYYY-MM-DD' format.
        end_date (str): The end date for the search in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: A DataFrame containing the disclosure data.
    """
    # Construct the URL with the stock code and date range
    url = (
        f"https://di.hkex.com.hk/di/NSAllFormList.aspx?sa2=an&sid={hkex_sid}&corpn={company_name}"
        f"&sd={start_date}&ed={end_date}&cid=0&sa1=cl&scsd={start_date.replace('/', '%2f')}"
        f"&sced={end_date.replace('/', '%2f')}&sc={stock_code}&src=MAIN&lang=EN&g_lang=en&"
    )

    # Fetch the page content
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for HTTP issues

    # Parse the page content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the main table
    main_table = []
    debenture_details = []
    table = soup.find('table', {'id': 'grdPaging'})  # Updated table ID
    if table:
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cols = row.find_all('td')
            main_table.append({
                'Form Serial Number': cols[0].text.strip(),
                'Name of Substantial Shareholder / Director / Chief Executive': cols[1].text.strip(),
                'Reason for Disclosure': cols[2].text.strip(),
                'Number of Shares Bought / Sold / Involved': cols[3].text.strip(),
                'Average Price Per Share': cols[4].text.strip(),
                'Number of Shares Interested': cols[5].text.strip(),
                '% of Issued Voting Shares': cols[6].text.strip(),
                'Date of Relevant Event': cols[7].text.strip(),
                'Interests in Shares of Associated Corporation': cols[8].text.strip(),
                'Interests in Debentures': cols[9].text.strip()
            })

            # If 'Interests in Debentures' is 'Yes', fetch the debenture details
            if cols[9].text.strip().lower() == 'yes':
                link = cols[9].find('a')['href']  # Extract the link to the debenture details

                # Ensure the link has the correct scheme
                if not link.startswith("http"):
                    link = f"https://di.hkex.com.hk/di/{link}"  # Prepend base URL

                debenture_response = requests.get(link)
                debenture_response.raise_for_status()
                debenture_soup = BeautifulSoup(debenture_response.content, 'html.parser')

                debenture_table = debenture_soup.find('table', {'id': 'grdPaging'})
                if debenture_table:
                    debenture_rows = debenture_table.find_all('tr')[1:]  # Skip header row
                    for debenture_row in debenture_rows:
                        debenture_cols = debenture_row.find_all('td')
                        debenture_details.append({
                            'Form Serial Number': debenture_cols[0].text.strip(),
                            'Name of Listed Corporation / Associated Corporation': debenture_cols[1].text.strip(),
                            'Amount of Debentures Bought / Sold / Involved': debenture_cols[2].text.strip(),
                            'Reason for Disclosure': debenture_cols[3].text.strip(),
                            'Average Price Per Unit': debenture_cols[4].text.strip(),
                            'Date of Relevant Event': debenture_cols[5].text.strip()
                        })

    main_df = pd.DataFrame(main_table)
    debenture_df = pd.DataFrame(debenture_details)

    return main_df, debenture_df


def format_dataframe_as_html(df):
    """
    Convert a Pandas DataFrame to an HTML table.

    Args:
        df (pd.DataFrame): The DataFrame to convert.

    Returns:
        str: HTML representation of the DataFrame.
    """
    if df.empty:
        return "<p>No data available.</p>"
    return df.to_html(index=False, escape=False)


def get_company_name(stock_code):
    """
    Fetch the company name listed in HKEX for the given stock code.

    Args:
        stock_code (str): The stock code to search for.

    Returns:
        str: The company name listed in HKEX.
    """
    url = f"https://di.hkex.com.hk/di/NSSrchCorp.aspx?src=MAIN&lang=EN&g_lang=en&sc={stock_code}"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the company name from the page
    company_name_element = soup.find('span', {'id': 'lblCorpName'})
    if company_name_element:
        return company_name_element.text.strip()
    else:
        raise ValueError(f"Company name not found for stock code {stock_code}")


def load_previous_data(file_path):
    """Load the previously saved data from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}


def save_current_data(file_path, data):
    """Save the current data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def detect_changes(previous_data, current_data):
    """Detect changes between previous and current data."""
    return previous_data != current_data


if __name__ == "__main__":
    # Define a list of tickers with internal system ID, stock code, and company name
    tickers = [
        {"hkex_sid": "972", "stock_code": "488", "company_name": "Lai+Sun+Development+Co.+Ltd."},
        {"hkex_sid": "27", "stock_code": "17", "company_name": "New+World+Development+Co.+Ltd."}
    ]

    start_date = "01/01/2025"
    end_date = "28/12/2025"

    # Define the path to save previous data
    previous_data_file = "data/previous_data.json"

    # Load previous data
    previous_data = load_previous_data(previous_data_file)

    # Initialize a dictionary to store current data
    current_data = {}

    for ticker in tickers:
        hkex_sid = ticker["hkex_sid"]
        stock_code = ticker["stock_code"]
        company_name = ticker["company_name"]

        print(f"Fetching data for {company_name.replace('+', ' ')} (Stock Code: {stock_code})")

        main_df, debenture_df = fetch_disclosures_via_url(stock_code, start_date, end_date)

        # Store the data in the current_data dictionary
        current_data[stock_code] = {
            "main_table": main_df.to_dict(orient="records"),
            "debenture_table": debenture_df.to_dict(orient="records")
        }

    # Detect changes
    changes_detected = detect_changes(previous_data, current_data)

    # Update the email content
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = f"HKEX DI Data for {datetime.now().strftime('%d/%m/%Y')}"

    msg.set_content("This email contains HTML content. Please view it in an HTML-compatible email client.")
    msg.add_alternative(email_body, subtype="html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, SMTP_PASSWORD)
        server.send_message(msg)

    if changes_detected:
        print("Changes detected. Notification email sent successfully.")
        # Save the current data
        save_current_data(previous_data_file, current_data)
    else:
        print("No changes detected. Email sent for manual verification.")