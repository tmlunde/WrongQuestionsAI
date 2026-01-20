# ============================================================
# 🟢  Cell 1 – Install & imports
# ============================================================
!pip install -q pandas requests tqdm openpyxl


import re, time, urllib.parse, requests, pandas as pd
from google.colab import files
from tqdm.notebook import tqdm




# ============================================================
# 🟢  Cell 2 – Upload the file with ctgov URLs
#     (CSV or XLSX; must contain columns "ID" and "ctgov_url")
# ============================================================
uploaded = files.upload()
INFILE = list(uploaded.keys())[0]
ID_COL, CTURL_COL = "ID", "ctgov_url"


ext = INFILE.split(".")[-1].lower()
df_in = (pd.read_excel if ext == "xlsx" else pd.read_csv)(INFILE)
df_in = df_in[[ID_COL, CTURL_COL]].dropna()


print(f"{len(df_in)} records loaded.")




import requests, re, time, xml.etree.ElementTree as ET


API_KEY = "33063d17c6b3e7cba91c054945679a652208"          # paste your real NCBI key, or leave "" for none
MAX_PMIDS = 20        # safety cap per trial


ESearch = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFetch  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def nct_from_url(url: str) -> str:
    m = re.search(r"(NCT\d{8})", str(url))
    return m.group(1) if m else ""


def safe_get(url, params, max_try=4):
    if API_KEY:
        params["api_key"] = API_KEY
    pause = 1.0
    for _ in range(max_try):
        r = requests.get(url, params=params, timeout=15)
        if r.status_code not in (429, 502):
            r.raise_for_status()
            return r
        time.sleep(pause)
        pause *= 2
    r.raise_for_status()


def pmids_from_nct(nct: str) -> list[str]:
    if not nct:
        return []
    r = safe_get(
        ESearch,
        params=dict(db="pubmed", term=f"{nct}[si]", retmode="json",
                    retmax=MAX_PMIDS)
    )
    return r.json()["esearchresult"]["idlist"]


def abstract_from_pmid(pmid: str) -> str:
    r = safe_get(
        EFetch,
        params=dict(db="pubmed", id=pmid, retmode="xml")
    )
    root = ET.fromstring(r.text)
    abst_elems = root.findall(".//AbstractText")
    texts = [" ".join(elem.itertext()) for elem in abst_elems]
    return " ".join(texts).strip()






# ============================================================
# 🟢  Cell 4 – Main loop (progress bar unchanged)
# ============================================================
rows = []


for _, row in tqdm(df_in.iterrows(), total=len(df_in), desc="Fetching"):
    nct_id   = nct_from_url(row[CTURL_COL])
    pmids    = pmids_from_nct(nct_id)           # all PubMed IDs linked to this trial
    abs_text = [abstract_from_pmid(p) for p in pmids]          # full abstracts
    joined   = " │ ".join(f"PMID-{p}: {a}" for p, a in zip(pmids, abs_text))  \
               if pmids else ""
   
    rows.append({
        "ID":         row[ID_COL],
        "ctgov_url":  row[CTURL_COL],
        "abstract":   joined
    })
   
    time.sleep(0.10 if API_KEY else 0.35)       # faster if you supplied an API key


# — save & download —
df_out = pd.DataFrame(rows)
df_out.to_csv("ctgov_pubmed_abstracts.csv", index=False, sep=';')
files.download("ctgov_pubmed_abstracts.csv")
