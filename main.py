from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os, json

app = FastAPI(
    title="GOAT Data API",
    version="1.0.0",
    description="Read-only access to GOAT KPI, leads, and cancellation data."
)

# ---------- ENV VARS ----------
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
KPI_SHEET_ID        = os.environ["KPI_SHEET_ID"]
LEADS_SHEET_ID      = os.environ["LEADS_SHEET_ID"]
CANCEL_SHEET_ID     = os.environ["CANCEL_SHEET_ID"]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

service_account_info = json.loads(SERVICE_ACCOUNT_JSON)
creds = service_account.Credentials.from_service_account_info(
    service_account_info, scopes=SCOPES
)
sheets_service = build("sheets", "v4", credentials=creds)

class RangeRequest(BaseModel):
    range_name: str  # e.g. "Monthly Data!A1:G24"

class SheetValues(BaseModel):
    values: List[List[Any]]

def read_range(spreadsheet_id: str, range_name: str) -> List[List[Any]]:
    try:
        result = (
            sheets_service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "ok", "message": "GOAT Data API running"}

@app.post("/kpi", response_model=SheetValues)
def get_kpi(data: RangeRequest):
    return {"values": read_range(KPI_SHEET_ID, data.range_name)}

@app.post("/leads", response_model=SheetValues)
def get_leads(data: RangeRequest):
    return {"values": read_range(LEADS_SHEET_ID, data.range_name)}

@app.post("/cancellations", response_model=SheetValues)
def get_cancellations(data: RangeRequest):
    return {"values": read_range(CANCEL_SHEET_ID, data.range_name)}
