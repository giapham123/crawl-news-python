import os
import json
import csv
import requests
import shutil
from bs4 import BeautifulSoup
from datetime import datetime
from prompts import (
    PROMPT_CLEAN_HTML,
    PROMPT_TITLE,
    PROMPT_TAGS_META,
    PROMT_CONTENT_META_TAG,
    PROMT_CREATE_IMAGE
)
from prompts_merge import (PROMT_MERGE, PROMT_MERGE_CONTENT_IMAGE)

# ================= SHARED CONFIG =================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://thuvienphapluat.vn/",
    "Connection": "keep-alive",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ================= STEP 1 CONFIG =================
BASE_URL = "https://thuvienphapluat.vn/phap-luat/"
PARAMS = [
    'doanh-nghiep', 'lao-dong-tien-luong', 'bat-dong-san', 'vi-pham-hanh-chinh',
    'bao-hiem', 'quyen-dan-su', 'thuong-mai', 'thue-phi-le-phi',
    'xuat-nhap-khau', 'thu-tuc-to-tung', 'cong-nghe-thong-tin', 'giao-thong-van-tai'
]

TODAY = datetime.now().strftime("%d/%m/%Y")

URLS_FOLDER = "urls_folder"
GLOBAL_FILE = "all_urls.txt"
DATE_FILE = "last_date.txt"

# ================= STEP 2 CONFIG =================
INPUT_FOLDER = "urls_folder"
OUTPUT_JSON_FOLDER = "result_json_folder"
OUTPUT_CSV_FOLDER = "result_csv_folder"
EXCLUDE_FILES = {"all_urls.txt"}

# ==================================================


def warm_up_session():
    try:
        print("[INFO] Warming up session...")
        SESSION.get("https://thuvienphapluat.vn/", timeout=15)
        print("[INFO] Session ready ✅")
    except Exception as e:
        print(f"[WARN] Warm-up failed (continuing anyway): {e}")


def crawl_page(url):
    try:
        res = SESSION.get(url, timeout=15)
        res.raise_for_status()
        res.encoding = "utf-8"
        return res.text
    except Exception as e:
        print(f"[ERROR] Cannot fetch: {url} → {e}")
        return None


# ================= STEP 1: CRAWL LINKS =================

def ensure_urls_folder():
    if not os.path.exists(URLS_FOLDER):
        os.makedirs(URLS_FOLDER)


def reset_if_new_day():
    ensure_urls_folder()

    date_path = os.path.join(URLS_FOLDER, DATE_FILE)
    all_url_path = os.path.join(URLS_FOLDER, GLOBAL_FILE)

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
    path = os.path.join(URLS_FOLDER, GLOBAL_FILE)
    if not os.path.exists(path):
        return set()
    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_to_global(new_urls):
    path = os.path.join(URLS_FOLDER, GLOBAL_FILE)
    with open(path, "a", encoding="utf-8") as f:
        for url in new_urls:
            f.write(url + "\n")


def save_new_urls(param, new_urls):
    filename = f"urls-{param}.txt"
    path = os.path.join(URLS_FOLDER, filename)
    with open(path, "w", encoding="utf-8") as f:
        for url in new_urls:
            f.write(url + "\n")


def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    valid_links = set()
    for article in soup.select("article.tvpl-field-row"):
        meta = article.select_one(".tvpl-field-row-meta")
        if not meta:
            continue

        date_text = meta.get_text(strip=True)
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


def step1_crawl_links():
    print("\n" + "=" * 50)
    print("STEP 1: CRAWL LINKS")
    print("=" * 50)
    print("Today date filter:", TODAY)

    reset_if_new_day()

    crawled_before = load_all_urls()
    print(f"Already crawled today: {len(crawled_before)} URLs")

    for p in PARAMS:
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

    print("\nSTEP 1 DONE.")


# ================= STEP 2: CRAWL ARTICLE DETAILS =================

def load_urls_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def extract_data(html):
    soup = BeautifulSoup(html, "html.parser")

    title_el = (
        soup.find("h1", class_="fw-bold title")
        or soup.find("h1", class_="h3 fw-bold title")
        or soup.find("h1")
    )
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = soup.select_one("section#news-content")
    content_html = content_el.decode_contents().strip() if content_el else ""
    content_text = content_el.get_text(" ", strip=True) if content_el else ""

    cate = ""
    cate_el = soup.select_one("a.badge[href*='/chu-de/']")
    if cate_el:
        cate = cate_el.get_text(strip=True)

    prompt_content_html = f"{PROMT_CONTENT_META_TAG}\n\n{content_html}"
    prompt_title = f"{PROMPT_TITLE}\n\n{title}"
    prompt_image = f"{PROMT_CREATE_IMAGE}\n\n{content_text}"
    merged_title_content = f"{PROMT_MERGE}\nTitle: {title}\nbody: {content_html}"
    merged_title_content_image = f"{PROMT_MERGE_CONTENT_IMAGE}\nTitle: {title}\nbody: {content_html}"

    return {
        "title": title,
        "merged_title_content_image": merged_title_content_image,
        "content_title": merged_title_content,
        "prompt_image": prompt_image,
        "prompt_title": prompt_title,
        "prompt_content_html": prompt_content_html,
        "content_html": content_html,
        "content_text": content_text,
    }


def crawl_file(file_path):
    urls = load_urls_from_file(file_path)
    if not urls:
        return []

    results = []
    for idx, url in enumerate(urls, 1):
        print(f"  [{idx}/{len(urls)}] Crawling: {url}")
        html = crawl_page(url)
        if not html:
            continue

        data = extract_data(html)
        data["url"] = url
        results.append(data)

    return results


def clear_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


def save_to_csv(data_list, csv_file):
    if not data_list:
        return

    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    fieldnames = list(data_list[0].keys())

    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data_list:
            writer.writerow(row)


def step2_crawl_article_details():
    print("\n" + "=" * 50)
    print("STEP 2: CRAWL ARTICLE DETAILS")
    print("=" * 50)

    os.makedirs(OUTPUT_JSON_FOLDER, exist_ok=True)
    clear_folder(OUTPUT_JSON_FOLDER)
    print("[INFO] Cleared old JSON files")

    if os.path.exists(OUTPUT_CSV_FOLDER):
        shutil.rmtree(OUTPUT_CSV_FOLDER)
    os.makedirs(OUTPUT_CSV_FOLDER, exist_ok=True)

    txt_files = [
        f for f in os.listdir(INPUT_FOLDER)
        if f.endswith(".txt") and f not in EXCLUDE_FILES
    ]

    if not txt_files:
        print("No .txt files found in", INPUT_FOLDER)
        return

    for txt_file in txt_files:
        file_path = os.path.join(INPUT_FOLDER, txt_file)
        base_name = txt_file.replace("urls-", "").replace(".txt", "")

        json_file = os.path.join(OUTPUT_JSON_FOLDER, f"{base_name}.json")
        csv_file = os.path.join(OUTPUT_CSV_FOLDER, f"{base_name}.csv")

        print(f"\n[FILE] Processing: {txt_file}")

        results = crawl_file(file_path)
        if not results:
            print(f"  No data for {txt_file}")
            continue

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  Saved JSON → {json_file}")

        save_to_csv(results, csv_file)
        print(f"  Saved CSV → {csv_file}")

    print("\nSTEP 2 DONE.")


# ================= MAIN =================

if __name__ == "__main__":
    warm_up_session()
    step1_crawl_links()
    step2_crawl_article_details()
    print("\n✅ ALL DONE.")
