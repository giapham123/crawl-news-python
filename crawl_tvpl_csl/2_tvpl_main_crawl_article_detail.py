import os
import json
import csv
import time
import random
import requests
import shutil
from datetime import datetime
from bs4 import BeautifulSoup
from prompts import (
    PROMPT_CLEAN_HTML,
    PROMPT_TITLE,
    PROMPT_TAGS_META,
    PROMT_CONTENT_META_TAG,
    PROMT_CREATE_IMAGE
)
from prompts_merge import (PROMT_MERGE, PROMT_MERGE_CONTENT_IMAGE)

# ================= CONFIG =================
INPUT_FOLDER = "urls_folder"
OUTPUT_JSON_FOLDER = "result_json_folder"
OUTPUT_CSV_FOLDER = "result_csv_folder"

EXCLUDE_FILES = {"all_urls.txt"}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

SESSION = requests.Session()
# ==========================================


def build_headers(referer=None):
    """Build fresh headers per request with a random UA to avoid fingerprinting."""
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


def warm_up_session():
    """Visit homepage and listing page to build cookies before real crawling."""
    steps = [
        ("https://thuvienphapluat.vn/", None),
        ("https://thuvienphapluat.vn/phap-luat/", "https://thuvienphapluat.vn/"),
    ]
    print("[INFO] Warming up session...")
    for url, referer in steps:
        try:
            SESSION.get(url, headers=build_headers(referer=referer), timeout=15)
            print(f"[INFO]   ✅ Visited {url}")
            time.sleep(random.uniform(1.5, 3.0))
        except Exception as e:
            print(f"[WARN]   Warm-up step failed (continuing anyway): {e}")
    print("[INFO] Session ready 🔑\n")


def load_urls_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def crawl_page(url, referer=None, retries=3):
    """Fetch a page with retries and exponential backoff on 403/errors."""
    for attempt in range(1, retries + 1):
        try:
            headers = build_headers(referer=referer)
            res = SESSION.get(url, headers=headers, timeout=20)

            if res.status_code == 403:
                print(f"[WARN] 403 Forbidden on attempt {attempt}/{retries} for {url} — backing off...")
                time.sleep(5 * attempt)  # 5s → 10s → 15s
                continue

            res.raise_for_status()
            res.encoding = "utf-8"
            return res.text

        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] HTTP error attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(5 * attempt)
        except Exception as e:
            print(f"[ERROR] Fetch error attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(3)

    print(f"[ERROR] Giving up on {url} after {retries} attempts.")
    return None


def extract_data(html):
    soup = BeautifulSoup(html, "html.parser")

    # 1️⃣ Title
    title_el = (
        soup.find("h1", class_="fw-bold title")
        or soup.find("h1", class_="h3 fw-bold title")
        or soup.find("h1")
    )
    title = title_el.get_text(strip=True) if title_el else ""

    # 2️⃣ Content
    content_el = soup.select_one("section#news-content")
    content_html = content_el.decode_contents().strip() if content_el else ""
    content_text = content_el.get_text(" ", strip=True) if content_el else ""

    # 3️⃣ Category
    cate = ""
    cate_el = soup.select_one("a.badge[href*='/chu-de/']")
    if cate_el:
        cate = cate_el.get_text(strip=True)

    # 4️⃣ Prompts
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
        # Use the listing page as referer — mimics clicking from the index
        html = crawl_page(url, referer="https://thuvienphapluat.vn/phap-luat/")
        if not html:
            continue

        data = extract_data(html)
        data["url"] = url
        results.append(data)

        # Random delay between article fetches to avoid rate-limiting
        if idx < len(urls):
            delay = random.uniform(2.0, 5.0)
            print(f"  ⏳ Sleeping {delay:.1f}s...")
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


def main():
    # ===== PREPARE FOLDERS =====
    os.makedirs(OUTPUT_JSON_FOLDER, exist_ok=True)
    clear_folder(OUTPUT_JSON_FOLDER)
    print("[INFO] Cleared old JSON files")

    if os.path.exists(OUTPUT_CSV_FOLDER):
        shutil.rmtree(OUTPUT_CSV_FOLDER)
    os.makedirs(OUTPUT_CSV_FOLDER, exist_ok=True)

    # ===== WARM UP SESSION =====
    warm_up_session()

    # ===== READ URL FILES =====
    txt_files = [
        f for f in os.listdir(INPUT_FOLDER)
        if f.endswith(".txt") and f not in EXCLUDE_FILES
    ]

    if not txt_files:
        print("No .txt files found in", INPUT_FOLDER)
        return

    # ===== PROCESS EACH FILE =====
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

        # Save JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  Saved JSON → {json_file}")

        # Save CSV
        save_to_csv(results, csv_file)
        print(f"  Saved CSV → {csv_file}")

        # Pause between processing different category files
        delay = random.uniform(3.0, 6.0)
        print(f"\n[INFO] Sleeping {delay:.1f}s before next file...")
        time.sleep(delay)


if __name__ == "__main__":
    main()