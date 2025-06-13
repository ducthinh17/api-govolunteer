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
    """Loại bỏ các hậu tố kích thước ảnh để lấy ảnh gốc."""
    if not url:
        return FALLBACK_IMAGE_URL
    return re.sub(r'-\d{2,4}x\d{2,4}(?=\.\w+$)', '', url)

# --- PHIÊN BẢN DÙNG `requests` CHO /NEWS (GIỮ NGUYÊN) ---
def scrape_news():
    """Sử dụng `requests` để lấy dữ liệu trang chủ một cách nhanh chóng."""
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
        h2 = sec.select_one("h2.elementor-heading-title.elementor-size-default")
        if not h2 or not h2.text.strip():
            continue

        category = h2.text.strip()
        articles = []

        for post in sec.select("article.elementor-post"):
            a_tag = post.select_one("h3.elementor-post__title a")
            if not a_tag or not a_tag.get('href', '').startswith(BASE_URL):
                continue

            img_tag = post.select_one(".elementor-post__thumbnail img")
            image_url = get_high_res_image_url(img_tag['src']) if img_tag and img_tag.get('src') else FALLBACK_IMAGE_URL

            excerpt_tag = post.select_one(".elementor-post__excerpt p")
            excerpt = excerpt_tag.text.strip() if excerpt_tag else None

            articles.append({
                "title": a_tag.text.strip(),
                "link": a_tag['href'],
                "imageUrl": image_url,
                "excerpt": excerpt,
            })

        if articles:
            # Loại bỏ các bài viết trùng lặp dựa trên link
            unique_articles = list({article['link']: article for article in articles}.values())
            sections.append({"category": category, "articles": unique_articles})

    print(f"✅ Lấy dữ liệu /news thành công, tìm thấy {len(sections)} mục.")
    # Loại bỏ các category trùng lặp
    return list({section['category']: section for section in sections}.values())


# --- PHIÊN BẢN MỚI DÙNG `requests` CHO /ARTICLE ---
def scrape_article_with_requests(article_url: str):
    """Sử dụng requests và BeautifulSoup để lấy nội dung bài viết một cách hiệu quả."""
    print(f"🚀 Sử dụng `requests` để lấy dữ liệu bài viết: {article_url}")
    try:
        response = requests.get(article_url, headers=HEADERS, timeout=20)
        response.raise_for_status()  # Báo lỗi nếu status code là 4xx hoặc 5xx

        soup = BeautifulSoup(response.text, "lxml")

        # Tìm chính xác div chứa nội dung bài viết
        # Selector này nhắm đến container bên trong widget nội dung của Elementor
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

