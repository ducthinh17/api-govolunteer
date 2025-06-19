# main.py

import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import các tính năng scraper của bạn
from scraper import scrape_news as fetch_news_from_source
from scraper import scrape_article_with_requests as fetch_article_from_source
from scraper import (
    scrape_chuong_trinh_chien_dich_du_an,
    scrape_skills,
    scrape_ideas,
    scrape_clubs,
    BASE_URL
)

# Import hàm tìm kiếm chính từ file logic
from src.sheets_lookup import find_volunteer_info

# --- KHỞI TẠO ỨNG DỤNG FASTAPI ---
app = FastAPI(
    title="GoVolunteer API - Final Version",
    version="12.0.0",
    description="API bao gồm các tính năng Scraper và Tra cứu Google Sheets."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
CACHE_DURATION_SECONDS = 1800

# --- CÁC ENDPOINT SCRAPER (GIỮ NGUYÊN) ---

@app.get("/", summary="Kiểm tra trạng thái API")
def read_root():
    return {"status": "online", "message": "API GoVolunteer đã sẵn sàng!"}

@app.get("/news", summary="Lấy danh sách tất cả tin tức")
def get_all_news():
    current_time = time.time()
    if cache["news_data"] and (current_time - cache["last_fetched"] < CACHE_DURATION_SECONDS):
        return cache["news_data"]
    data = fetch_news_from_source()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu tin tức.")
    cache["news_data"] = data
    cache["last_fetched"] = current_time
    return data

@app.get("/clubs", summary="Lấy danh sách các CLB, Đội, Nhóm")
def get_clubs():
    data = scrape_clubs()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu CLB.")
    return data

@app.get("/chuong-trinh-chien-dich-du-an", summary="Lấy danh sách các chương trình, chiến dịch, dự án")
def get_campaigns():
    data = scrape_chuong_trinh_chien_dich_du_an()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu chương trình, chiến dịch, dự án.")
    return data

@app.get("/skills", summary="Lấy danh sách các bài viết kỹ năng")
def get_skills():
    data = scrape_skills()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu kỹ năng.")
    return data

@app.get("/ideas", summary="Lấy danh sách các ý tưởng tình nguyện")
def get_ideas():
    data = scrape_ideas()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu ý tưởng.")
    return data

@app.get("/article", summary="Lấy nội dung chi tiết của một bài viết")
def get_article_detail(url: str):
    if not url or not url.startswith(BASE_URL):
        raise HTTPException(status_code=400, detail=f"URL không hợp lệ.")
    content = fetch_article_from_source(url)
    if content is None:
        raise HTTPException(status_code=503, detail="Không thể lấy nội dung bài viết.")
    return {"html_content": content}


# --- ENDPOINT TRA CỨU HOÀN CHỈNH ---

@app.post("/lookup", summary="Tra cứu Hoạt động & Chứng nhận Tình nguyện viên")
def lookup_volunteer(request: LookupRequest):
    """
    Nhận Họ tên và CCCD, tìm kiếm trên cả 2 sheet và trả về danh sách gộp.
    """
    all_records = find_volunteer_info(request.fullName, request.citizenId)
    
    if isinstance(all_records, dict) and 'error' in all_records:
        error_detail = all_records.get("error")
        print(f"LỖI KHI TRA CỨU: {error_detail}")
        raise HTTPException(status_code=503, detail=f"Lỗi từ dịch vụ dữ liệu: {error_detail}")

    if not all_records:
        raise HTTPException(status_code=404, detail="Không tìm thấy hoạt động hay chứng nhận nào phù hợp.")
    
    return {"records": all_records}