

# ============================================================
# Cell 1 – Install & imports
# ============================================================
!pip install -q pandas requests openpyxl tqdm   #  ← added “tqdm”


import time, re, requests, pandas as pd
from google.colab import files
from pathlib import Path
from tqdm.notebook import tqdm  


# Config — edit these 3 lines if you wish
OUTCOME_TERMS = (
    "mortality OR morbidity OR \"length of stay\" "
    "OR readmission OR complication*"
)
EMAIL = "tmlunde@gmail.com"
TOOL  = "AIOutcomeScan"


# PubMed endpoints
ESEARCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
RATE_LIMIT_S = 0.35   # ≤3 requests / sec




# ============================================================
# Cell 2 – Upload the Excel (or CSV) file
# ============================================================
uploaded = files.upload()
INPUT_FILE = list(uploaded.keys())[0]    # first uploaded file


# Column names in your sheet – change if they differ
DEVICE_COL  = "Device"
COMPANY_COL = "Company"


print(f"Loaded {INPUT_FILE}")


# ============================================================
# Cell 3 – Load data into a DataFrame
# ============================================================
suffix = Path(INPUT_FILE).suffix.lower()
if suffix == ".xlsx":
    df = pd.read_excel(INPUT_FILE)
elif suffix == ".csv":
    df = pd.read_csv(INPUT_FILE)
else:
    raise ValueError("File must be .xlsx or .csv")


df = df[[DEVICE_COL, COMPANY_COL]].dropna()
print(f"{len(df)} devices loaded")




# ============================================================
# Cell 4 – Revised helper functions (handles TytoCare)
# ============================================================
import urllib.parse, unicodedata


def _variants(device):
    """Return a set of common spelling variants."""
    # strip trademark/registration symbols & normalise
    clean = unicodedata.normalize("NFKD", device).encode("ascii", "ignore").decode()
    no_punct = re.sub(r"[®™©]", "", clean).strip()
    # core variants
    spaced   = no_punct
    nospace  = no_punct.replace(" ", "")
    hyphen   = no_punct.replace(" ", "-")
    return {spaced, nospace, hyphen}


def _quoted(field_variants):
    """'"word"[tiab]' ‑ style OR string for a set of variants."""
    return " OR ".join(f"\"{v}\"[tiab]" for v in field_variants)


def build_term(device, company):
    device_part  = f"({_quoted(_variants(device))})"
    company_part = f" AND ({_quoted(_variants(company))})[ad]" if pd.notna(company) else ""
    term = f"{device_part}{company_part} AND ({OUTCOME_TERMS}) AND humans[mh]"
    return urllib.parse.quote_plus(term)


def get_first_hit_abstract(pmid):
    if not pmid:
        return ""
    r = requests.get(
        ESUMMARY,
        params=dict(db="pubmed", id=pmid, retmode="json",
                    tool=TOOL, email=EMAIL),
        timeout=15
    )
    r.raise_for_status()
    js = r.json()["result"][str(pmid)]
    title = js.get("title", "")
    first_author = js.get("sortfirstauthor", "")
    return f"{first_author}: {title}"


def fetch_pubmed(device, company):
    term = build_term(device, company)
    r = requests.get(
        ESEARCH,
        params=dict(db="pubmed", term=term, retmode="json",
                    retmax=1, tool=TOOL, email=EMAIL),
        timeout=15
    )
    r.raise_for_status()
    es = r.json()["esearchresult"]
    count = int(es["count"])
    if count == 0:
        return 0, ""
    pmid = es["idlist"][0] if es["idlist"] else ""
    return 1, get_first_hit_abstract(pmid)


# ============================================================
# Cell 5 – Run the loop (respects rate‑limit)
# ============================================================
hits, abstracts = [], []


for dev, comp in tqdm(                       #  ← wrap with tqdm
        df[[DEVICE_COL, COMPANY_COL]].itertuples(index=False, name=None),
        total=len(df),
        desc="Scanning devices"):
    try:
        found, abst = fetch_pubmed(dev, comp)
    except Exception as e:
        found, abst = 0, f"ERROR: {e}"
    hits.append(found)
    abstracts.append(abst)
    time.sleep(RATE_LIMIT_S)


df_out = pd.DataFrame({
    "Device": df[DEVICE_COL],
    "article_found": hits,
    "abstract": abstracts
})
print("Scan complete.")




# ============================================================
# Cell 6 – Save & offer download
# ============================================================
OUTPUT_CSV = "pubmed_hits.csv"
df_out.to_csv(OUTPUT_CSV, index=False)
files.download(OUTPUT_CSV)
