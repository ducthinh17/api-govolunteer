import time
import random
import sys
import re
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

BASE_URL = "https://govolunteerhcmc.vn"
FALLBACK_IMAGE_URL = "https://govolunteerhcmc.vn/wp-content/uploads/2024/02/logo-gv-tron.png"

def setup_driver():
    """Cấu hình Chrome Driver một cách đáng tin cậy cho môi trường Render."""
    chrome_options = Options()
    
    # --- SỬA LỖI QUAN TRỌNG NHẤT ---
    # Nếu không tìm thấy biến môi trường, hãy sử dụng đường dẫn mặc định
    # mà buildpack thường cài đặt. Điều này làm cho code ổn định hơn.
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN", "/app/.apt/usr/bin/google-chrome")
    driver_path = os.environ.get("CHROMEDRIVER_PATH", "/app/.chromedriver/bin/chromedriver")
    
    print(f"ℹ️ Sử dụng Chrome tại: {chrome_bin}")
    print(f"ℹ️ Sử dụng Chromedriver tại: {driver_path}")
    
    chrome_options.binary_location = chrome_bin
    
    # Các tùy chọn bắt buộc để chạy trong môi trường container (server)
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    print("🚀 Đang khởi tạo Selenium Driver với đường dẫn đã xác định...")
    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        print("✅ Selenium Driver đã sẵn sàng.")
        return driver
    except Exception as e:
        print(f"❌ LỖI KHỞI TẠO DRIVER: {e}", file=sys.stderr)
        return None

def get_high_res_image_url(url: str):
    if not url: return FALLBACK_IMAGE_URL
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.\w+$)', '', url)

def scrape_news():
    driver = setup_driver()
    if not driver: return None

    try:
        driver.get(BASE_URL)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "lxml")
        sections = []
        for sec in soup.select("section.elementor-section.elementor-top-section"):
            h2 = sec.select_one("h2.elementor-heading-title.elementor-size-default")
            if not h2 or not h2.text.strip(): continue
            category = h2.text.strip()
            articles = []
            for post in sec.select("article.elementor-post"):
                a = post.select_one("h3.elementor-post__title a")
                if not a or not a.get('href', '').startswith(BASE_URL): continue
                img = post.select_one(".elementor-post__thumbnail img")
                image_url = get_high_res_image_url(img['src']) if img and img.get('src') else FALLBACK_IMAGE_URL
                ex = post.select_one(".elementor-post__excerpt p")
                excerpt = ex.text.strip() if ex else None
                articles.append({"title": a.text.strip(), "link": a['href'], "imageUrl": image_url, "excerpt": excerpt})
            if articles:
                sections.append({"category": category, "articles": list({article['link']: article for article in articles}.values())})
        print(f"✅ Lấy dữ liệu trang chủ thành công, tìm thấy {len(sections)} mục.")
        return list({section['category']: section for section in sections}.values())
    except Exception as e:
        print(f"❌ Lỗi khi scraping trang chủ: {e}", file=sys.stderr)
        return None
    finally:
        if driver: driver.quit()

def scrape_article_content(article_url: str):
    driver = setup_driver()
    if not driver: return None
    try:
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
        if driver: driver.quit()
