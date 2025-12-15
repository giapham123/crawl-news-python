import os
import json
import csv
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

# ================= CONFIG =================
INPUT_FOLDER = "urls_folder"
OUTPUT_JSON_FOLDER = "result_json_folder"
OUTPUT_CSV_FOLDER = "result_csv_folder"

HEADERS = {"User-Agent": "Mozilla/5.0"}
# ==========================================


def load_urls_from_file(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def crawl_page(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"[ERROR] Cannot fetch: {url} → {e}")
        return None


def extract_data(html):
    soup = BeautifulSoup(html, "html.parser")

    # 1️⃣ Title
    title_el = (
        soup.find("h1", class_="fw-bold title")
        or soup.find("h1", class_="h3 fw-bold title")
    )
    title = title_el.get_text(strip=True) if title_el else ""

    # 2️⃣ Content
    content_el = soup.find("div", class_="col-md-9 ct-main pe-md-0")
    content_html = content_el.decode_contents().strip() if content_el else ""
    content_text = content_el.get_text(" ", strip=True) if content_el else ""

    # 3️⃣ Category
    cate = ""
    if content_el:
        cate_el = content_el.find("a", class_="text-primary")
        if cate_el:
            cate = cate_el.get_text(strip=True)

    # 4️⃣ Prompts
    prompt_content_html = f"{PROMT_CONTENT_META_TAG}\n\n{content_html}"
    prompt_title = f"{PROMPT_TITLE}\n\n{title}"
    prompt_image = f"{PROMT_CREATE_IMAGE}\n\n{content_text}"

    return {
        "title": title,
        "category": cate,
        "prompt_content_html": prompt_content_html,
        "prompt_title": prompt_title,
        "prompt_image": prompt_image,
        "content_html": content_html,
        "content_text": content_text,
    }


def crawl_file(file_path):
    urls = load_urls_from_file(file_path)
    if not urls:
        return []

    results = []
    for idx, url in enumerate(urls, 1):
        print(f"[{idx}/{len(urls)}] Crawling: {url}")
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


def main():
    # ===== PREPARE FOLDERS =====
    os.makedirs(OUTPUT_JSON_FOLDER, exist_ok=True)
    clear_folder(OUTPUT_JSON_FOLDER)
    print("[INFO] Cleared old JSON files")

    if os.path.exists(OUTPUT_CSV_FOLDER):
        shutil.rmtree(OUTPUT_CSV_FOLDER)
    os.makedirs(OUTPUT_CSV_FOLDER, exist_ok=True)

    # ===== READ URL FILES =====
    txt_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".txt")]
    if not txt_files:
        print("No .txt files found in", INPUT_FOLDER)
        return

    # ===== PROCESS EACH FILE =====
    for txt_file in txt_files:
        file_path = os.path.join(INPUT_FOLDER, txt_file)
        base_name = txt_file.replace("urls-", "").replace(".txt", "")

        json_file = os.path.join(OUTPUT_JSON_FOLDER, f"{base_name}.json")
        csv_file = os.path.join(OUTPUT_CSV_FOLDER, f"{base_name}.csv")

        print(f"\nProcessing: {txt_file}")

        results = crawl_file(file_path)
        if not results:
            print(f"No data for {txt_file}")
            continue

        # Save JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON → {json_file}")

        # Save CSV
        save_to_csv(results, csv_file)
        print(f"Saved CSV → {csv_file}")

if __name__ == "__main__":
    main()
