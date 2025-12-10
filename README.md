<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" />
  <img src="https://img.shields.io/github/last-commit/amrocodes/shopify-transfers-export" />
  <img src="https://img.shields.io/github/issues/amrocodes/shopify-transfers-export" />
  <img src="https://img.shields.io/github/issues-pr/amrocodes/shopify-transfers-export" />
  <img src="https://img.shields.io/badge/code%20style-black-000000.svg" />

  <!-- NEW: Powered by APIs -->
  <img src="https://img.shields.io/badge/Shopify_API-Connected-95BF47?logo=shopify&logoColor=white" />
  <img src="https://img.shields.io/badge/Google_Sheets_API-Connected-34A853?logo=googlesheets&logoColor=white" />
</p>

# Shopify Transfers Export (Automated with GitHub Actions)

This project automatically exports active Shopify inventory transfers and pushes clean, formatted reports into a shared Google Sheet. It removes the need for any manual exports or local scripts and ensures the team always has accurate, updated information.

The automation runs entirely in the cloud using **GitHub Actions**, with optional manual triggers that anyone on the team can use.

---

## 🌟 Features

### ✅ Automated Daily Sync (GitHub Actions)
- Pulls all current Shopify transfers once per day.
- Uploads formatted data directly into a Google Sheet.
- Option for team members to trigger manual runs without needing a GitHub account.

### ✅ Clean Google Sheets Output
- Index dashboard summarizing all transfers.
- Raw full-table "Transfers" tab.
- A dedicated tab for each active transfer (`#Txxxx`).
- Product images inserted using `IMAGE()` formulas.
- Auto-sized columns and consistent formatting.
- Automatic removal of old/stale transfer tabs.

### ✅ Shopify API Integration
- Uses GraphQL Admin API.
- Handles pagination automatically.
- Collects item quantities, SKUs, and product images.
- Filters out cancelled/completed transfers.

### ✅ Google Sheets API Integration
- Uses a service account for secure, headless authentication.
- Batch updates for formatting and autosizing.
- Fast, reliable writes.

### ✅ Zero Local Setup Required
After configuration:
- No Python environment needed.
- No API keys stored locally.
- No running scripts on personal machines.

---

## 📂 Project Structure

```
shopify-transfers-export/
│
├── shopify_transfers_pretty_export.py      # Main script
├── .github/
│   └── workflows/
│       └── shopify-transfers.yml           # GitHub Actions workflow
│
├── .env.example                            # Environment template
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚙️ How It Works (Simple Overview)

### 1. Fetch transfers from Shopify  
The script queries Shopify for:
- Transfers within a target date range
- Transfers not yet fully completed
- Each transfer’s line-item details
- Featured product images

### 2. Build a clean dataset  
The script organizes everything into a pandas DataFrame so it can easily:
- Group by transfer
- Clean fields
- Produce consistent outputs

### 3. Update the Google Sheet  
Each run:
- Refreshes the **Index** tab
- Updates the **Transfers** tab
- Creates or replaces individual **#Txxxx** tabs
- Prunes old/stale tabs
- Inserts a timestamp
- Formats everything automatically

All updates are delivered using the Google Sheets API.

---

## 🚀 Automation (GitHub Actions)

This workflow is defined in `.github/workflows/shopify-transfers.yml`.

### Workflow triggers
```yaml
on:
  schedule:
    - cron: "0 2 * * *"   # Daily at 02:00 UTC (11:00 JST)
  workflow_dispatch:       # Allows manual triggers
```

### Secrets Required

| Secret | Description |
|--------|-------------|
| `SHOPIFY_SHOP_DOMAIN` | Shopify store domain |
| `SHOPIFY_ACCESS_TOKEN` | Private Admin API token |
| `SHOPIFY_API_VERSION` | API version |
| `GSPREAD_SHEET_ID` | Google Sheet ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON_B64` | Base64‑encoded service account JSON |

These are stored safely in GitHub Secrets.

---

## 🧪 Manual Runs (For the Team)

Anyone can trigger the script manually:

1. Open the repository.
2. Click **Actions**.
3. Select **Shopify Transfers Export** workflow.
4. Click **Run workflow**.

No installation. No API keys. No coding.

---

## 📊 Google Sheets Format

### **Index tab**
- Transfer ID
- Status
- Origin & destination
- Item totals
- Last updated timestamp

### **Transfers tab**
All transfer rows combined.

### **Individual transfer tabs**
Each includes:
- Header metadata
- SKU list
- Quantities
- Image previews
- Auto‑formatting

Old tabs are automatically removed to keep everything current.

---

## 🔒 Security

This project follows strong security practices:
- Service account authentication (no OAuth popups)
- API secrets stored only in GitHub Secrets
- `.env` ignored from Git
- No business data stored in the repository

---

## 📦 Requirements (For Optional Local Development)

```
pip install -r requirements.txt
```

Packages used:
- pandas  
- requests  
- gspread  
- google-auth  
- google-api-python-client  
- python-dateutil  

---

## 📘 License

MIT License.

---

## 🙌 Acknowledgements

Powered by:
- Shopify GraphQL Admin API  
- Google Sheets API  
- GitHub Actions  

This project replaces a manual, repetitive task with a robust, automated workflow that keeps transfer data accurate and accessible for everyone.

