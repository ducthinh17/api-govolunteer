from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sheets_lookup import search_all_records_in_sheet

CERTIFICATE_SHEET_ID = '17wUDyxg3QyaEwcVyT2bRuhvaVk5IqS40HmZMpSFYY6s'

router = APIRouter()

class LookupRequest(BaseModel):
    fullName: str
    citizenId: str

@router.post("/find-certificates")
def find_certificates(request: LookupRequest):
    certificates = search_all_records_in_sheet(CERTIFICATE_SHEET_ID, request.fullName, request.citizenId)
    if not certificates:
        raise HTTPException(status_code=404, detail="Không tìm thấy chứng nhận.")
    return {"certificates": certificates}
