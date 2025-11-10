cat > README.md << 'EOF'
# Shopify Transfers → Google Sheets Exporter

Exports Shopify Inventory Transfers to a formatted Google Sheet with per-transfer tabs and inline product images.

## What it does 
- Fetches transfers via Shopify Admin GraphQL API (date-windowed, excludes TRANSFERRED/CANCELED).
- Builds an "Index" and "Transfers" tab.
- Creates one sheet per transfer with a compact header and image-enabled items table.
- Formats each tab (row heights, column sizes, centered bold headers).
- Writes a timestamp on the Index tab.
- Optional: prunes stale per-transfer tabs not present in the current export.

## Requirements
- Python 3.10+
- A Shopify Admin API access token with permissions to read inventory transfers and products.
- Google OAuth client (user-flow) that can access Google Sheets.
- A target Google Sheet you own.

## Setup (local)
1. **Clone and install**
   ```bash
   git clone https://github.com/amrocodes/shopify-transfers-export.git
   cd shopify-transfers-export
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt  # create this file if you like (see below)
