Here is a clean, repo-ready `README.md` you can drop in:

---

# Systematic Assessment of Clinical Evidence for FDA-Approved AI/ML Medical Devices

This repository implements a **three-phase automated pipeline** for mapping the clinical evidence base supporting FDA-approved artificial intelligence and machine learning (AI/ML) medical devices.

It combines:

* Automated PubMed outcome-study searches
* FDA 510(k) page scraping for ClinicalTrials.gov links
* PubMed retrieval of trial-linked publications
* Manual quality control and bias assessment (external to code)

All scripts are designed to be run **sequentially** in Google Colab or a similar Python environment.

---

## Objective

To systematically identify and characterize:

* Published **patient-centered outcome studies**
* Prospectively registered **clinical trials**
* Published **trial results**
  supporting FDA-authorized AI/ML medical devices.

The analysis universe includes **all 1,248 FDA-authorized AI/ML devices** cleared or approved through **July 30, 2025**, across 510(k), De Novo, and PMA pathways.

---

## Data Source

FDA database of AI/ML-enabled medical devices
(Excel download, accessed July 29, 2025)
[https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-enabled-medical-devices](https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-enabled-medical-devices)

---

## Repository Structure

```
.
├── ai-ml-enabled-devices-excel (1).xlsx   # Input file (FDA device list)
├── s1.py                                  # PubMed outcome-study sweep
├── s2.py                                  # FDA 510(k) ClinicalTrials.gov scraper
├── s3.py                                  # Trial-linked PubMed retrieval
└── README.md
```

---

## Installation

```bash
pip install pandas requests beautifulsoup4 biopython openpyxl lxml
```

(Optional)
Set an NCBI API key to increase PubMed rate limits:

```bash
export NCBI_API_KEY="your_key_here"
```

---

## Input File Requirements

The input file must be an Excel or CSV file containing:

| Column Name   | Description                                   |
| ------------- | --------------------------------------------- |
| ID            | FDA device identifier (rename Device ID → ID) |
| Device Name   | FDA-cleared device name                       |
| Manufacturer  | Manufacturer name                             |
| 510(k) Number | 510(k) identifier (format: K######)           |

Example file included in repo:

```
ai-ml-enabled-devices-excel (1).xlsx
```

---

## Pipeline Overview

Each script must be run **in order**.

---

### Phase S-1: PubMed Outcome-Study Sweep

**Script:** `s1.py`

Automated PubMed search for **patient-centered outcome studies** per device.

**Search strategy includes:**

* Device name variants
* Manufacturer affiliation
* Outcome terms: mortality, morbidity, length of stay, readmission, complications
* Human-only studies

**Output:**

```
s1_pubmed_results.csv
```

| Column               | Description                |
| -------------------- | -------------------------- |
| Device Name          | FDA device name            |
| Literature Found     | Binary indicator (0/1)     |
| Example Study Title  | Most recent matching study |
| Example First Author | First author of that study |

**Run:**

```bash
python s1.py
```

---

### Phase S-2: ClinicalTrials.gov Link Extraction from FDA 510(k) Pages

**Script:** `s2.py`

Scrapes FDA 510(k) summary pages to extract **ClinicalTrials.gov** registrations.

**Methods:**

* Direct hyperlink detection
* Plain-text NCT identifier extraction

**Output:**

```
fda_trial_links.csv
```

| Column    | Description                          |
| --------- | ------------------------------------ |
| 510(k) ID | FDA 510(k) identifier                |
| Trial URL | ClinicalTrials.gov registration link |

**Run:**

```bash
python s2.py
```

---

### Phase S-3: Published Clinical Trial Retrieval

**Script:** `s3.py`

Links ClinicalTrials.gov registrations to **published PubMed results**.

**Process:**

* Extracts NCT IDs
* Queries PubMed via E-utilities
* Retrieves abstracts linked via `[si]` field
* Concatenates multiple publications per trial

**Output:**

```
ctgov_pubmed_abstracts.csv
```

| Column           | Description                                 |
| ---------------- | ------------------------------------------- |
| 510(k) ID        | FDA 510(k) identifier                       |
| Trial URL        | ClinicalTrials.gov URL                      |
| Linked Abstracts | Concatenated PubMed abstracts (│-separated) |

**Run:**

```bash
python s3.py
```

---

## Manual Phase (S-04): Data Extraction and Quality Control

*(External to code; described for reproducibility)*

After automated retrieval:

* Two independent reviewers manually extract:

  * Study design
  * Sample size
  * Geography
  * Workflow integration
  * Clinical task type
  * Validation approach
  * Population demographics
  * Exclusion criteria
  * Funding source
  * Equity and bias indicators

* Discrepancies resolved by consensus

* Registry data cross-validated against publications

This phase yields structured variables for downstream analysis of:

* Evidence gaps
* Population representativeness
* Potential bias
* Regulatory validation rigor

---

## Rate Limiting and Compliance

* PubMed (NCBI E-utilities):

  * 0.35 s between requests (no API key)
  * 0.10 s between requests (with API key)

* FDA web scraping:

  * 0.35 s between page requests
  * Retry once after 5 minutes on failure

---

## Expected Outputs

* Identification of FDA AI devices with:

  * Published outcome studies
  * Registered clinical trials
  * Published trial results

* Mapping of:

  * Evidence density
  * Population diversity
  * Bias risk
  * Regulatory-linked validation

---

## Reproducibility Notes

* All scripts are deterministic
* Input file defines the analysis universe
* Outputs are CSV-based and versionable
* Designed for scheduled re-runs as FDA approvals evolve

---

## Citation

If using this pipeline, please cite:

> Systematic Assessment of Clinical Evidence for FDA-Approved AI/ML Medical Devices.
> Supplementary Methods.
> Data sources: FDA AI/ML Device Database, PubMed, ClinicalTrials.gov.

---

## Contact

For questions, issues, or extensions:
Open a GitHub issue or submit a pull request.

---

If you'd like, I can also add:

* CLI argument support
* Config file for paths and rate limits
* Logging and progress bars
* Notebook (.ipynb) wrappers for Colab
