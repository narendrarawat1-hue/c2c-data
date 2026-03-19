import requests
import xml.etree.ElementTree as ET
import base64
import os

# --- Tableau Auth ---
SERVER     = "https://prod-apsoutheast-a.online.tableau.com"
PAT_NAME   = "c2c-sync"
PAT_SECRET = os.environ["TABLEAU_PAT_SECRET"]   # from GitHub secret
SITE       = "cars24"

resp = requests.post(f"{SERVER}/api/3.19/auth/signin", json={
    "credentials": {
        "personalAccessTokenName": PAT_NAME,
        "personalAccessTokenSecret": PAT_SECRET,
        "site": {"contentUrl": SITE}
    }
})
root    = ET.fromstring(resp.text)
ns      = {"t": "http://tableau.com/api"}
TOKEN   = root.find(".//t:credentials", ns).attrib["token"]
SITE_ID = root.find(".//t:site", ns).attrib["id"]
print("✅ Tableau auth OK")

# --- Download raw CSV from Tableau ---
VIEW_ID  = "e4fd94d1-3a86-4d66-a6bf-fc57f7ab2f4c"
csv_resp = requests.get(
    f"{SERVER}/api/3.19/sites/{SITE_ID}/views/{VIEW_ID}/data",
    headers={"x-tableau-auth": TOKEN}
)
csv_bytes = csv_resp.content
print(f"✅ Downloaded from Tableau: {len(csv_bytes)/1024/1024:.2f} MB")

# --- Upload to GitHub ---
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]   # auto-provided by GitHub Actions
REPO         = "narendrarawat1-hue/c2c-data"
FILE_PATH    = "c2c_dashboard_1.csv"

gh  = requests.get(
    f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}",
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}
)
sha = gh.json().get("sha")

r = requests.put(
    f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}",
    headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
    json={
        "message": "Auto-update C2C CSV",
        "content": base64.b64encode(csv_bytes).decode(),
        "sha": sha
    }
)
print(f"✅ Uploaded to GitHub: {r.status_code}")
