import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime

# ==============================
# CONFIG
# ==============================

SERVER = "https://prod-apsoutheast-a.online.tableau.com"
API_VERSION = "3.19"

# From GitHub Secrets
TOKEN_NAME = os.getenv("TABLEAU_PAT_NAME")
TOKEN_VALUE = os.getenv("TABLEAU_PAT")

SITE_CONTENT_URL = "cars24"   # keep "" if default site
VIEW_ID = "2cd73242-c7a7-4abd-b2d6-bfa8d68fba31"   # replace this

# ==============================
# SIGN IN
# ==============================

def sign_in():
    url = f"{SERVER}/api/{API_VERSION}/auth/signin"

    payload = f"""
    <tsRequest>
        <credentials personalAccessTokenName="{TOKEN_NAME}"
                     personalAccessTokenSecret="{TOKEN_VALUE}">
            <site contentUrl="{SITE_CONTENT_URL}" />
        </credentials>
    </tsRequest>
    """

    headers = {"Content-Type": "application/xml"}

    response = requests.post(url, data=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"❌ Sign-in failed: {response.text}")

    root = ET.fromstring(response.text)
    token = root.find(".//t:credentials", 
                      {"t": "http://tableau.com/api"}).attrib["token"]

    site_id = root.find(".//t:site", 
                        {"t": "http://tableau.com/api"}).attrib["id"]

    print("✅ Signed in")
    return token, site_id


# ==============================
# GET VIEW DATA (CSV)
# ==============================

def get_view_csv(token, site_id):
    url = f"{SERVER}/api/{API_VERSION}/sites/{site_id}/views/{VIEW_ID}/data"

    headers = {
        "X-Tableau-Auth": token
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"❌ Data fetch failed: {response.text}")

    with open("output.csv", "wb") as f:
        f.write(response.content)

    print("✅ CSV downloaded: output.csv")


# ==============================
# EXTRACT DATE RANGE
# ==============================

def extract_date_range(df):
    """Extract min and max dates from the dataframe"""
    date_col = "Day of D.DTS"
    
    if date_col in df.columns:
        # Convert to datetime
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Remove NaN dates
        valid_dates = df[date_col].dropna()
        
        if len(valid_dates) > 0:
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            return min_date, max_date
    
    return None, None


# ==============================
# GENERATE HTML WITH DATE RANGE
# ==============================

def generate_html_with_date_range(df, min_date, max_date):
    """Generate enhanced HTML with date range information"""
    
    # Format dates
    min_date_str = min_date.strftime("%B %d, %Y") if min_date else "N/A"
    max_date_str = max_date.strftime("%B %d, %Y") if max_date else "N/A"
    
    # Create HTML header with date range
    html_header = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AOD Dashboard</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .date-range {{
                background-color: #3498db;
                padding: 10px 15px;
                border-radius: 5px;
                display: inline-block;
                margin-bottom: 15px;
                font-weight: bold;
            }}
            .date-from {{
                color: #27ae60;
            }}
            .date-to {{
                color: #e74c3c;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background-color: #34495e;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #ecf0f1;
            }}
            tr:hover {{
                background-color: #ecf0f1;
            }}
            .last-updated {{
                text-align: right;
                margin-top: 20px;
                font-size: 12px;
                color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 AOD Dashboard</h1>
            <div class="date-range">
                📅 Data Range: <span class="date-from">{min_date_str}</span> to <span class="date-to">{max_date_str}</span>
            </div>
        </div>
    """
    
    # Convert dataframe to HTML table
    table_html = df.to_html(index=False, classes="data-table")
    
    # Create footer
    html_footer = f"""
        <div class="last-updated">
            Last Updated: {datetime.now().strftime("%B %d, %Y at %H:%M:%S UTC")}
        </div>
    </body>
    </html>
    """
    
    return html_header + table_html + html_footer


# ==============================
# SIGN OUT
# ==============================

def sign_out(token):
    url = f"{SERVER}/api/{API_VERSION}/auth/signout"
    headers = {"X-Tableau-Auth": token}
    requests.post(url, headers=headers)
    print("🔒 Signed out")


# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    try:
        token, site_id = sign_in()

        get_view_csv(token, site_id)

        # ✅ Read CSV and extract date range
        df = pd.read_csv("output.csv")
        min_date, max_date = extract_date_range(df)
        
        print(f"📅 Date Range Detected: {min_date.strftime('%B %d, %Y')} to {max_date.strftime('%B %d, %Y')}")

        # ✅ Generate enhanced HTML with date range
        html_content = generate_html_with_date_range(df, min_date, max_date)

        with open("aod_claude/aod_dashboard_v3.html", "w") as f:
            f.write(html_content)

        print("✅ HTML updated with date range: aod_claude/aod_dashboard_v3.html")

        sign_out(token)

        print("\n🎉 DONE\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        raise
