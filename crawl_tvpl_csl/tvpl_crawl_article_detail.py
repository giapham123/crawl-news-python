import os
import json
import csv
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from prompts import PROMPT_CLEAN_HTML, PROMPT_TITLE, PROMPT_TAGS_META, PROMT_CONTENT_META_TAG, PROMT_CREATE_IMAGE

INPUT_FOLDER = "urls_folder"
HEADERS = {"User-Agent": "Mozilla/5.0"}


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

    # 1️⃣ Get Title
    title_el = soup.find("h1", class_="fw-bold title") or \
               soup.find("h1", class_="h3 fw-bold title")
    title = title_el.get_text(strip=True) if title_el else ""

    # 2️⃣ Get Content
    content_el = soup.find("div", class_="col-md-9 ct-main pe-md-0")
    content_html = content_el.decode_contents().strip() if content_el else ""
    content_text = content_el.get_text(" ", strip=True) if content_el else ""

    # 3️⃣ Get Category
    cate = ""
    if content_el:
        cate_el = content_el.find("a", {"class": "text-primary"})
        if cate_el:
            cate = cate_el.get_text(strip=True)

    # 4️⃣ Merge prompts with content
    prompt_content_html = f"{PROMT_CONTENT_META_TAG}\n\n{content_html}"
    prompt_title = f"{PROMPT_TITLE}\n\n{title}"
    prompt_image = f"{PROMT_CREATE_IMAGE}\n\n{content_html}"
    prompt_tags_meta = f"{PROMPT_TAGS_META}\n\n{content_html}"

    return {
        "title": title,
        "content_html": content_html,
        "content_text": content_text,
        "cate": cate,
        "prompt_content_html": prompt_content_html,
        "prompt_title": prompt_title,
        "prompt_image": prompt_image,
        "prompt_tags_meta": prompt_tags_meta
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


def save_to_csv(data_list, csv_file):
    if not data_list:
        return
    # Use the keys of the first item as CSV columns
    fieldnames = list(data_list[0].keys())
    with open(csv_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data_list:
            writer.writerow(row)


def main():
    # Create timestamped result folder
    timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
    output_folder = f"result{timestamp}"
    os.makedirs(output_folder, exist_ok=True)

    # Scan all .txt files in INPUT_FOLDER
    txt_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".txt")]

    if not txt_files:
        print("No .txt files found in", INPUT_FOLDER)
        return

    for txt_file in txt_files:
        file_path = os.path.join(INPUT_FOLDER, txt_file)
        base_name = txt_file.replace("urls-", "").replace(".txt", "")
        json_file = os.path.join(output_folder, f"{base_name}.json")
        csv_file = os.path.join(output_folder, f"{base_name}.csv")

        print(f"\nProcessing file: {txt_file} → {base_name}.json / {base_name}.csv")

        results = crawl_file(file_path)
        if results:  # Only save if results is not empty
            # Save JSON
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(results)} articles to {json_file}")

            # Save CSV
            save_to_csv(results, csv_file)
            print(f"Saved {len(results)} articles to {csv_file}")
        else:
            print(f"No articles found for {txt_file}, skipping JSON/CSV creation.")


if __name__ == "__main__":
    main()
