import os
import re
import json
import csv
import time
import random
import shutil
from bs4 import BeautifulSoup
from datetime import datetime
from curl_cffi import requests as cf_requests
from prompts import (
    PROMPT_CLEAN_HTML,
    PROMPT_TITLE,
    PROMPT_TAGS_META,
    PROMT_CONTENT_META_TAG,
    PROMT_CREATE_IMAGE
)
from prompts_merge import (PROMT_MERGE, PROMT_MERGE_CONTENT_IMAGE)

# ================= SHARED CONFIG =================
# Rotate between Chrome versions to avoid fingerprint pattern
IMPERSONATE_PROFILES = ["chrome124", "chrome123", "chrome120", "chrome110"]

SESSION = cf_requests.Session(impersonate=random.choice(IMPERSONATE_PROFILES))

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


def build_headers(referer=None):
    """Minimal extra headers — curl_cffi already handles UA + TLS fingerprint."""
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer or "https://thuvienphapluat.vn/",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }


def warm_up_session():
    """Visit homepage and listing page to build cookies before real crawling."""
    steps = [
        ("https://thuvienphapluat.vn/", None),
        ("https://thuvienphapluat.vn/phap-luat/", "https://thuvienphapluat.vn/"),
    ]
    print("[INFO] Warming up session...")
    for url, referer in steps:
        try:
            SESSION.get(url, headers=build_headers(referer=referer), timeout=20)
            print(f"[INFO]   Visited {url}")
            time.sleep(random.uniform(1.5, 3.0))
        except Exception as e:
            print(f"[WARN]   Warm-up step failed (continuing anyway): {e}")
    print("[INFO] Session ready\n")


def crawl_page(url, referer=None, retries=3):
    """
    Fetch a page using curl_cffi (bypasses Cloudflare TLS fingerprinting).
    Retries with exponential backoff on 403 or errors.
    """
    for attempt in range(1, retries + 1):
        try:
            impersonate = random.choice(IMPERSONATE_PROFILES)
            res = SESSION.get(
                url,
                headers=build_headers(referer=referer),
                impersonate=impersonate,
                timeout=20,
            )

            if res.status_code == 403:
                wait = 5 * attempt  # 5s -> 10s -> 15s
                print(f"[WARN] 403 on attempt {attempt}/{retries} (profile={impersonate}) — waiting {wait}s...")
                time.sleep(wait)
                continue

            if res.status_code == 429:
                wait = 15 * attempt  # rate-limited — back off harder
                print(f"[WARN] 429 Rate Limited on attempt {attempt}/{retries} — waiting {wait}s...")
                time.sleep(wait)
                continue

            res.raise_for_status()
            return res.text

        except Exception as e:
            print(f"[ERROR] Attempt {attempt}/{retries} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)

    print(f"[ERROR] Giving up on {url} after {retries} attempts.")
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
        print("New day detected -> reset all_urls.txt")
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

    for i, p in enumerate(PARAMS, 1):
        url = BASE_URL + p
        print(f"\n[{i}/{len(PARAMS)}] Crawling: {url}")

        html = crawl_page(url, referer="https://thuvienphapluat.vn/phap-luat/")
        if not html:
            save_new_urls(p, [])
        else:
            links = extract_links(html)
            print(f"  -> Found {len(links)} links today")

            new_links = links - crawled_before
            print(f"  -> New links: {len(new_links)}")

            save_new_urls(p, new_links)

            if new_links:
                save_to_global(new_links)
                crawled_before.update(new_links)

        delay = random.uniform(2.0, 5.0)
        print(f"  Sleeping {delay:.1f}s...")
        time.sleep(delay)

    print("\nSTEP 1 DONE.")


# ================= STEP 2: CRAWL ARTICLE DETAILS =================

def load_urls_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# Caption marker for placeholder images, e.g. "(Hình từ Internet)",
# "(Hình ảnh Internet)", "(Hình ảnh từ Internet)" — case-insensitive.
INTERNET_IMAGE_RE = re.compile(r"hình.*internet", re.IGNORECASE | re.DOTALL)


def remove_internet_images(content_el):
    """Drop placeholder images whose <em> caption mentions 'Hình ... Internet'.

    The article markup is typically:
        <p><img ... /></p>
        <p style="text-align: center;"><em>... (Hình từ Internet)</em></p>
    We remove both the image and its caption.
    """
    if content_el is None:
        return

    for em in content_el.find_all("em"):
        text = em.get_text(" ", strip=True)
        if not text or not INTERNET_IMAGE_RE.search(text):
            continue

        caption = em.find_parent("p") or em

        # The image usually sits in the <p> right before the caption.
        img = None
        prev_p = caption.find_previous_sibling("p")
        if prev_p is not None:
            img = prev_p.find("img")
        if img is None:
            img = em.find_previous("img")

        if img is not None:
            (img.find_parent("p") or img).decompose()
        caption.decompose()


def extract_data(html):
    soup = BeautifulSoup(html, "html.parser")

    title_el = (
        soup.find("h1", class_="fw-bold title")
        or soup.find("h1", class_="h3 fw-bold title")
        or soup.find("h1")
    )
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = soup.select_one("section#news-content")
    remove_internet_images(content_el)
    content_html = content_el.decode_contents().strip() if content_el else ""
    content_text = content_el.get_text(" ", strip=True) if content_el else ""

    # Category from breadcrumb: <ol class="tvpl-bc"> -> last link (skip "Trang chủ")
    cate = ""
    bc_links = soup.select("ol.tvpl-bc a.tvpl-bc-link")
    cate_links = [a for a in bc_links if a.get("href", "").rstrip("/") != "/phap-luat"]
    if cate_links:
        cate = cate_links[-1].get_text(strip=True)
    if not cate:
        cate_el = soup.select_one("a.badge[href*='/chu-de/']")
        if cate_el:
            cate = cate_el.get_text(strip=True)

    prompt_content_html = f"{PROMT_CONTENT_META_TAG}\n\n{content_html}"
    prompt_title = f"{PROMPT_TITLE}\n\n{title}"
    prompt_image = f"{PROMT_CREATE_IMAGE}\n\n{content_text}"
    merged_title_content = f"{PROMT_MERGE}\nTitle: {title}\nbody: {content_html}"
    merged_title_content_image = f"{PROMT_MERGE_CONTENT_IMAGE}\nCate: {cate}\nTitle: {title}\nbody: {content_html}"

    return {
        "title": title,
        "cate": cate,
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
        html = crawl_page(url, referer="https://thuvienphapluat.vn/phap-luat/")
        if not html:
            continue

        data = extract_data(html)
        data["url"] = url
        results.append(data)

        if idx < len(urls):
            delay = random.uniform(2.0, 5.0)
            print(f"  Sleeping {delay:.1f}s...")
            time.sleep(delay)

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
        print(f"  Saved JSON -> {json_file}")

        save_to_csv(results, csv_file)
        print(f"  Saved CSV -> {csv_file}")

        delay = random.uniform(3.0, 6.0)
        print(f"\n[INFO] Sleeping {delay:.1f}s before next file...")
        time.sleep(delay)

    print("\nSTEP 2 DONE.")


# ================= MAIN =================

if __name__ == "__main__":
    warm_up_session()
    step1_crawl_links()
    step2_crawl_article_details()
    print("\nALL DONE.")