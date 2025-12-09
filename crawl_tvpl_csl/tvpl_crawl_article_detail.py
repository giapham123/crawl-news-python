import os
import json
import requests
from bs4 import BeautifulSoup

INPUT_FOLDER = "urls_folder"
OUTPUT_FOLDER = "urls_folder"  # JSON files will also be saved here

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

    # -----------------------------
    # 1️⃣ Get Title
    # -----------------------------
    title_el = soup.find("h3", class_="fw-bold title") or \
               soup.find("h3", class_="h3 fw-bold title")
    title = title_el.get_text(strip=True) if title_el else ""

    # -----------------------------
    # 2️⃣ Get Content
    # -----------------------------
    content_el = soup.find("div", class_="col-md-9 ct-main pe-md-0")
    content_html = content_el.decode_contents().strip() if content_el else ""
    content_text = content_el.get_text(" ", strip=True) if content_el else ""

    # -----------------------------
    # 3️⃣ Get Category (Cate)
    # -----------------------------
    cate = ""
    if content_el:
        cate_el = content_el.find("a", {"class": "text-primary"})
        if cate_el:
            cate = cate_el.get_text(strip=True)

    return {
        "title": title,
        "content_html": content_html,
        "content_text": content_text,
        "cate": cate
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


def main():
    # Scan all .txt files in INPUT_FOLDER
    txt_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".txt")]

    if not txt_files:
        print("No .txt files found in", INPUT_FOLDER)
        return

    for txt_file in txt_files:
        file_path = os.path.join(INPUT_FOLDER, txt_file)
        base_name = txt_file.replace("urls-", "").replace(".txt", "")
        output_file = os.path.join(OUTPUT_FOLDER, f"{base_name}.json")

        print(f"\nProcessing file: {txt_file} → {base_name}.json")

        results = crawl_file(file_path)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(results)} articles to {output_file}")


if __name__ == "__main__":
    main()
