import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Các hằng số không thay đổi ---
SERVICE_ACCOUNT_FILE = 'credentials.json' 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

ACTIVITY_SHEET_ID = '1BCJbZqR98jjjqCJq1B2I5p_GuyGi6xwmgxKsRhvxdh0'
CERTIFICATE_SHEET_ID = '17wUDyxg3QyaEwcVyT2bRuhvaVk5IqS40HmZMpSFYY6s'
SHEET_NAME = 'Sheet1'

# --- Khởi tạo dịch vụ Google Sheets ---
sheet_api = None
try:
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        sheet_api = service.spreadsheets()
    else:
        print(f"LỖI QUAN TRỌNG: File '{SERVICE_ACCOUNT_FILE}' không được tìm thấy.")
except Exception as e:
    print(f"LỖI KHỞI TẠO DỊCH VỤ GOOGLE: {e}")


def _search_all_in_sheet(spreadsheet_id: str, full_name: str, citizen_id: str):
    """
    Hàm nội bộ để tìm kiếm TẤT CẢ các dòng khớp trong một sheet cụ thể.
    """
    if not sheet_api:
        print("Lỗi: Dịch vụ Google Sheets không khả dụng.")
        return []

    try:
        result = sheet_api.values().get(spreadsheetId=spreadsheet_id, range=SHEET_NAME).execute()
        values = result.get('values', [])

        if not values or len(values) < 2:
            return []

        headers = values[0]
        try:
            name_index = headers.index('User_Name')
            cccd_index = headers.index('CCCD')
        except ValueError:
            print(f"Lỗi: Sheet {spreadsheet_id} thiếu cột 'User_Name' hoặc 'CCCD'.")
            return []

        found_records = []
        
        for row in values[1:]:
            if len(row) > max(name_index, cccd_index):
                user_name_in_sheet = row[name_index].strip()
                cccd_in_sheet = row[cccd_index].strip()
                
                if user_name_in_sheet.lower() == full_name.strip().lower() and cccd_in_sheet == citizen_id.strip():
                    record = {headers[i]: (row[i] if i < len(row) else '') for i in range(len(headers))}
                    found_records.append(record)
        
        return found_records
        
    except HttpError as e:
        print(f"Lỗi HTTP khi truy cập sheet {spreadsheet_id}: {e}")
        return []
    except Exception as e:
        print(f"Lỗi không xác định khi tìm kiếm sheet {spreadsheet_id}: {e}")
        return []


def find_volunteer_info(full_name: str, citizen_id: str):
    """
    Tìm thông tin hoạt động và chứng chỉ của tình nguyện viên.
    """
    activity_results = _search_all_in_sheet(ACTIVITY_SHEET_ID, full_name, citizen_id)
    certificate_results = _search_all_in_sheet(CERTIFICATE_SHEET_ID, full_name, citizen_id)

    # Trả về kết quả với key số nhiều để frontend xử lý
    return {
        'activities': activity_results,
        'certificates': certificate_results
    }
