import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- CẤU HÌNH ---
SERVICE_ACCOUNT_FILE = 'credentials.json' 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

ACTIVITY_SHEET_ID = '1BCJbZqR98jjjqCJq1B2I5p_GuyGi6xwmgxKsRhvxdh0'
CERTIFICATE_SHEET_ID = '17wUDyxg3QyaEwcVyT2bRuhvaVk5IqS40HmZMpSFYY6s'
SHEET_NAME = 'Sheet1'  

# --- KHỞI TẠO KẾT NỐI ---
sheet_api = None
try:
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        sheet_api = service.spreadsheets()
    else:
        # Lỗi này sẽ được hiển thị trên console của server khi khởi động
        print(f"LỖI QUAN TRỌNG: File credentials '{SERVICE_ACCOUNT_FILE}' không được tìm thấy.")
except Exception as e:
    print(f"LỖI KHỞI TẠO DỊCH VỤ GOOGLE: {e}")


def _search_sheet_for_all_records(spreadsheet_id: str, record_type: str, full_name: str, citizen_id: str):
    """
    Hàm nội bộ đa năng để tìm tất cả các dòng khớp với người dùng trong một sheet cụ thể.
    """
    if not sheet_api:
        return {"error": "Dịch vụ Google Sheets không khả dụng do lỗi khởi tạo."}

    try:
        result = sheet_api.values().get(spreadsheetId=spreadsheet_id, range=SHEET_NAME).execute()
        values = result.get('values', [])
        
        if not values or len(values) < 2:
            return [] # Trả về danh sách rỗng nếu sheet trống

        headers = values[0]
        try:
            name_index = headers.index('User_Name')
            cccd_index = headers.index('CCCD')
        except ValueError as e:
            return {"error": f"Sheet (ID: {spreadsheet_id}) thiếu cột tiêu đề bắt buộc: {e}."}

        found_records = []
        # Chuẩn bị dữ liệu đầu vào để so sánh
        input_name_lower = full_name.strip().lower()
        input_cccd = citizen_id.strip()

        for row in values[1:]:
            if len(row) > max(name_index, cccd_index):
                # Lấy dữ liệu từ sheet và chuẩn hóa (bỏ khoảng trắng, viết thường)
                user_name_in_sheet = row[name_index].strip().lower()
                cccd_in_sheet = row[cccd_index].strip()
                
                # So sánh dữ liệu đã được chuẩn hóa
                if user_name_in_sheet == input_name_lower and cccd_in_sheet == input_cccd:
                    record = {headers[i]: (row[i] if i < len(row) else '') for i in range(len(headers))}
                    record['record_type'] = record_type # Gán loại để frontend phân biệt
                    found_records.append(record)
        
        return found_records
        
    except HttpError as e:
        return {"error": f"Không thể truy cập Google Sheet. Lỗi HTTP: {e.resp.status}"}
    except Exception as e:
        return {"error": f"Lỗi không xác định khi xử lý sheet {spreadsheet_id}: {e}"}


def find_volunteer_info(full_name: str, citizen_id: str):
    """
    Tìm kiếm trên cả hai sheet Hoạt động và Chứng nhận, sau đó gộp kết quả lại.
    """
    activity_results = _search_sheet_for_all_records(ACTIVITY_SHEET_ID, 'activity', full_name, citizen_id)
    if isinstance(activity_results, dict) and 'error' in activity_results:
        return activity_results

    certificate_results = _search_sheet_for_all_records(CERTIFICATE_SHEET_ID, 'certificate', full_name, citizen_id)
    if isinstance(certificate_results, dict) and 'error' in certificate_results:
        return certificate_results

    # Gộp hai danh sách kết quả lại thành một và trả về
    return activity_results + certificate_results