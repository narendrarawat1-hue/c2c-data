import requests
import xml.etree.ElementTree as ET
import pandas as pd
import io
import os

# ==============================
# CONFIG
# ==============================

SERVER = "https://prod-apsoutheast-a.online.tableau.com"
API_VERSION = "3.19"

PAT_NAME = os.getenv("TABLEAU_PAT_NAME")
PAT_SECRET = os.getenv("TABLEAU_PAT")

SITE = "cars24"
VIEW_ID = "e4fd94d1-3a86-4d66-a6bf-fc57f7ab2f4c"

# ✅ IMPORTANT (root folder for GitHub Pages)
CSV_FILE = "c2c_dashboard_1.csv"
HTML_FILE = "c2c_live_dashboard.html"


# ==============================
# SIGN IN
# ==============================

def sign_in():
    url = f"{SERVER}/api/{API_VERSION}/auth/signin"

    payload = {
        "credentials": {
            "personalAccessTokenName": PAT_NAME,
            "personalAccessTokenSecret": PAT_SECRET,
            "site": {"contentUrl": SITE}
        }
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        raise Exception(f"❌ Tableau Auth Failed: {response.text}")

    root = ET.fromstring(response.text)
    ns = {"t": "http://tableau.com/api"}

    token = root.find(".//t:credentials", ns).attrib["token"]
    site_id = root.find(".//t:site", ns).attrib["id"]

    print("✅ Signed in to Tableau")
    return token, site_id


# ==============================
# DOWNLOAD CSV
# ==============================

def download_csv(token, site_id):
    url = f"{SERVER}/api/{API_VERSION}/sites/{site_id}/views/{VIEW_ID}/data"
    headers = {"X-Tableau-Auth": token}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"❌ CSV Download Failed: {response.text}")

    df = pd.read_csv(io.StringIO(response.text))

    print(f"✅ Data downloaded: {df.shape}")

    df.to_csv(CSV_FILE, index=False)
    print(f"✅ CSV saved: {CSV_FILE}")

    return df


# ==============================
# GENERATE HTML
# ==============================

def generate_html(df):
    last_updated = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""
    <html>
    <head>
        <title>C2C Dashboard</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            h2 {{ color: #333; }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
            }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h2>📊 C2C Dashboard (Auto Updated)</h2>
        <p><b>Last Updated:</b> {last_updated}</p>
        {df.to_html(index=False)}
    </body>
    </html>
    """

    with open(HTML_FILE, "w") as f:
        f.write(html_content)

    print(f"✅ HTML updated: {HTML_FILE}")


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
    token, site_id = sign_in()

    df = download_csv(token, site_id)

    generate_html(df)

    sign_out(token)

    print("\n🎉 DONE\n")
