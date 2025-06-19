import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- IMPORT CÁC TÍNH NĂNG CỦA BẠN ---
# Giữ nguyên các import cho tính năng scraper của bạn
from scraper import scrape_news as fetch_news_from_source
from scraper import scrape_article_with_requests as fetch_article_from_source
from scraper import (
    scrape_chuong_trinh_chien_dich_du_an,
    scrape_skills,
    scrape_ideas,
    scrape_clubs,
    BASE_URL
)

# Import hàm tìm kiếm đã được sửa lỗi logic
# File main.py này sẽ gọi hàm find_volunteer_info từ file sheets_lookup.py đã sửa
from src.sheets_lookup import find_volunteer_info

# --- KHỞI TẠO ỨNG DỤNG FASTAPI ---
app = FastAPI(
    title="GoVolunteer API - Full Version",
    version="11.0.0",
    description="API bao gồm các tính năng Scraper và Tra cứu Google Sheets."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production, nên thay "*" bằng domain của frontend
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# --- ĐỊNH NGHĨA MODEL DỮ LIỆU ---
class LookupRequest(BaseModel):
    fullName: str
    citizenId: str

# --- HỆ THỐNG CACHE CHO /news ---
cache = {"news_data": None, "last_fetched": 0}
CACHE_DURATION_SECONDS = 1800  # Cache trong 30 phút

# --- CÁC ENDPOINT SCRAPER (GIỮ NGUYÊN) ---

@app.get("/", summary="Kiểm tra trạng thái API")
def read_root():
    """Cung cấp trạng thái hoạt động của API."""
    return {"status": "online", "message": "API GoVolunteer đã sẵn sàng!"}

@app.get("/news", summary="Lấy danh sách tất cả tin tức")
def get_all_news():
    """Lấy danh sách tin tức theo danh mục từ trang /news. Dữ liệu được cache trong 30 phút."""
    current_time = time.time()
    if cache["news_data"] and (current_time - cache["last_fetched"] < CACHE_DURATION_SECONDS):
        return cache["news_data"]

    data = fetch_news_from_source()
    if not data:
        raise HTTPException(
            status_code=503,
            detail="Không thể lấy dữ liệu từ trang chủ GoVolunteer. Trang web có thể đang bận hoặc không phản hồi."
        )

    cache["news_data"] = data
    cache["last_fetched"] = current_time
    return data

@app.get("/clubs", summary="Lấy danh sách các CLB, Đội, Nhóm")
def get_clubs():
    """Lấy danh sách các CLB, đội, nhóm được phân loại từ trang /clubs."""
    data = scrape_clubs()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu CLB.")
    return data

@app.get("/chuong-trinh-chien-dich-du-an", summary="Lấy danh sách các chương trình, chiến dịch, dự án")
def get_campaigns():
    """Lấy danh sách các chương trình, chiến dịch, dự án được phân loại."""
    data = scrape_chuong_trinh_chien_dich_du_an()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu chương trình, chiến dịch, dự án.")
    return data

@app.get("/skills", summary="Lấy danh sách các bài viết kỹ năng")
def get_skills():
    """Lấy danh sách các bài viết kỹ năng được phân loại."""
    data = scrape_skills()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu kỹ năng.")
    return data

@app.get("/ideas", summary="Lấy danh sách các ý tưởng tình nguyện")
def get_ideas():
    """Lấy danh sách các ý tưởng tình nguyện được phân loại."""
    data = scrape_ideas()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu ý tưởng.")
    return data

@app.get("/article", summary="Lấy nội dung chi tiết của một bài viết")
def get_article_detail(url: str):
    """Lấy nội dung HTML của một bài viết cụ thể dựa trên URL."""
    if not url or not url.startswith(BASE_URL):
        raise HTTPException(status_code=400, detail=f"URL không hợp lệ. Phải bắt đầu bằng {BASE_URL}")

    content = fetch_article_from_source(url)
    if content is None:
        raise HTTPException(
            status_code=503,
            detail="Không thể lấy nội dung bài viết. Trang nguồn có thể đã thay đổi cấu trúc hoặc không phản hồi."
        )
    return {"html_content": content}


# --- ENDPOINT TRA CỨU ĐÃ SỬA LỖI HOÀN CHỈNH ---

@app.post("/lookup", summary="Tra cứu Hoạt động & Chứng nhận Tình nguyện viên")
def lookup_volunteer(request: LookupRequest):
    """
    Nhận Họ tên và CCCD, tìm kiếm trên cả 2 sheet Hoạt động và Chứng nhận,
    và trả về một danh sách GỘP của tất cả các kết quả.
    """
    # Hàm find_volunteer_info bây giờ sẽ trả về một danh sách gộp, hoặc một dict chứa lỗi
    all_records = find_volunteer_info(request.fullName, request.citizenId)
    
    # Kịch bản 1: Có lỗi xảy ra trong quá trình xử lý (vd: không kết nối được Google)
    if isinstance(all_records, dict) and 'error' in all_records:
        error_detail = all_records.get("error")
        # Log lỗi ra console của server để debug
        print(f"LỖI KHI TRA CỨU: {error_detail}")
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail=f"Không thể xử lý yêu cầu do lỗi từ dịch vụ dữ liệu: {error_detail}"
        )

    # Kịch bản 2: Xử lý thành công nhưng không tìm thấy bản ghi nào
    if not all_records:
        raise HTTPException(
            status_code=404,  # Not Found
            detail="Không tìm thấy hoạt động hay chứng nhận nào phù hợp với thông tin đã cung cấp."
        )
    
    # Kịch bản 3: Thành công, trả về dữ liệu đúng cấu trúc frontend mong đợi
    return {"records": all_records}