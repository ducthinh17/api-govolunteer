# src/scraper.py
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://govolunteerhcmc.vn"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
FALLBACK_IMAGE_URL = "https://govolunteerhcmc.vn/wp-content/uploads/2024/02/logo-gv-tron.png" # Link logo mặc định

def scrape_news():
    """
    Scrapes news articles from the GoVolunteerHCMC website.
    """
    try:
        response = requests.get(BASE_URL, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()  # Ném lỗi nếu request không thành công
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return [] # Trả về mảng rỗng nếu có lỗi mạng

    soup = BeautifulSoup(response.text, "lxml")
    sections = []
    
    # Sử dụng CSS selectors tương tự như trong code JS
    for sec in soup.select("section.elementor-section.elementor-top-section"):
        h2 = sec.select_one("h2.elementor-heading-title.elementor-size-default")
        if not h2 or not h2.text.strip():
            continue
        
        category = h2.text.strip()
        articles = []
        
        for post in sec.select("article.elementor-post"):
            a = post.select_one("h3.elementor-post__title a")
            # Bỏ qua nếu không có link hoặc link không thuộc trang web
            if not a or not a.get('href') or not a.get('href').startswith(BASE_URL):
                continue

            title = a.text.strip()
            link = a['href']
            
            img = post.select_one(".elementor-post__thumbnail img")
            image_url = img['src'] if img and img.get('src') else FALLBACK_IMAGE_URL
            
            ex = post.select_one(".elementor-post__excerpt p")
            excerpt = ex.text.strip() if ex else None
            
            articles.append({
                "title": title,
                "link": link,
                "imageUrl": image_url,
                "excerpt": excerpt,
            })
            
        if articles:
            # Loại bỏ các bài viết trùng lặp dựa trên link
            unique_articles = list({article['link']: article for article in articles}.values())
            sections.append({
                "category": category,
                "articles": unique_articles,
            })
            
    # Loại bỏ các section trùng lặp dựa trên category
    unique_sections = list({section['category']: section for section in sections}.values())
    return unique_sections

def scrape_article_content(article_url: str):
    """
    Scrapes the content of a single article.
    """
    try:
        response = requests.get(article_url, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching article content: {e}")
        return "<p>Không thể tải nội dung bài viết.</p>"

    soup = BeautifulSoup(response.text, "lxml")
    content_div = soup.select_one(".elementor-widget-theme-post-content")
    
    return str(content_div) if content_div else "<p>Không tìm thấy nội dung.</p>"