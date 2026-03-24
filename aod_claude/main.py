import os
import requests
import xml.etree.ElementTree as ET

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
    get_view_csv(token, site_id)
    sign_out(token)

    print("\n🎉 DONE\n")
