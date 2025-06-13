
import time
import random
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://govolunteerhcmc.vn"
FALLBACK_IMAGE_URL = "https://govolunteerhcmc.vn/wp-content/uploads/2024/02/logo-gv-tron.png"

def setup_driver():
    """
    Cấu hình và khởi tạo một Chrome driver ở chế độ headless.
    Chế độ này rất quan trọng để chạy trên server không có giao diện đồ họa.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f'user-agent={random.choice(["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"])}')
    
    print("🚀 Đang khởi tạo Selenium Driver...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(45) # Tăng thời gian chờ tải trang lên 45 giây
        print("✅ Selenium Driver đã sẵn sàng.")
        return driver
    except Exception as e:
        print(f"❌ LỖI NGHIÊM TRỌNG KHI KHỞI TẠO DRIVER: {e}", file=sys.stderr)
        return None

def get_high_res_image_url(url: str):
    """
    Loại bỏ các hậu tố kích thước của WordPress (ví dụ: "-300x192")
    khỏi URL hình ảnh để lấy phiên bản có độ phân giải cao nhất.
    """
    if not url: return FALLBACK_IMAGE_URL
    return url.replace(/-\d{2,4}x\d{2,4}(?=\.\w+$)/, "")

def scrape_news():
    """
    Scrapes news articles from the GoVolunteerHCMC main page using Selenium.
    """
    driver = setup_driver()
    if not driver:
        return None

    try:
        print(f"🌍 Đang truy cập trang chủ: {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(5)  # Đợi JavaScript tải
        
        soup = BeautifulSoup(driver.page_source, "lxml")
        sections = []
        
        for sec in soup.select("section.elementor-section.elementor-top-section"):
            h2 = sec.select_one("h2.elementor-heading-title.elementor-size-default")
            if not h2 or not h2.text.strip():
                continue
            
            category = h2.text.strip()
            articles = []
            
            for post in sec.select("article.elementor-post"):
                a = post.select_one("h3.elementor-post__title a")
                if not a or not a.get('href', '').startswith(BASE_URL):
                    continue

                title = a.text.strip()
                link = a['href']
                
                img = post.select_one(".elementor-post__thumbnail img")
                image_url = get_high_res_image_url(img['src']) if img and img.get('src') else FALLBACK_IMAGE_URL
                
                ex = post.select_one(".elementor-post__excerpt p")
                excerpt = ex.text.strip() if ex else None
                
                articles.append({
                    "title": title,
                    "link": link,
                    "imageUrl": image_url,
                    "excerpt": excerpt,
                })
            
            if articles:
                unique_articles = list({article['link']: article for article in articles}.values())
                sections.append({
                    "category": category,
                    "articles": unique_articles,
                })
        
        print(f"✅ Lấy dữ liệu trang chủ thành công, tìm thấy {len(sections)} mục.")
        return list({section['category']: section for section in sections}.values())

    except Exception as e:
        print(f"❌ Lỗi khi scraping trang chủ: {e}", file=sys.stderr)
        return None
    finally:
        driver.quit()
        print("🚪 Đã đóng Selenium Driver của tác vụ /news.")

def scrape_article_content(article_url: str):
    """
    Scrapes the content of a single article using Selenium.
    """
    driver = setup_driver()
    if not driver:
        return None

    try:
        print(f"📄 Đang truy cập bài viết: {article_url}")
        driver.get(article_url)
        time.sleep(3)
        
        print("🔍 Đang tìm kiếm thẻ div nội dung '.elementor-widget-theme-post-content'...")
        content_div = driver.find_element(by="css selector", value=".elementor-widget-theme-post-content")
        
        html_content = content_div.get_attribute('outerHTML')
        print("✅ TÌM THẤY VÀ LẤY NỘI DUNG THÀNH CÔNG!")
        return html_content
            
    except TimeoutException:
        print(f"❌ LỖI TIMEOUT: Trang web mất quá nhiều thời gian để tải. ({article_url})", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ LỖI KHÔNG TÌM THẤY ELEMENT hoặc lỗi khác: {e}", file=sys.stderr)
        return None
    finally:
        driver.quit()
        print("🚪 Đóng Selenium Driver của tác vụ /article.")

# ----------------------------------------------------------------------
# FILE: main.py (PHIÊN BẢN CHUYÊN NGHIỆP VÀ HOÀN CHỈNH)
#
# Cập nhật file này để trả về thông báo lỗi chi tiết hơn và rõ ràng hơn.
# ----------------------------------------------------------------------

import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# Đổi tên import để dễ phân biệt
from scraper import scrape_news as fetch_news_from_source
from scraper import scrape_article_content as fetch_article_from_source

app = FastAPI(
    title="GoVolunteer Scraper API",
    description="API chuyên nghiệp để lấy dữ liệu từ GoVolunteerHCMC.",
    version="3.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["GET"], allow_headers=["*"])

cache = { "news_data": None, "last_fetched": 0 }
CACHE_DURATION_SECONDS = 1800 # Cache trong 30 phút

@app.get("/", summary="Kiểm tra trạng thái API")
def read_root():
    return {"status": "online", "message": "Chào mừng đến với API GoVolunteer!"}

@app.get("/news", summary="Lấy danh sách tất cả tin tức (có cache)")
def get_all_news():
    current_time = time.time()
    if cache["news_data"] and (current_time - cache["last_fetched"] < CACHE_DURATION_SECONDS):
        print("✅ Trả về dữ liệu từ cache.")
        return cache["news_data"]
    
    print("♻️ Cache đã hết hạn. Bắt đầu scrape dữ liệu mới...")
    data = fetch_news_from_source()
    
    if not data:
        raise HTTPException(status_code=503, detail="Không thể lấy dữ liệu từ trang chủ GoVolunteer. Server có thể đang bận hoặc trang web không phản hồi.")
    
    cache["news_data"] = data
    cache["last_fetched"] = current_time
    print("💾 Đã cập nhật cache với dữ liệu mới.")
    return data

@app.get("/article", summary="Lấy nội dung chi tiết của một bài viết")
def get_article_detail(url: str):
    if not url or not url.startswith(BASE_URL):
        raise HTTPException(status_code=400, detail=f"URL không hợp lệ.")
    
    content = fetch_article_from_source(url)
    
    if content is None:
        raise HTTPException(status_code=503, detail="Server đã gặp lỗi khi cố gắng lấy nội dung bài viết. Nguyên nhân có thể do hết thời gian chờ hoặc không tìm thấy nội dung trên trang.")
        
    return {"html_content": content}
