import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- CẬP NHẬT DÒNG IMPORT ---
# Giờ đây chúng ta nhập cả hai hàm từ scraper và đổi tên chúng cho nhất quán
from scraper import scrape_news as fetch_news_from_source
from scraper import scrape_article_with_requests as fetch_article_from_source
from scraper import scrape_chuong_trinh_chien_dich_du_an
from scraper import scrape_skills
from scraper import scrape_ideas
from scraper import BASE_URL

# --- KHỞI TẠO APP VÀ CẤU HÌNH (GIỮ NGUYÊN) ---
app = FastAPI(title="GoVolunteer Scraper API", version="6.0.0") # Tăng phiên bản
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# --- HỆ THỐNG CACHE (GIỮ NGUYÊN) ---
cache = {"news_data": None, "last_fetched": 0}
CACHE_DURATION_SECONDS = 1800  # Cache trong 30 phút

# --- CÁC ENDPOINTS ---
@app.get("/", summary="Kiểm tra trạng thái API")
def read_root():
    """Cung cấp trạng thái hoạt động của API."""
    return {"status": "online", "message": "API GoVolunteer (Optimized Version) đã sẵn sàng!"}

@app.get("/news", summary="Lấy danh sách tất cả tin tức")
def get_all_news():
    """Lấy danh sách tin tức theo danh mục từ trang chủ. Dữ liệu được cache trong 30 phút."""
    current_time = time.time()
    if cache["news_data"] and (current_time - cache["last_fetched"] < CACHE_DURATION_SECONDS):
        print("✅ Trả về dữ liệu /news từ cache.")
        return cache["news_data"]

    print("♻️ Cache /news hết hạn. Bắt đầu scrape dữ liệu mới...")
    data = fetch_news_from_source()
    if not data:
        raise HTTPException(
            status_code=503,
            detail="Không thể lấy dữ liệu từ trang chủ GoVolunteer. Trang web có thể đang bận hoặc không phản hồi."
        )

    cache["news_data"] = data
    cache["last_fetched"] = current_time
    print("💾 Đã cập nhật cache /news.")
    return data

@app.get("/chuong-trinh-chien-dich-du-an", summary="Lấy danh sách các chương trình chiến dịch dự án")
def get_campaigns():
    """Lấy danh sách các chương trình chiến dịch dự án từ trang chủ."""
    data = scrape_chuong_trinh_chien_dich_du_an()
    if not data:
        raise HTTPException(
            status_code=503,
            detail="Không thể lấy dữ liệu chương trình chiến dịch dự án. Trang web có thể đang bận hoặc không phản hồi."
        )
    return data


@app.get("/skills", summary="Lấy danh sách các kỹ năng")
def get_skills():
    """Lấy danh sách các kỹ năng từ trang chủ."""
    data = scrape_skills()
    if not data:
        raise HTTPException(
            status_code=503,
            detail="Không thể lấy dữ liệu kỹ năng. Trang web có thể đang bận hoặc không phản hồi."
        )
    return data


@app.get("/ideas", summary="Lấy danh sách các ý tưởng")
def get_ideas():
    """Lấy danh sách các ý tưởng từ trang chủ."""
    data = scrape_ideas()
    if not data:
        raise HTTPException(
            status_code=503,
            detail="Không thể lấy dữ liệu ý tưởng. Trang web có thể đang bận hoặc không phản hồi."
        )
    return data

@app.get("/article", summary="Lấy nội dung chi tiết của một bài viết")
def get_article_detail(url: str):
    """Lấy nội dung HTML của một bài viết cụ thể dựa trên URL."""
    if not url or not url.startswith(BASE_URL):
        raise HTTPException(status_code=400, detail=f"URL không hợp lệ. Phải bắt đầu bằng {BASE_URL}")

    # Bây giờ hàm này sẽ gọi phiên bản dùng `requests`, nhanh và đáng tin cậy hơn
    content = fetch_article_from_source(url)

    if content is None:
        raise HTTPException(
            status_code=503,
            detail="Không thể lấy nội dung bài viết. Trang nguồn có thể đã thay đổi cấu trúc hoặc không phản hồi."
        )

    return {"html_content": content}
