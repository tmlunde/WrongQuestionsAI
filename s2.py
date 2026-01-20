# ============================================================
# Cell 1 – Install & imports (now includes tqdm)
# ============================================================
!pip install -q pandas requests beautifulsoup4 openpyxl tqdm


import re, time, requests, pandas as pd
from bs4 import BeautifulSoup
from google.colab import files
from tqdm.notebook import tqdm




# ============================================================
# Cell 2 – Upload the device list
# ============================================================
uploaded = files.upload()
INPUT_FILE = list(uploaded.keys())[0]
ID_COL = "ID"            # edit if header differs




# ============================================================
# Cell 3 – Load IDs
# ============================================================
ext = INPUT_FILE.split(".")[-1].lower()
df_ids = (pd.read_excel if ext == "xlsx" else pd.read_csv)(INPUT_FILE)
ids = df_ids[ID_COL].dropna().astype(str).tolist()
print(f"{len(ids)} 510(k) IDs loaded")




# ============================================================
# Cell 4 – Robust helper: grabs the ClinicalTrials.gov link
# ============================================================
import re, requests
from bs4 import BeautifulSoup


BASE = "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID="
HDRS = {
    # Desktop‑browser UA stops the FDA site from serving the light/mobile HTML
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125 Safari/537.36"
    )
}


def ctgov_link(kid: str) -> str:
    """
    Return the first ClinicalTrials.gov URL linked to a 510(k) ID, else ''.
    Handles:
      • <a href="…clinicaltrials.gov…">   (older pages)
      • rows that list only 'NCT########' as text (newer pages)
    """
    try:
        # Fetch full HTML for the 510(k) summary page
        html = requests.get(BASE + kid, headers=HDRS, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")


        # 1️⃣  Direct anchor that already contains the CT.gov URL
        a = soup.find("a", href=re.compile(r"clinicaltrials\.gov", re.I))
        if a and a.get("href"):
            return a["href"].strip()


        # 2️⃣  Any plain‑text NCT identifier anywhere in the page
        m = re.search(r"(NCT\d{8})", soup.get_text())
        if m:
            return f"https://www.clinicaltrials.gov/study/{m.group(1)}"


    except Exception:
        # Network or parse error → fall through and return blank
        pass


    return ""   # No CT.gov link found






# ============================================================
# Cell 5 – Loop with progress bar
# ============================================================
links = []
for kid in tqdm(ids, desc="Scanning FDA pages"):
    links.append(ctgov_link(kid))
    time.sleep(0.35)         # polite pause


df_out = pd.DataFrame({"ID": ids, "ctgov_url": links})
print("✅ Scrape complete.")




# ============================================================
# Cell 6 – Save & download
# ============================================================
df_out.to_csv("fda_trial_links.csv", index=False)
files.download("fda_trial_links.csv")
