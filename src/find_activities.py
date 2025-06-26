from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.sheets_utils import search_all_records_in_sheet

ACTIVITY_SHEET_ID = '1BCJbZqR98jjjqCJq1B2I5p_GuyGi6xwmgxKsRhvxdh0'

router = APIRouter()

class LookupRequest(BaseModel):
    fullName: str
    citizenId: str

@router.post("/find-activities")
def find_activities(request: LookupRequest):
    activities = search_all_records_in_sheet(ACTIVITY_SHEET_ID, request.fullName, request.citizenId)
    if not activities:
        raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động.")
    return {"activities": activities}
