# src/main.py
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Đổi tên các hàm import để mã nguồn rõ ràng hơn
from scraper import scrape_news as fetch_news_from_source
from scraper import scrape_article_content as fetch_article_from_source
from scraper import BASE_URL # Import BASE_URL để sử dụng trong validation

# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI(
    title="GoVolunteer Scraper API",
    description="API chuyên nghiệp để lấy dữ liệu từ GoVolunteerHCMC, có hỗ trợ caching và xử lý lỗi chi tiết.",
    version="3.1.0", 
)

# --- Cấu hình CORS (Cross-Origin Resource Sharing) ---
# Cho phép ứng dụng frontend của bạn (chạy ở domain khác) có thể gọi API này
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong môi trường production, bạn nên giới hạn lại, ví dụ: ["https://your-app.zalo.me"]
    allow_credentials=True,
    allow_methods=["GET"], # Chỉ cho phép phương thức GET
    allow_headers=["*"],
)

# --- Cơ chế Caching ---
# Lưu trữ dữ liệu vào bộ nhớ để giảm thiểu số lần phải scrape lại trang web
cache = { "news_data": None, "last_fetched": 0 }
CACHE_DURATION_SECONDS = 1800 # Cache trong 30 phút

# --- Định nghĩa các API Endpoints ---

@app.get("/", summary="Kiểm tra trạng thái API")
def read_root():
    """
    Endpoint gốc, dùng để kiểm tra xem API có đang hoạt động hay không.
    Các dịch vụ hosting như Render cũng có thể dùng đường dẫn này để health check.
    """
    return {"status": "online", "message": "Chào mừng đến với API GoVolunteer!"}

@app.get("/news", summary="Lấy danh sách tất cả tin tức (có cache)")
def get_all_news():
    """
    Lấy danh sách tất cả các mục và bài viết từ trang chủ.
    Dữ liệu sẽ được cache trong 30 phút để cải thiện hiệu năng.
    """
    current_time = time.time()
    
    # 1. Kiểm tra cache trước
    if cache["news_data"] and (current_time - cache["last_fetched"] < CACHE_DURATION_SECONDS):
        print("✅ Trả về dữ liệu từ cache.")
        return cache["news_data"]
    
    # 2. Nếu cache không hợp lệ, tiến hành scrape
    print("♻️ Cache đã hết hạn. Bắt đầu scrape dữ liệu mới từ trang chủ...")
    data = fetch_news_from_source()
    
    # 3. Xử lý trường hợp scrape thất bại
    if not data:
        # Trả về lỗi 503 (Service Unavailable) để cho biết lỗi không phải do server API
        # mà do dịch vụ bên ngoài (trang GoVolunteer) không phản hồi.
        raise HTTPException(
            status_code=503, 
            detail="Không thể lấy dữ liệu từ trang chủ GoVolunteer. Trang web có thể đang bận hoặc không phản hồi."
        )
    
    # 4. Cập nhật cache với dữ liệu mới
    cache["news_data"] = data
    cache["last_fetched"] = current_time
    print("💾 Đã cập nhật cache với dữ liệu mới.")
    
    return data

@app.get("/article", summary="Lấy nội dung chi tiết của một bài viết")
def get_article_detail(url: str):
    """
    Lấy nội dung HTML của một bài viết cụ thể dựa trên URL được cung cấp.
    Endpoint này không được cache vì mỗi URL là một yêu cầu riêng biệt.
    """
    # 1. Kiểm tra tính hợp lệ của tham số đầu vào
    if not url or not url.startswith(BASE_URL):
        # Trả về lỗi 400 (Bad Request) nếu URL không hợp lệ
        raise HTTPException(status_code=400, detail=f"URL không hợp lệ. URL phải là một chuỗi và bắt đầu bằng '{BASE_URL}'.")
    
    # 2. Gọi hàm để scrape nội dung
    content = fetch_article_from_source(url)
    
    # 3. Xử lý trường hợp scrape thất bại (rất quan trọng)
    if content is None:
        # Trả về lỗi 503 để báo cho frontend biết server đã cố gắng nhưng thất bại
        raise HTTPException(
            status_code=503, 
            detail="Server đã gặp lỗi khi cố gắng lấy nội dung bài viết. Nguyên nhân có thể do hết thời gian chờ hoặc không tìm thấy nội dung trên trang."
        )
        
    # 4. Trả về nội dung nếu thành công
    return {"html_content": content}

