import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://thuvienphapluat.vn/phap-luat/"
params = [
    'doanh-nghiep','lao-dong-tien-luong','bat-dong-san','vi-pham-hanh-chinh',
    'bao-hiem','quyen-dan-su','thuong-mai','thue-phi-le-phi',
    'xuat-nhap-khau','thu-tuc-to-tung','cong-nghe-thong-tin','giao-thong-van-tai'
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    # "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://thuvienphapluat.vn/",
    "Connection": "keep-alive",
}

TODAY = datetime.now().strftime("%d/%m/%Y")

OUTPUT_FOLDER = "urls_folder"
GLOBAL_FILE = "all_urls.txt"
DATE_FILE = "last_date.txt"

# Shared session to persist cookies across requests
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


def reset_if_new_day():
    ensure_output_folder()

    date_path = os.path.join(OUTPUT_FOLDER, DATE_FILE)
    all_url_path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)

    if os.path.exists(date_path):
        with open(date_path, "r", encoding="utf-8") as f:
            last_date = f.read().strip()
    else:
        last_date = None

    if last_date != TODAY:
        print("🔄 New day detected → reset all_urls.txt")
        if os.path.exists(all_url_path):
            os.remove(all_url_path)
        with open(date_path, "w", encoding="utf-8") as f:
            f.write(TODAY)


def load_all_urls():
    path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_to_global(new_urls):
    path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)
    with open(path, "a", encoding="utf-8") as f:
        for url in new_urls:
            f.write(url + "\n")


def save_new_urls(param, new_urls):
    filename = f"urls-{param}.txt"
    path = os.path.join(OUTPUT_FOLDER, filename)
    with open(path, "w", encoding="utf-8") as f:
        for url in new_urls:
            f.write(url + "\n")


def crawl_page(url):
    try:
        res = SESSION.get(url, timeout=15)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"  ❌ Error fetching {url}: {e}")
        return None


def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    valid_links = set()
    for article in soup.select("article.tvpl-field-row"):
        # Get date from .tvpl-field-row-meta
        meta = article.select_one(".tvpl-field-row-meta")
        if not meta:
            continue

        date_text = meta.get_text(strip=True)  # e.g. "19:10 | 16/06/2026"
        if TODAY not in date_text:
            continue

        # Get the article link (title link, not thumbnail)
        a = article.select_one("a.tvpl-field-row-title")
        if not a:
            # fallback: any first <a> with href
            a = article.find("a", href=True)
        if not a:
            continue

        href = a.get("href", "")
        if not href:
            continue

        if not href.startswith("http"):
            href = "https://thuvienphapluat.vn" + href

        valid_links.add(href)

    return valid_links


def warm_up_session():
    """Visit homepage first to get cookies, reducing chance of 403."""
    try:
        print("🌐 Warming up session via homepage...")
        SESSION.get("https://thuvienphapluat.vn/", timeout=15)
        print("  ✅ Session ready")
    except Exception as e:
        print(f"  ⚠️ Warm-up failed (continuing anyway): {e}")


def crawl_all():
    crawled_before = load_all_urls()
    print(f"Already crawled today: {len(crawled_before)} URLs")

    for p in params:
        url = BASE_URL + p
        print(f"\nCrawling: {url}")

        html = crawl_page(url)
        if not html:
            save_new_urls(p, [])
            continue

        links = extract_links(html)
        print(f"  → Found {len(links)} links today")

        new_links = links - crawled_before
        print(f"  → New links: {len(new_links)}")

        save_new_urls(p, new_links)

        if new_links:
            save_to_global(new_links)
            crawled_before.update(new_links)


if __name__ == "__main__":
    print("Today date filter:", TODAY)
    reset_if_new_day()
    warm_up_session()   # 🔑 get cookies before crawling
    crawl_all()
    print("\nDONE.")