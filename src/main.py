# src/main.py
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from scraper import scrape_news, scrape_article_content

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Caching đơn giản ===
# Lưu trữ dữ liệu và thời điểm lấy dữ liệu
cache = {
    "data": None,
    "timestamp": 0
}
CACHE_DURATION = 1800  # 30 phút (tính bằng giây)

@app.get("/news", summary="Lấy danh sách tất cả các bài viết đã được phân loại")
def get_all_news():
    """
    Endpoint chính để lấy toàn bộ dữ liệu tin tức.
    Sử dụng cơ chế cache để không phải scrape lại trang web liên tục.
    """
    current_time = time.time()
    # Nếu cache còn hiệu lực, trả về dữ liệu từ cache
    if cache["data"] and (current_time - cache["timestamp"] < CACHE_DURATION):
        return cache["data"]

    # Nếu cache hết hạn, tiến hành scrape lại
    data = scrape_news()
    if not data:
        raise HTTPException(status_code=500, detail="Không thể lấy dữ liệu từ GoVolunteer.")
    
    # Cập nhật cache
    cache["data"] = data
    cache["timestamp"] = current_time
    
    return data

@app.get("/article", summary="Lấy nội dung chi tiết của một bài viết")
def get_article_detail(url: str):
    """
    Endpoint để lấy nội dung của một bài viết cụ thể dựa trên URL.
    """
    if not url or not url.startswith("https://govolunteerhcmc.vn"):
        raise HTTPException(status_code=400, detail="URL không hợp lệ.")
    
    content = scrape_article_content(url)
    return {"html": content}