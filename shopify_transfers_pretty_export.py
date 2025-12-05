#!/usr/bin/env python3
import os, sys, time, json, pickle
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser as dtparser
from typing import Dict, Any, List, Optional

# ---------- Google Sheets auth ----------
import gspread
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from gspread_dataframe import set_with_dataframe
from googleapiclient.discovery import build  # autosize + format
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account 

SHEET_ID = os.getenv("GSPREAD_SHEET_ID")
OAUTH_CLIENT_JSON = os.getenv("GOOGLE_OAUTH_CLIENT_JSON")
TOKEN_PATH = os.getenv("GOOGLE_OAUTH_TOKEN_PKL", "token.pkl")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

SHEET_ID = os.getenv("GSPREAD_SHEET_ID")
OAUTH_CLIENT_JSON = os.getenv("GOOGLE_OAUTH_CLIENT_JSON")
TOKEN_PATH = os.getenv("GOOGLE_OAUTH_TOKEN_PKL", "token.pkl")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

def get_gspread_client():
    """
    Returns an authenticated gspread client.

    - In CI (GitHub Actions):
        Uses GOOGLE_SERVICE_ACCOUNT_JSON_PATH and a service account JSON file.
    - Locally:
        Uses the OAuth client JSON + token.pkl flow.
    """
    # 1) CI / service-account mode
    sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    if sa_path:
        try:
            # This is the file the GitHub Action writes from the secret
            print(f"Using Google service account credentials (CI mode). Path: {sa_path}")
            if not os.path.exists(sa_path):
                print(f"Service account JSON path does not exist: {sa_path}")
                return None

            creds = service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=SCOPES,
            )
            return gspread.authorize(creds)
        except Exception as e:
            print(f"Google service account auth failed: {e}")
            # Fall through to local-mode auth if you ever run this script manually on your machine
            # with GOOGLE_SERVICE_ACCOUNT_JSON_PATH still set but broken.
            # If you don't want that, you can 'return None' here instead.

    # 2) Local OAuth-mode (what you used on your Mac)
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "rb") as f:
                creds = pickle.load(f)
        except Exception:
            creds = None

    if not creds:
        if not OAUTH_CLIENT_JSON or not os.path.exists(OAUTH_CLIENT_JSON):
            print("Google Sheets: missing GOOGLE_OAUTH_CLIENT_JSON; skipping upload.")
            return None
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_JSON, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    try:
        return gspread.authorize(creds)
    except Exception as e:
        print(f"Google Sheets auth failed: {e}")
        return None

def get_google_creds():
    """
    Return Credentials suitable for the Sheets API.

    - In CI (GitHub Actions): use the service account JSON pointed to by
      GOOGLE_SERVICE_ACCOUNT_JSON_PATH.
    - Locally: fall back to the same OAuth flow/token used elsewhere.
    """
    # CI / service-account mode
    sa_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_PATH")
    if sa_path:
        try:
            print(f"Using Google service account credentials for autosize. Path: {sa_path}")
            if not os.path.exists(sa_path):
                print(f"Service account JSON for autosize not found at {sa_path}")
                return None
            return service_account.Credentials.from_service_account_file(
                sa_path,
                scopes=SCOPES,
            )
        except Exception as e:
            print(f"Service account creds for autosize failed: {e}")
            return None

    # Local OAuth mode (same behaviour you had on your Mac)
    creds = None
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, "rb") as f:
                creds = pickle.load(f)
        except Exception:
            creds = None

    if not creds:
        if not OAUTH_CLIENT_JSON or not os.path.exists(OAUTH_CLIENT_JSON):
            print("No OAuth client JSON for autosize; skipping formatting.")
            return None
        flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_JSON, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)

    return creds

def autosize_transfer_tab(spreadsheet_id: str, ws, header_rows: int, nrows: int):
    """
    No frozen rows.
    Normalize ALL rows to default height first (≈21 px),
    then make only the data rows tall (~90 px) for the images.
    Auto-resize text columns and vertically center A:D in data rows.
    Also center-align and bold the table header.
    """
    sheet_id = ws.id
    service = build("sheets", "v4", credentials=get_google_creds())

    # 0-based indexes
    data_header_row = header_rows            # row with "Image/Product/SKU/Qty"
    data_start      = data_header_row + 1    # first product row
    data_end        = data_start + max(nrows, 0)  # exclusive
    reset_end       = max(data_end + 50, 2000)

    requests = [
        {  # remove freezing
            "updateSheetProperties": {
                "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 0}},
                "fields": "gridProperties.frozenRowCount"
            }
        },
        {  # normalize all rows (default height)
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": reset_end},
                "properties": {"pixelSize": 21},
                "fields": "pixelSize"
            }
        },
        {  # set image column A to ~90 px
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1},
                "properties": {"pixelSize": 90},
                "fields": "pixelSize"
            }
        },
        {  # auto-resize text columns B..D
            "autoResizeDimensions": {
                "dimensions": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 4}
            }
        },
        {  # enlarge only product rows
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": data_start, "endIndex": data_end},
                "properties": {"pixelSize": 90},
                "fields": "pixelSize"
            }
        },
        {  # vertically center A:D in product rows
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": data_start,
                    "endRowIndex": data_end,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
                },
                "cell": {"userEnteredFormat": {"verticalAlignment": "MIDDLE"}},
                "fields": "userEnteredFormat.verticalAlignment"
            }
        },
        {  # center-align + bold the header row (Image/Product/SKU/Qty)
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": data_header_row,
                    "endRowIndex": data_header_row + 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 4
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {"bold": True}
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,textFormat.bold)"
            }
        }
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests}
    ).execute()
    
# ---------- Shopify fetch ----------
import requests
SHOP_DOMAIN = os.getenv("SHOPIFY_SHOP_DOMAIN")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2025-10")

today = datetime.utcnow().date()
START_DATE = os.getenv("SHOPIFY_START_DATE", (today - timedelta(days=7)).isoformat())
END_DATE   = os.getenv("SHOPIFY_END_DATE",   (today + timedelta(days=7)).isoformat())

print(f"Fetching transfers from {START_DATE} to {END_DATE}")

if not SHOP_DOMAIN or not ACCESS_TOKEN:
    print("Set SHOPIFY_SHOP_DOMAIN and SHOPIFY_ACCESS_TOKEN environment variables.")
    sys.exit(1)

ENDPOINT = f"https://{SHOP_DOMAIN}/admin/api/{API_VERSION}/graphql.json"
HEADERS = {"X-Shopify-Access-Token": ACCESS_TOKEN, "Content-Type": "application/json"}

parts: List[str] = []
if START_DATE:
    parts.append(f"created_at:>={START_DATE}")
if END_DATE:
    parts.append(f"created_at:<={END_DATE}")
parts.append("NOT status:TRANSFERRED")
parts.append("NOT status:CANCELED")
QUERY_FILTER = " AND ".join(parts)
print("Using query filter:", QUERY_FILTER)

GQL_LIST_TRANSFERS = """
query ListTransfers($first:Int!, $after:String, $query:String) {
  inventoryTransfers(first: $first, after: $after, query: $query) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      name
      dateCreated
      status
      referenceName
      note
      tags
      totalQuantity
      receivedQuantity
      origin { name }
      destination { name }
    }
  }
}
"""

# Uses featuredMedia.preview.image.url (Admin API)
GQL_TRANSFER_ITEMS = """
query TransferItems($id:ID!, $first:Int!, $after:String) {
  inventoryTransfer(id: $id) {
    id
    lineItems(first: $first, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        title
        totalQuantity
        shippedQuantity
        pickedForShipmentQuantity
        processableQuantity
        shippableQuantity
        inventoryItem {
          id
          sku
          variant {
            product {
              featuredMedia {
                preview {
                  image { url }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def gql_request(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(ENDPOINT, headers=HEADERS, json={"query": query, "variables": variables}, timeout=60)
    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL error: {payload}")
    return payload["data"]

def normalize_ts(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    try:
        return dtparser.isoparse(s).isoformat()
    except Exception:
        return s

def list_transfers(query_filter: Optional[str]) -> List[Dict[str, Any]]:
    transfers = []
    after = None
    while True:
        data = gql_request(GQL_LIST_TRANSFERS, {"first": 50, "after": after, "query": query_filter})
        conn = data["inventoryTransfers"]
        transfers.extend(conn.get("nodes", []))
        if not conn["pageInfo"]["hasNextPage"]:
            break
        after = conn["pageInfo"]["endCursor"]
        time.sleep(0.3)
    return transfers

def list_transfer_items(transfer_id: str) -> List[Dict[str, Any]]:
    items = []
    after = None
    while True:
        data = gql_request(GQL_TRANSFER_ITEMS, {"id": transfer_id, "first": 100, "after": after})
        conn = data["inventoryTransfer"]["lineItems"]
        nodes = conn.get("nodes", [])
        items.extend(nodes)
        if not conn["pageInfo"]["hasNextPage"]:
            break
        after = conn["pageInfo"]["endCursor"]
        time.sleep(0.2)
    return items

def fetch_transfers(query_filter: Optional[str]) -> List[Dict[str, Any]]:
    rows = []
    transfers = list_transfers(query_filter)
    for t in transfers:
        base = {
            "transfer_id": t.get("id"),
            "transfer_name": t.get("name"),
            "created_utc": normalize_ts(t.get("dateCreated")),
            "status": t.get("status"),
            "reference_name": t.get("referenceName"),
            "note": t.get("note"),
            "tags": ", ".join(t.get("tags") or []),
            "origin": (t.get("origin") or {}).get("name"),
            "destination": (t.get("destination") or {}).get("name"),
            "total_qty": t.get("totalQuantity"),
            "received_qty": t.get("receivedQuantity"),
        }
        if base["status"] in ("TRANSFERRED", "CANCELED"):
            continue

        items = list_transfer_items(t["id"])
        for li in items:
            inv = li.get("inventoryItem") or {}
            variant = inv.get("variant") or {}
            product = variant.get("product") or {}
            fm = product.get("featuredMedia") or {}
            preview = fm.get("preview") or {}
            image = preview.get("image") or {}
            image_url = image.get("url")

            rows.append({**base,
                "line_item_id": li.get("id"),
                "title": li.get("title"),
                "sku": inv.get("sku"),
                "line_total_qty": li.get("totalQuantity"),
                "line_shipped_qty": li.get("shippedQuantity"),
                "line_picked_qty": li.get("pickedForShipmentQuantity"),
                "line_processable_qty": li.get("processableQuantity"),
                "line_shippable_qty": li.get("shippableQuantity"),
                "image_url": image_url
            })

    print(f"✅ Found {len(rows)} total line items.")
    has_images = sum(1 for r in rows if r.get('image_url'))
    print(f"🖼️ Found {has_images} items with image URLs.")
    return rows

# ---------- (Optional) Excel build ----------
def build_workbook(df: pd.DataFrame, out_path: str) -> pd.DataFrame:
    print(f"🧾 Building workbook: {out_path}")

    df["transfer_name"] = df["transfer_name"].astype(str).fillna("Unnamed Transfer").str.strip()
    df["image_formula"] = df["image_url"].apply(
        lambda url: f'=IMAGE("{url}", 4, 80, 80)' if isinstance(url, str) and url.startswith("http") else ""
    )

    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        idx_cols = ["transfer_id","transfer_name","status","origin","destination","created_utc"]
        for c in idx_cols:
            if c not in df.columns:
                df[c] = None
        idx = df.groupby(idx_cols).size().reset_index(name="line_count")
        idx.to_excel(writer, index=False, sheet_name="Index")

        df.drop(columns=["image_url","image_formula"], errors="ignore").to_excel(
            writer, index=False, sheet_name="Transfers"
        )

    print(f"✅ Workbook built successfully: {out_path}")
    return idx

# ---------- Main ----------
def main():
    print(f"Shop: {SHOP_DOMAIN}, API version: {API_VERSION}")
    rows = fetch_transfers(QUERY_FILTER)
    if not rows:
        print("No transfers found.")
        return
    df = pd.DataFrame(rows)
    out_name = f"shopify_transfers_pretty_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    idx_df = build_workbook(df, out_name)
    print(f"✅ Wrote {len(df)} rows to {out_name}")

    # -------- Google Sheets Upload --------
    try:
        gc = get_gspread_client()
        if gc and SHEET_ID:
            sh = gc.open_by_key(SHEET_ID)

            # Index tab
            ws_idx = next((w for w in sh.worksheets() if w.title == "Index"), None)
            if ws_idx:
                ws_idx.clear()
            else:
                ws_idx = sh.add_worksheet("Index", 1000, 26)
            set_with_dataframe(ws_idx, idx_df)
            # Write "Last updated" timestamp on Index!F1 (JST label)
            ts_text = f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} JST"
            ws_idx.update(values=[[ts_text]], range_name="F1")
            # Bold the timestamp cell
            service_idx = build("sheets", "v4", credentials=get_google_creds())
            service_idx.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={"requests": [{
                    "repeatCell": {
                        "range": {
                            "sheetId": ws_idx.id,
                            "startRowIndex": 0, "endRowIndex": 1,
                            "startColumnIndex": 5, "endColumnIndex": 6
                        },
                        "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                        "fields": "userEnteredFormat.textFormat.bold"
                    }
                }]}
            ).execute()
            # Auto-resize column F to fit the timestamp
            service_idx.spreadsheets().batchUpdate(
                spreadsheetId=SHEET_ID,
                body={"requests": [{
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": ws_idx.id,
                            "dimension": "COLUMNS",
                            "startIndex": 5,
                            "endIndex": 6
                        }
                    }
                }]}
            ).execute()

            # Transfers tab (raw table)
            ws_transfers = next((w for w in sh.worksheets() if w.title == "Transfers"), None)
            if ws_transfers:
                ws_transfers.clear()
            else:
                ws_transfers = sh.add_worksheet("Transfers", 1000, 26)
            set_with_dataframe(ws_transfers, df)

            # --- Prune stale per-transfer tabs not present in current export ---
            try:
                prune_enabled = os.getenv("GSPREAD_PRUNE_TABS", "1") == "1"
                tab_prefix = os.getenv("GSPREAD_TAB_PREFIX", "#T")
                if prune_enabled:
                    # Titles we will (re)create this run
                    current_titles = set(
                        df["transfer_name"]
                        .dropna()
                        .astype(str)
                        .str.slice(0, 99)
                        .tolist()
                    )
                    existing = {w.title: w for w in sh.worksheets()}
                    to_delete = []
                    for title, w in existing.items():
                        # Only consider transfer-like tabs (default prefix "#T")
                        if title.startswith(tab_prefix) and title not in current_titles:
                            to_delete.append(w)
                    if to_delete:
                        print(f"🧹 Pruning {len(to_delete)} stale transfer tabs not in current window…")
                    deleted = 0
                    for w in to_delete:
                        try:
                            print(f"  🗑️ Deleting stale tab: {w.title}")
                            sh.del_worksheet(w)
                            deleted += 1
                            time.sleep(1.0)  # gentle throttle to avoid 429s
                        except Exception as de:
                            print(f"  ⚠️ Could not delete {w.title}: {de}")
                    if to_delete:
                        print(f"✅ Pruned {deleted} stale tabs.")
            except Exception as e:
                print(f"⚠️ Prune step skipped due to error: {e}")

            # -------- Per-transfer tabs (compact header + items with images) --------
            tab_counter = 0
            for tname, tdf in df.groupby("transfer_name", sort=False):
                sheet_name = str(tname)[:99]
                ws = next((w for w in sh.worksheets() if w.title == sheet_name), None)
                if not ws:
                    ws = sh.add_worksheet(sheet_name, 1000, 12)
                ws.clear()

                # Header meta
                tmeta = tdf.iloc[0]
                status = str(tmeta.get("status") or "")
                origin = str(tmeta.get("origin") or "")
                dest   = str(tmeta.get("destination") or "")
                created = str(tmeta.get("created_utc") or "")
                refname = str(tmeta.get("reference_name") or "")
                note    = str(tmeta.get("note") or "")
                tags    = str(tmeta.get("tags") or "")

                # Totals
                units_to_ship = (tdf["line_shippable_qty"].fillna(0)).sum() if "line_shippable_qty" in tdf else 0
                if not units_to_ship:
                    units_to_ship = (tdf["line_total_qty"].fillna(0)).sum() if "line_total_qty" in tdf else 0
                shipments_received_units = (tdf["received_qty"].drop_duplicates().fillna(0)).max() if "received_qty" in tdf else 0

                # compact header (right-side meta)
                header_rows = [
                    [f"##{tname}", "", "", "", "Date created", created],
                    ["Status:", status, "", "", "Reference name", refname],
                    [],
                    ["Origin", origin, "", "", "Notes", note],
                    ["Destination", dest, "", "", "Tags", tags],
                    ["Units to be shipped", int(units_to_ship), "", "", "", ""],
                    ["Shipments received", int(shipments_received_units or 0), "", "", "", ""],
                    [],
                ]
                ws.update(values=header_rows, range_name="A1")

                # items table (single update; IMAGE() formulas)
                item_cols = ["image_url", "title", "sku", "line_total_qty"]
                for c in item_cols:
                    if c not in tdf.columns:
                        tdf[c] = None
                items_df = tdf[item_cols].copy()
                items_df.rename(columns={"image_url":"Image","title":"Product","sku":"SKU","line_total_qty":"Qty"}, inplace=True)

                def image_formula(u):
                    return f'=IMAGE("{u}", 4, 80, 80)' if isinstance(u, str) and u.startswith("http") else ""
                items_df["Image"] = items_df["Image"].apply(image_formula)
                items_df["Qty"] = pd.to_numeric(items_df["Qty"], errors="coerce")

                table_header = [["Image", "Product", "SKU", "Qty"]]
                table_rows = items_df.fillna("").values.tolist()
                table_values = table_header + table_rows

                start_row_1based = len(header_rows) + 1
                ws.update(values=table_values, range_name=f"A{start_row_1based}", value_input_option="USER_ENTERED")

                # format: reset heights, no freezing, enlarge only product rows
                autosize_transfer_tab(SHEET_ID, ws, header_rows=len(header_rows), nrows=len(table_rows))
                time.sleep(2.8)
                tab_counter += 1
                if tab_counter % 10 == 0:
                    time.sleep(8)

                print(f"✅ Uploaded & formatted transfer tab: {sheet_name} ({len(table_rows)} items)")

            print("✅ All data uploaded to Google Sheets successfully.")
    except Exception as e:
        print(f"⚠️ Google Sheets upload failed: {e}")


if __name__ == "__main__":
    main()
