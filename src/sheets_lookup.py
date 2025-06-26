import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

ACTIVITY_SHEET_ID = '1BCJbZqR98jjjqCJq1B2I5p_GuyGi6xwmgxKsRhvxdh0'
CERTIFICATE_SHEET_ID = '1KaLqFwWDNOfHx432E12ScEZ0-BDdhAPbq3Q0BJLK-Fg'
SHEET_NAME = 'Sheet1'

sheet_api = None
try:
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        sheet_api = service.spreadsheets()
    else:
        print(f"LỖI QUAN TRỌNG: File '{SERVICE_ACCOUNT_FILE}' không được tìm thấy ở thư mục gốc của dự án.")
except Exception as e:
    print(f"LỖI KHỞI TẠO DỊCH VỤ GOOGLE: {e}")

def _search_one_sheet(spreadsheet_id: str, full_name: str, citizen_id: str):
    """Hàm nội bộ để tìm kiếm trong một sheet cụ thể."""
    if not sheet_api:
        return {"error": "Dịch vụ Google Sheets không khả dụng do lỗi khởi tạo."}

    try:
        result = sheet_api.values().get(spreadsheetId=spreadsheet_id, range=SHEET_NAME).execute()
        values = result.get('values', [])

        if not values:
            return None

        headers = values[0]
        try:
            name_index = headers.index('User_Name')
            cccd_index = headers.index('CCCD')
        except ValueError:
            return {"error": f"Sheet {spreadsheet_id} thiếu cột 'User_Name' hoặc 'CCCD'."}

        for row in values[1:]:
            if len(row) > max(name_index, cccd_index):
                user_name_in_sheet = row[name_index].strip()
                cccd_in_sheet = row[cccd_index].strip()

                if user_name_in_sheet == full_name.strip() and cccd_in_sheet == citizen_id.strip():
                    return {headers[i]: (row[i] if i < len(row) else '') for i in range(len(headers))}

        return None
    except HttpError as e:
        print(f"Lỗi HTTP khi truy cập sheet {spreadsheet_id}: {e}")
        return {"error": f"Không thể truy cập Google Sheet. Mã lỗi: {e.resp.status}"}
    except Exception as e:
        print(f"Lỗi không xác định khi tìm kiếm sheet {spreadsheet_id}: {e}")
        return {"error": "Lỗi máy chủ nội bộ khi xử lý sheet."}

def find_volunteer_info(full_name: str, citizen_id: str):
    activity_result = _search_one_sheet(ACTIVITY_SHEET_ID, full_name, citizen_id)
    certificate_result = _search_one_sheet(CERTIFICATE_SHEET_ID, full_name, citizen_id)

    return {
        'activity': activity_result,
        'certificate': certificate_result
    }

def update_pdf_requested(full_name: str, citizen_id: str, email: str):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=CERTIFICATE_SHEET_ID, range=SHEET_NAME).execute()
    values = result.get('values', [])
    headers = values[0]

    try:
        name_index = headers.index('User_Name')
        cccd_index = headers.index('CCCD')
        email_index = headers.index('Email')
        requested_index = headers.index('PDF_Requested')
    except ValueError:
        raise Exception("Thiếu cột cần thiết trong Google Sheet.")

    for i, row in enumerate(values[1:], start=2):  # Bắt đầu từ dòng 2
        if len(row) <= max(name_index, cccd_index):
            continue
        if row[name_index].strip() == full_name.strip() and row[cccd_index].strip() == citizen_id.strip():
            # Ghi email nếu cần
            body = {
                "values": [[email, "TRUE"]]
            }
            sheet.values().update(
                spreadsheetId=CERTIFICATE_SHEET_ID,
                range=f"{SHEET_NAME}!{chr(65 + email_index)}{i}:{chr(65 + requested_index)}{i}",
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            return True
    return False