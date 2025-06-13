
import time
import random
import sys
import re
import os
import requests # Giữ lại requests cho trang news
from bs4 import BeautifulSoup

# Import các thư viện của Selenium chỉ khi cần thiết
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

# --- PHIÊN BẢN CŨ CỦA BẠN (ĐÃ TỐI ƯU) CHO /NEWS ---
def scrape_news():
    """
    Sử dụng `requests` để lấy dữ liệu trang chủ một cách nhanh chóng.
    """
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
    """Cấu hình Chrome Driver cho môi trường Render."""
    chrome_options = Options()
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN", "/app/.apt/usr/bin/google-chrome")
    driver_path = os.environ.get("CHROMEDRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    
    chrome_options.binary_location = chrome_bin
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    print("🚀 Đang khởi tạo Selenium Driver cho tác vụ /article...")
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        print("✅ Selenium Driver đã sẵn sàng.")
        return driver
    except Exception as e:
        print(f"❌ Lỗi khởi tạo Selenium Driver: {e}", file=sys.stderr)
        return None

def scrape_article_content(article_url: str):
    """
    Sử dụng Selenium để đảm bảo lấy được nội dung chi tiết của bài viết.
    """
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
