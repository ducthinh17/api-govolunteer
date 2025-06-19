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
        print("✅ Kết nối đến Google Sheets API thành công.")
    else:
        print(f"❌ LỖI QUAN TRỌNG: File credentials '{SERVICE_ACCOUNT_FILE}' không được tìm thấy.")
except Exception as e:
    print(f"❌ LỖI KHỞI TẠO DỊCH VỤ GOOGLE: {e}")


def _search_sheet_for_all_records(spreadsheet_id: str, record_type: str, full_name: str, citizen_id: str):
    """
    Hàm nội bộ đa năng để tìm tất cả các dòng khớp với người dùng trong một sheet cụ thể.
    """
    print(f"\n--- 🕵️  Bắt đầu tìm kiếm Sheet: {record_type.upper()} ---")
    if not sheet_api:
        print("    -> ❌ Lỗi: Dịch vụ Google Sheets không khả dụng.")
        return {"error": "Dịch vụ Google Sheets không khả dụng."}

    try:
        result = sheet_api.values().get(spreadsheetId=spreadsheet_id, range=SHEET_NAME).execute()
        values = result.get('values', [])
        
        if not values or len(values) < 2:
            print("    -> ⚠️ Cảnh báo: Sheet trống hoặc chỉ có hàng tiêu đề.")
            return []

        print(f"    -> Đã lấy được {len(values)} hàng từ Sheet.")
        headers = values[0]
        print(f"    -> Tiêu đề của Sheet: {headers}")

        try:
            name_index = headers.index('User_Name')
            cccd_index = headers.index('CCCD')
            print(f"    -> Cột 'User_Name' ở vị trí {name_index}, 'CCCD' ở vị trí {cccd_index}.")
        except ValueError as e:
            error_msg = f"Sheet {record_type} (ID: {spreadsheet_id}) thiếu cột tiêu đề bắt buộc: {e}."
            print(f"    -> ❌ Lỗi: {error_msg}")
            return {"error": error_msg}

        found_records = []
        for i, row in enumerate(values[1:], 1): # Bắt đầu từ hàng 1 (sau header)
            if len(row) > max(name_index, cccd_index):
                user_name_in_sheet = row[name_index].strip()
                cccd_in_sheet = row[cccd_index].strip()
                
                if user_name_in_sheet.lower() == full_name.strip().lower() and cccd_in_sheet == citizen_id.strip():
                    print(f"    -> ✅ TÌM THẤY KẾT QUẢ KHỚP tại hàng {i+1} cho người dùng '{full_name}'.")
                    record = {headers[j]: (row[j] if j < len(row) else '') for j in range(len(headers))}
                    record['record_type'] = record_type
                    found_records.append(record)
        
        print(f"--- 🏁 Kết thúc tìm kiếm Sheet {record_type.upper()}. Tìm thấy tổng cộng {len(found_records)} bản ghi. ---")
        return found_records
        
    except HttpError as e:
        error_msg = f"Không thể truy cập Google Sheet. Mã lỗi: {e.resp.status}. Chi tiết: {e.content}"
        print(f"    -> ❌ Lỗi HTTP: {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Lỗi không xác định khi xử lý sheet: {e}"
        print(f"    -> ❌ Lỗi không xác định: {error_msg}")
        return {"error": error_msg}

def find_volunteer_info(full_name: str, citizen_id: str):
    """
    Tìm kiếm trên cả hai sheet và gộp kết quả.
    """
    # Tìm kiếm trong sheet hoạt động
    activity_results = _search_sheet_for_all_records(ACTIVITY_SHEET_ID, 'activity', full_name, citizen_id)
    if isinstance(activity_results, dict) and 'error' in activity_results:
        return activity_results

    # Tìm kiếm trong sheet chứng nhận
    certificate_results = _search_sheet_for_all_records(CERTIFICATE_SHEET_ID, 'certificate', full_name, citizen_id)
    if isinstance(certificate_results, dict) and 'error' in certificate_results:
        return certificate_results

    # Gộp hai danh sách kết quả
    all_records = activity_results + certificate_results
    print(f"\n--- 🔀  GỘP KẾT QUẢ ---")
    print(f"    -> Hoạt động: {len(activity_results)} | Chứng nhận: {len(certificate_results)}")
    print(f"    -> Tổng cộng: {len(all_records)} bản ghi.")
    return all_records