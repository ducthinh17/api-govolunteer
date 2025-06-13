import time
import random
import sys
import re
import os
import requests 
from bs4 import BeautifulSoup

# Import các thư viện của Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# --- Cấu hình chung ---
BASE_URL = "https://govolunteerhcmc.vn"
FALLBACK_IMAGE_URL = "https://govolunteerhcmc.vn/wp-content/uploads/2024/02/logo-gv-tron.png"

def get_high_res_image_url(url: str):
    """Loại bỏ các hậu tố kích thước ảnh để lấy ảnh gốc."""
    if not url: return FALLBACK_IMAGE_URL
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.\w+$)', '', url)

# --- PHIÊN BẢN DÙNG `requests` CHO /NEWS (GIỮ NGUYÊN) ---
def scrape_news():
    """Sử dụng `requests` để lấy dữ liệu trang chủ một cách nhanh chóng."""
    print("🚀 Sử dụng `requests` để lấy dữ liệu /news...")
    headers = {
        'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }
    try:
        response = requests.get(BASE_URL, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Lỗi khi dùng requests: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(response.text, "lxml")
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

            img = post.select_one(".elementor-post__thumbnail img")
            image_url = get_high_res_image_url(img['src']) if img and img.get('src') else FALLBACK_IMAGE_URL
            
            ex = post.select_one(".elementor-post__excerpt p")
            excerpt = ex.text.strip() if ex else None
            
            articles.append({
                "title": a.text.strip(),
                "link": a['href'],
                "imageUrl": image_url,
                "excerpt": excerpt,
            })
            
        if articles:
            unique_articles = list({article['link']: article for article in articles}.values())
            sections.append({"category": category, "articles": unique_articles})
            
    print(f"✅ Lấy dữ liệu /news thành công, tìm thấy {len(sections)} mục.")
    return list({section['category']: section for section in sections}.values())


# --- PHIÊN BẢN NÂNG CẤP DÙNG SELENIUM CHO /ARTICLE ---
def setup_selenium_driver():
    """Cấu hình Chrome Driver cho môi trường Render với các bước kiểm tra chi tiết."""
    chrome_options = Options()
    
    # --- BƯỚC KIỂM TRA CHI TIẾT ---
    # 1. Lấy đường dẫn từ biến môi trường mà Render buildpack cài đặt
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN")
    driver_path = os.environ.get("CHROMEDRIVER_PATH")
    
    print("--- KIỂM TRA MÔI TRƯỜNG SELENIUM ---")
    print(f"ℹ️ Biến môi trường GOOGLE_CHROME_BIN: {chrome_bin}")
    print(f"ℹ️ Biến môi trường CHROMEDRIVER_PATH: {driver_path}")
    
    # 2. Kiểm tra xem các biến môi trường có tồn tại không
    if not chrome_bin or not driver_path:
        error_message = "❌ Lỗi Cấu Hình: Không tìm thấy biến môi trường. Vui lòng kiểm tra lại thứ tự và cài đặt Buildpacks trên Render (google-chrome, chromedriver, python)."
        print(error_message, file=sys.stderr)
        return None

    # 3. Kiểm tra xem các tệp có thực sự tồn tại tại đường dẫn đó không
    if not os.path.exists(chrome_bin):
        error_message = f"❌ Lỗi Tệp Tin: Không tìm thấy tệp thực thi Chrome tại: {chrome_bin}"
        print(error_message, file=sys.stderr)
        return None
    if not os.path.exists(driver_path):
        error_message = f"❌ Lỗi Tệp Tin: Không tìm thấy tệp Chromedriver tại: {driver_path}"
        print(error_message, file=sys.stderr)
        return None
    
    print("✅ Môi trường và đường dẫn hợp lệ. Bắt đầu khởi tạo driver...")
    print("-------------------------------------")

    chrome_options.binary_location = chrome_bin
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        print("✅ Selenium Driver đã khởi tạo thành công.")
        return driver
    except Exception as e:
        print(f"❌ Lỗi trong quá trình khởi tạo webdriver.Chrome: {e}", file=sys.stderr)
        return None

def scrape_article_content(article_url: str):
    """Sử dụng Selenium để đảm bảo lấy được nội dung chi tiết của bài viết."""
    driver = setup_selenium_driver()
    if not driver: 
        return None

    try:
        print(f"📄 Đang truy cập bài viết bằng Selenium: {article_url}")
        driver.get(article_url)
        time.sleep(3)
        
        content_div = driver.find_element(by="css selector", value=".elementor-widget-theme-post-content")
        html_content = content_div.get_attribute('outerHTML')
        print("✅ Lấy nội dung bài viết thành công!")
        return html_content
    except Exception as e:
        print(f"❌ Lỗi khi scraping bài viết: {e}", file=sys.stderr)
        return None
    finally:
        if driver:
            driver.quit()
            print("🚪 Đã đóng Selenium Driver.")
