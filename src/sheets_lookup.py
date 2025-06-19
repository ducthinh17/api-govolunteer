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


# *** ĐÃ SỬA LẠI HOÀN TOÀN HÀM NÀY ***
def _search_all_in_sheet(spreadsheet_id: str, full_name: str, citizen_id: str):
    """
    Hàm nội bộ để tìm kiếm TẤT CẢ các dòng khớp trong một sheet cụ thể.
    Nó sẽ trả về một danh sách (list) các bản ghi.
    """
    if not sheet_api:
        print("Lỗi: Dịch vụ Google Sheets không khả dụng.")
        return [] # Trả về danh sách rỗng nếu dịch vụ lỗi

    try:
        result = sheet_api.values().get(spreadsheetId=spreadsheet_id, range=SHEET_NAME).execute()
        values = result.get('values', [])

        if not values or len(values) < 2:
            return []  # Không có dữ liệu hoặc chỉ có dòng tiêu đề

        headers = values[0]
        try:
            name_index = headers.index('User_Name')
            cccd_index = headers.index('CCCD')
        except ValueError:
            print(f"Lỗi: Sheet {spreadsheet_id} thiếu cột 'User_Name' hoặc 'CCCD'.")
            return []

        # Tạo một danh sách rỗng để lưu trữ tất cả các kết quả tìm thấy
        found_records = []
        
        # Lặp qua tất cả các dòng dữ liệu (bỏ qua dòng tiêu đề)
        for row in values[1:]:
            # Đảm bảo dòng có đủ cột để tránh lỗi IndexError
            if len(row) > max(name_index, cccd_index):
                user_name_in_sheet = row[name_index].strip()
                cccd_in_sheet = row[cccd_index].strip()
                
                # So sánh thông tin sau khi đã làm sạch khoảng trắng
                if user_name_in_sheet.lower() == full_name.strip().lower() and cccd_in_sheet == citizen_id.strip():
                    # Nếu khớp, tạo một object và THÊM VÀO DANH SÁCH
                    record = {headers[i]: (row[i] if i < len(row) else '') for i in range(len(headers))}
                    found_records.append(record)
        
        # Trả về TOÀN BỘ DANH SÁCH đã tìm thấy
        return found_records
        
    except HttpError as e:
        print(f"Lỗi HTTP khi truy cập sheet {spreadsheet_id}: {e}")
        return [] # Trả về danh sách rỗng nếu có lỗi
    except Exception as e:
        print(f"Lỗi không xác định khi tìm kiếm sheet {spreadsheet_id}: {e}")
        return []


# *** ĐÃ SỬA LẠI HÀM NÀY ĐỂ TRẢ VỀ ĐÚNG KEY MÀ FRONTEND MONG ĐỢI ***
def find_volunteer_info(full_name: str, citizen_id: str):
    """
    Tìm thông tin hoạt động và chứng chỉ của tình nguyện viên.
    Hàm này trả về một danh sách cho mỗi loại, với key là số nhiều.
    """
    activity_results = _search_all_in_sheet(ACTIVITY_SHEET_ID, full_name, citizen_id)
    certificate_results = _search_all_in_sheet(CERTIFICATE_SHEET_ID, full_name, citizen_id)

    # Đổi key thành "activities" và "certificates" (số nhiều) để khớp với frontend
    return {
        'activities': activity_results,
        'certificates': certificate_results
    }
