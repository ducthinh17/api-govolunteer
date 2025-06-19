import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Các file scraper của bạn
from scraper import scrape_news as fetch_news_from_source
from scraper import scrape_article_with_requests as fetch_article_from_source
from scraper import (
    scrape_chuong_trinh_chien_dich_du_an,
    scrape_skills,
    scrape_ideas,
    scrape_clubs,
    BASE_URL
)

# *** SỬA LẠI DÒNG NÀY VỀ NHƯ BAN ĐẦU ***
# Dòng import này là đúng với cấu trúc dự án của bạn trên Render.
from src.sheets_lookup import find_volunteer_info

app = FastAPI(title="GoVolunteer Scraper & Lookup API", version="8.2.0") # Tăng phiên bản
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class LookupRequest(BaseModel):
    fullName: str
    citizenId: str

# --- Hệ thống cache và các endpoints cũ không thay đổi ---
cache = {"news_data": None, "last_fetched": 0}
CACHE_DURATION_SECONDS = 1800

@app.get("/", summary="Kiểm tra trạng thái API")
def read_root():
    return {"status": "online", "message": "API GoVolunteer (Final Fixed Version) đã sẵn sàng!"}

@app.get("/news", summary="Lấy danh sách tất cả tin tức")
def get_all_news():
    current_time = time.time()
    if cache["news_data"] and (current_time - cache["last_fetched"] < CACHE_DURATION_SECONDS):
        return cache["news_data"]
    data = fetch_news_from_source()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu từ trang chủ.")
    cache["news_data"] = data
    cache["last_fetched"] = current_time
    return data

@app.get("/clubs", summary="Lấy danh sách các CLB, Đội, Nhóm")
def get_clubs():
    data = scrape_clubs()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu CLB.")
    return data

@app.get("/chuong-trinh-chien-dich-du-an", summary="Lấy danh sách các chương trình")
def get_campaigns():
    data = scrape_chuong_trinh_chien_dich_du_an()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu chương trình.")
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


# --- ENDPOINT TRA CỨU ĐÃ HOÀN THIỆN ---
@app.post("/lookup", summary="Tra cứu Tình nguyện viên từ Google Sheets")
def lookup_volunteer(request: LookupRequest):
    """
    Nhận Họ tên và CCCD, sau đó tìm kiếm TẤT CẢ thông tin tương ứng 
    trong các Google Sheets.
    """
    if not request.fullName or not request.citizenId:
        raise HTTPException(
            status_code=400,
            detail="Vui lòng cung cấp đầy đủ Họ tên và CCCD."
        )

    results = find_volunteer_info(request.fullName, request.citizenId)
    
    activity_list = results.get('activities', [])
    certificate_list = results.get('certificates', [])

    # Chỉ báo lỗi 404 nếu CẢ HAI danh sách đều rỗng
    if not activity_list and not certificate_list:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy thông tin tình nguyện viên phù hợp."
        )
    
    # Trả về kết quả cho frontend, dù rỗng hay không
    return results
