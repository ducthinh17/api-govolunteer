import requests
from bs4 import BeautifulSoup
import re
import sys

# --- Cấu hình chung ---
BASE_URL = "https://govolunteerhcmc.vn"
FALLBACK_IMAGE_URL = "https://govolunteerhcmc.vn/wp-content/uploads/2024/02/logo-gv-tron.png"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Referer': 'https://www.google.com/'
}

def get_high_res_image_url(url: str):
    """Loại bỏ các hậu tố kích thước ảnh (-150x150, -300x200, v.v.) để lấy ảnh gốc chất lượng cao."""
    if not url:
        return FALLBACK_IMAGE_URL
    # Biểu thức chính quy này sẽ tìm và thay thế các chuỗi như "-123x456" ở cuối tên file (trước phần mở rộng)
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.\w+$)', '', url)

# --- PHIÊN BẢN `requests` CHO /NEWS (ĐÃ TỐI ƯU) ---
def scrape_news():
    """
    Sử dụng `requests` để lấy dữ liệu trang chủ một cách nhanh chóng.
    Đã cập nhật logic để lấy cả section không có tiêu đề (dành cho Swiper/Bảng tin).
    """
    print("🚀 Sử dụng `requests` để lấy dữ liệu /news...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Lỗi khi dùng requests cho /news: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(response.text, "lxml")
    sections = []

    for sec in soup.select("section.elementor-section.elementor-top-section"):
        # BƯỚC 1: Tìm tất cả bài viết trong section trước
        articles = []
        for post in sec.select("article.elementor-post"):
            a_tag = post.select_one("h3.elementor-post__title a")
            if not a_tag or not a_tag.get('href', '').startswith(BASE_URL):
                continue

            img_tag = post.select_one(".elementor-post__thumbnail img")
            image_url = get_high_res_image_url(img_tag.get('src')) if img_tag and img_tag.get('src') else FALLBACK_IMAGE_URL

            excerpt_tag = post.select_one(".elementor-post__excerpt p")
            excerpt = excerpt_tag.text.strip() if excerpt_tag else None

            articles.append({
                "title": a_tag.text.strip(),
                "link": a_tag['href'],
                "imageUrl": image_url,
                "excerpt": excerpt,
            })

        # BƯỚC 2: CHỈ xử lý nếu section này thực sự có bài viết
        if not articles:
            continue

        # BƯỚC 3: Bây giờ mới tìm tiêu đề. Nếu không có, gán tên mặc định.
        h2 = sec.select_one("h2.elementor-heading-title.elementor-size-default")
        
        # ----- ĐÂY LÀ THAY ĐỔI QUAN TRỌNG NHẤT -----
        # Logic này đảm bảo section không có tiêu đề (như slider) vẫn được lấy
        # và được đặt tên là "BẢNG TIN TÌNH NGUYỆN" để frontend xử lý.
        category_name = h2.text.strip() if h2 and h2.text.strip() else "BẢNG TIN TÌNH NGUYỆN"
        
        unique_articles = list({article['link']: article for article in articles}.values())
        sections.append({"category": category_name, "articles": unique_articles})

    print(f"✅ Lấy dữ liệu /news thành công, tìm thấy {len(sections)} mục.")
    
    # Loại bỏ các category trùng lặp (nếu có), giữ lại bản có dữ liệu
    final_sections = list({section['category']: section for section in sections}.values())
    
    return final_sections


# --- PHIÊN BẢN `requests` CHO /ARTICLE ---
def scrape_article_with_requests(article_url: str):
    """Sử dụng requests và BeautifulSoup để lấy nội dung bài viết một cách hiệu quả."""
    print(f"🚀 Sử dụng `requests` để lấy dữ liệu bài viết: {article_url}")
    try:
        response = requests.get(article_url, headers=HEADERS, timeout=20)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Selector này nhắm đến container bên trong widget nội dung của Elementor
        # để lấy chính xác phần thân bài viết
        content_div = soup.select_one(".elementor-widget-theme-post-content .elementor-widget-container")

        if not content_div:
            print("❌ Không tìm thấy thẻ div chứa nội dung (.elementor-widget-theme-post-content).", file=sys.stderr)
            return None

        html_content = str(content_div)
        print("✅ Lấy nội dung bài viết thành công!")
        return html_content

    except requests.RequestException as e:
        print(f"❌ Lỗi khi dùng requests cho bài viết: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ Lỗi không xác định khi xử lý bài viết: {e}", file=sys.stderr)
        return None
# --- Placeholder functions for new routes ---

def scrape_chuong_trinh_chien_dich_du_an():
    print("Scraping chuong-trinh-chien-dich-du-an")
    return []

def scrape_skills():
    print("Scraping /skills")
    return []

def scrape_ideas():
    print("Scraping /ideas")
    return []
