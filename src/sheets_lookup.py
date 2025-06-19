import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = 'credentials.json' 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# --- GIỮ NGUYÊN CÁC BIẾN CỦA BẠN ---
ACTIVITY_SHEET_ID = '1BCJbZqR98jjjqCJq1B2I5p_GuyGi6xwmgxKsRhvxdh0'
CERTIFICATE_SHEET_ID = '17wUDyxg3QyaEwcVyT2bRuhvaVk5IqS40HmZMpSFYY6s'
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


# --- HÀM TÌM KIẾM ĐÃ ĐƯỢC SỬA ĐỔI ĐỂ TÌM TẤT CẢ KẾT QUẢ ---
def _search_sheet_for_all_records(spreadsheet_id: str, record_type: str, full_name: str, citizen_id: str):
    """
    Hàm nội bộ để tìm kiếm TẤT CẢ các dòng khớp trong một sheet và trả về một DANH SÁCH.
    """
    if not sheet_api:
        return {"error": "Dịch vụ Google Sheets không khả dụng do lỗi khởi tạo."}

    try:
        result = sheet_api.values().get(spreadsheetId=spreadsheet_id, range=SHEET_NAME).execute()
        values = result.get('values', [])

        if not values or len(values) < 2:
            return []  # Trả về danh sách rỗng nếu không có dữ liệu

        headers = values[0]
        try:
            name_index = headers.index('User_Name')
            cccd_index = headers.index('CCCD')
        except ValueError as e:
            return {"error": f"Sheet {spreadsheet_id} thiếu cột '{e}'. Vui lòng kiểm tra lại."}

        found_records = [] # DANH SÁCH để lưu tất cả các kết quả
        for row in values[1:]:
            if len(row) > max(name_index, cccd_index):
                user_name_in_sheet = row[name_index].strip()
                cccd_in_sheet = row[cccd_index].strip()
                
                if user_name_in_sheet.lower() == full_name.strip().lower() and cccd_in_sheet == citizen_id.strip():
                    record = {headers[i]: (row[i] if i < len(row) else '') for i in range(len(headers))}
                    record['record_type'] = record_type # Thêm trường để phân biệt loại kết quả
                    found_records.append(record) # Thêm vào danh sách thay vì return ngay
        
        return found_records # Trả về toàn bộ danh sách đã tìm thấy
        
    except HttpError as e:
        print(f"Lỗi HTTP khi truy cập sheet {spreadsheet_id}: {e}")
        return {"error": f"Không thể truy cập Google Sheet. Mã lỗi: {e.resp.status}"}
    except Exception as e:
        print(f"Lỗi không xác định khi tìm kiếm sheet {spreadsheet_id}: {e}")
        return {"error": "Lỗi máy chủ nội bộ khi xử lý sheet."}


# --- SỬA HÀM find_volunteer_info ĐỂ GỌI LOGIC MỚI ---
def find_volunteer_info(full_name: str, citizen_id: str):
    """
    Tìm kiếm trên cả hai sheet Hoạt động và Chứng nhận, sau đó gộp kết quả lại.
    """
    activity_results = _search_sheet_for_all_records(ACTIVITY_SHEET_ID, 'activity', full_name, citizen_id)
    # Nếu có lỗi, trả về ngay lập tức
    if isinstance(activity_results, dict) and 'error' in activity_results:
        return activity_results

    certificate_results = _search_sheet_for_all_records(CERTIFICATE_SHEET_ID, 'certificate', full_name, citizen_id)
    # Nếu có lỗi, trả về ngay lập tức
    if isinstance(certificate_results, dict) and 'error' in certificate_results:
        return certificate_results

    # Gộp 2 danh sách lại làm một và trả về
    return activity_results + certificate_results