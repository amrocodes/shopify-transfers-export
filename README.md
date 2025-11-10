# Shopify Transfers Export

This project automates the process of exporting Shopify inventory transfers, extracting product images, and updating a Google Sheet with clean, readable transfer tabs. It was built to help operations teams track transfer status, quantities, and item details without manually exporting anything from Shopify.

The script runs locally or on a schedule and creates:

- An **Index** tab with a high-level summary and a timestamp  
- A **Transfers** tab containing raw line-item data  
- One **tab per transfer**, including:
  - A compact header (status, dates, notes, tags, origin, destination)
  - A formatted item table  
  - Inline product images using Google Sheets `IMAGE()` formulas  
  - Auto-sized columns and dynamic row heights

This is designed for teams who need a clear, always-updated view of ongoing Shopify transfers.

---

## Features

### Shopify Integration
- Pulls live transfer data using the Shopify Admin GraphQL API  
- Fetches product images (`featuredMedia.preview.image.url`)  
- Batches GraphQL requests to stay under Shopify's cost limits  
- Automatically excludes completed or canceled transfers

### Google Sheets Automation
- Updates a target Google Sheet in three parts:
  1. `Index` tab with summary and timestamp  
  2. `Transfers` tab with all raw line items  
  3. One tab per transfer, fully formatted  
- Adjusts column widths, row heights, alignment and headers via the Google Sheets API  
- Inserts images with `=IMAGE(url, 4, 80, 80)`

### Optional Excel Output
- Builds a local Excel file before upload  
- Useful for backups or offline review

### Scheduling (macOS, Linux)
- Supports macOS `launchd` or Linux `cron` for hands-free operation  
- Can run daily or hourly, depending on your workflow

---

## Requirements

- Python 3.10 or later  
- A Google Cloud project with:
  - Google Sheets API enabled  
  - Google Drive API enabled  
  - OAuth client credentials (desktop app)  
- Shopify Admin API access token  
- A Google Sheet where data will be written

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/amrocodes/shopify-transfers-export.git
cd shopify-transfers-export
