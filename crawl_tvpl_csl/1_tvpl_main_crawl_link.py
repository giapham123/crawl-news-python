import os
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://thuvienphapluat.vn/phap-luat/"
params = [
    'doanh-nghiep','lao-dong-tien-luong','bat-dong-san','vi-pham-hanh-chinh',
    'bao-hiem','quyen-dan-su','thuong-mai','thue-phi-le-phi',
    'xuat-nhap-khau','thu-tuc-to-tung','cong-nghe-thong-tin','giao-thong-van-tai'
]

# Rotate between realistic User-Agent strings
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

TODAY = datetime.now().strftime("%d/%m/%Y")

OUTPUT_FOLDER = "urls_folder"
GLOBAL_FILE = "all_urls.txt"
DATE_FILE = "last_date.txt"

# Shared session to persist cookies across requests
SESSION = requests.Session()


def build_headers(referer=None):
    """Build a fresh headers dict each request to mimic real browser behavior."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer or "https://thuvienphapluat.vn/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


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


def crawl_page(url, referer=None, retries=3):
    """Fetch a page with retries and exponential backoff on failure."""
    for attempt in range(1, retries + 1):
        try:
            headers = build_headers(referer=referer)
            res = SESSION.get(url, headers=headers, timeout=20)

            if res.status_code == 403:
                print(f"  ⚠️  403 Forbidden on attempt {attempt}/{retries} — waiting before retry...")
                time.sleep(5 * attempt)  # exponential-ish backoff: 5s, 10s, 15s
                continue

            res.raise_for_status()
            return res.text

        except requests.exceptions.HTTPError as e:
            print(f"  ❌ HTTP error on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)
        except Exception as e:
            print(f"  ❌ Error on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(3)

    print(f"  ✖ Giving up on {url} after {retries} attempts.")
    return None


def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    valid_links = set()
    for article in soup.select("article.tvpl-field-row"):
        meta = article.select_one(".tvpl-field-row-meta")
        if not meta:
            continue

        date_text = meta.get_text(strip=True)  # e.g. "19:10 | 16/06/2026"
        if TODAY not in date_text:
            continue

        a = article.select_one("a.tvpl-field-row-title")
        if not a:
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
    """
    Visit homepage and a secondary page to build up cookies + browsing history,
    which greatly reduces the chance of getting a 403 on subsequent requests.
    """
    steps = [
        ("https://thuvienphapluat.vn/", None),
        ("https://thuvienphapluat.vn/phap-luat/", "https://thuvienphapluat.vn/"),
    ]
    print("🌐 Warming up session...")
    for url, referer in steps:
        try:
            headers = build_headers(referer=referer)
            SESSION.get(url, headers=headers, timeout=15)
            print(f"  ✅ Visited {url}")
            time.sleep(random.uniform(1.5, 3.0))  # human-like pause between page loads
        except Exception as e:
            print(f"  ⚠️ Warm-up step failed (continuing anyway): {e}")
    print("  🔑 Session ready\n")


def crawl_all():
    crawled_before = load_all_urls()
    print(f"Already crawled today: {len(crawled_before)} URLs\n")

    for i, p in enumerate(params):
        url = BASE_URL + p
        print(f"[{i+1}/{len(params)}] Crawling: {url}")

        html = crawl_page(url, referer="https://thuvienphapluat.vn/phap-luat/")
        if not html:
            save_new_urls(p, [])
        else:
            links = extract_links(html)
            print(f"  → Found {len(links)} links today")

            new_links = links - crawled_before
            print(f"  → New links: {len(new_links)}")

            save_new_urls(p, new_links)

            if new_links:
                save_to_global(new_links)
                crawled_before.update(new_links)

        # Random delay between category requests to avoid rate-limiting
        delay = random.uniform(2.0, 5.0)
        print(f"  ⏳ Sleeping {delay:.1f}s before next request...")
        time.sleep(delay)


if __name__ == "__main__":
    print("Today date filter:", TODAY)
    reset_if_new_day()
    warm_up_session()
    crawl_all()
    print("\nDONE.")