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

# Shopify Transfers Export

This project automates exporting active Shopify inventory transfers and updating a shared Google Sheets dashboard. It collects transfer data via the Shopify GraphQL Admin API, processes each line item including product images, and updates individual Google Sheets tabs with clean formatting and embedded images. The script can also run automatically on a schedule using macOS launchd.

---

## Features

### Automated Shopify transfer export
Fetches all active transfers from Shopify using the GraphQL Admin API, including item-level details and featured product images.

### Individual Google Sheets tabs per transfer
Each transfer gets its own sheet containing:
- Transfer metadata (status, origin, destination, shipment counts)
- Itemized product list
- Embedded product images via the Google Sheets `IMAGE()` formula
- Auto-sized columns and row heights
- Cleanly formatted headers

### Central Index dashboard
A summary sheet listing:
- Transfer number  
- Number of line items  
- Status  
- Timestamp for last update  

### Scheduled automation
The script can run daily using a macOS launch agent configured with launchd.

### Safe configuration using `.env`
Environment variables are kept private using a `.env` file and `.env.example` template.

---

## Project Structure

```
shopify-transfers-export/
│
├── scrapers/
│   ├── shopify_transfers_pretty_export.py   # Main script
│   ├── run_transfers.sh                     # Shell runner
│   ├── .env.example                         # Example env vars (safe to commit)
│   └── token.pkl (ignored)                  # Google OAuth token
│
├── .gitignore
├── README.md
└── LICENSE
```

---

## Requirements

### Install Python Packages
```
pip install -r requirements.txt
```

Packages include:
- pandas  
- gspread  
- google-auth  
- google-auth-oauthlib  
- google-api-python-client  
- python-dotenv  
- requests  
- python-dateutil  

### Other Requirements

Create a `.env` file containing:

```
SHOPIFY_SHOP_DOMAIN=
SHOPIFY_ACCESS_TOKEN=
SHOPIFY_API_VERSION=2025-10

GSPREAD_SHEET_ID=
GOOGLE_OAUTH_CLIENT_JSON=/absolute/path/to/client_secret.json
GOOGLE_OAUTH_TOKEN_PKL=/absolute/path/to/token.pkl
```

> Do **not** commit `.env` or actual credentials.

---

## How the Script Works (Beginner Friendly)

This project has three major components:

### 1. Fetch transfers from Shopify
The script queries Shopify with GraphQL to pull all transfers that are:

- Created within a given date range  
- Not canceled  
- Not completed  

It then fetches line-item data including SKUs, quantities, and product images.

### 2. Build a clean dataset
Each transfer is normalized into a pandas DataFrame so the script can:

- Group transfers  
- Calculate totals  
- Build clean tables  
- Generate Google Sheets IMAGE formulas  

### 3. Upload to Google Sheets
For every run:

- The **Index** tab is fully overwritten  
- The **Transfers** tab is fully overwritten  
- Each transfer gets its own tab  
- Row heights and column widths are adjusted  
- Header row is bold and centered  
- Images are inserted via formula  

The script also writes a timestamp to `Index!F1`.

---

## Environment Variables Explained

### Shopify
| Variable | Description |
|---------|-------------|
| `SHOPIFY_SHOP_DOMAIN` | Store domain (example.myshopify.com) |
| `SHOPIFY_ACCESS_TOKEN` | Admin API token |
| `SHOPIFY_API_VERSION` | API version to use |

### Google Sheets
| Variable | Description |
|---------|-------------|
| `GSPREAD_SHEET_ID` | Google Sheet ID |
| `GOOGLE_OAUTH_CLIENT_JSON` | Path to OAuth client JSON |
| `GOOGLE_OAUTH_TOKEN_PKL` | Path where OAuth token is saved |

---

## Running the Script Manually

Run from inside the `scrapers/` directory:

```
set -a
. ./.env
set +a

python3 shopify_transfers_pretty_export.py
```

If it's your first time, Google OAuth will open a browser window.

---

## Automating with macOS Launchd

You can automate the script using a launch agent plist.

### Install

```
cp com.shopify.transfers.export.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.shopify.transfers.export.plist
```

### Check if running

```
launchctl list | grep shopify
```

### Logs

```
~/Library/Logs/shopify-transfers.log
```

### Unload

```
launchctl unload ~/Library/LaunchAgents/com.shopify.transfers.export.plist
```

---

## Troubleshooting

### Google OAuth keeps asking to log in
```
rm token.pkl
```

### Old transfer tabs still exist
The script updates existing tabs but does not remove old ones.  
You may delete them manually or enable an optional auto-archive mode.

### Images not loading
Google Sheets rate limits previewing images.  
Using `=IMAGE(url, 4, 80, 80)` improves reliability.

### Script not running in launchd
Make sure all paths in `.env` are **absolute**.

---

## How It Works Internally (Detailed Beginner Breakdown)

### 1. Google Sheets Authentication
The script loads credentials and, if needed, opens a browser for you to log in.  
A cached token prevents future logins.

### 2. Shopify Transfer Fetching
GraphQL queries handle:

- Transfers list  
- Pagination  
- Line-item fetches  
- Featured media image URLs  

### 3. Data modeling
All data becomes a big DataFrame so the script can group by transfer.

### 4. Google Sheets Upload
Three types of tabs:

- Index  
- Transfers  
- Per-transfer formatted tabs  

### 5. Auto-formatting
The script uses batchUpdate to:

- Reset row heights  
- Auto-resize columns  
- Insert image formulas  
- Bold + center headers  
- Remove frozen rows  

---

## Why This Project Matters

This automation solves real operational challenges:

- Shopify UI is limited for transfer reporting  
- Teams need reliable, readable overviews  
- Manual updates are slow and error-prone  
- Automated syncing ensures accurate daily data  
- Google Sheets is easy for non-technical teams  

---

## Showcasing This Project Professionally

A polished portfolio description:

> A real-world automation pipeline that fetches Shopify inventory transfers via GraphQL and pushes formatted, image-rich reports into Google Sheets. Includes pagination handling, structured data modeling, Google Sheets batch formatting, and macOS automation for daily runs.

---

## License

MIT License.  
See `LICENSE` for details.

---

## Final Notes

Feel free to open issues or submit improvements.  
Happy building!
