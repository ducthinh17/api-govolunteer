import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from scraper import scrape_news as fetch_news_from_source
from scraper import scrape_article_content as fetch_article_from_source
from scraper import BASE_URL

app = FastAPI(title="GoVolunteer Scraper API", version="5.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["GET"], allow_headers=["*"])

cache = { "news_data": None, "last_fetched": 0 }
CACHE_DURATION_SECONDS = 1800

@app.get("/", summary="Kiểm tra trạng thái API")
def read_root():
    return {"status": "online", "message": "API GoVolunteer đã sẵn sàng!"}

@app.get("/news", summary="Lấy danh sách tất cả tin tức")
def get_all_news():
    current_time = time.time()
    if cache["news_data"] and (current_time - cache["last_fetched"] < CACHE_DURATION_SECONDS):
        print("✅ Trả về dữ liệu từ cache.")
        return cache["news_data"]
    
    print("♻️ Cache hết hạn. Bắt đầu scrape dữ liệu mới...")
    data = fetch_news_from_source()
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu từ trang chủ GoVolunteer. Server có thể đang bận hoặc trang web không phản hồi.")
    
    cache["news_data"] = data
    cache["last_fetched"] = current_time
    print("💾 Đã cập nhật cache.")
    return data

@app.get("/article", summary="Lấy nội dung chi tiết của một bài viết")
def get_article_detail(url: str):
    if not url or not url.startswith(BASE_URL):
        raise HTTPException(status_code=400, detail=f"URL không hợp lệ.")
    
    content = fetch_article_from_source(url)
    if content is None:
        raise HTTPException(status_code=503, detail="Server đã gặp lỗi khi cố gắng lấy nội dung bài viết. Vui lòng kiểm tra log trên Render.")
        
    return {"html_content": content}
