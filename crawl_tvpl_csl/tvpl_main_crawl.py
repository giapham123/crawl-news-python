import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://thuvienphapluat.vn/phap-luat/"
params = ['doanh-nghiep', 'lao-dong-tien-luong','bat-dong-san','vi-pham-hanh-chinh','bao-hiem','quyen-dan-su'
          ,'thuong-mai','thue-phi-le-phi','xuat-nhap-khau','thu-tuc-to-tung','cong-nghe-thong-tin','giao-thong-van-tai']

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Today in dd/mm/yyyy format
TODAY = datetime.now().strftime("%d/%m/%Y")
# For testing:
# TODAY = "09/12/2025"

# Output folder
OUTPUT_FOLDER = "urls_folder"


def ensure_output_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


def save_urls_for_param(param, urls):
    ensure_output_folder()

    filename = f"urls-{param}.txt"
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

    print(f"Saved {len(urls)} URLs → {filepath}")


def crawl_page(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_links(html):
    soup = BeautifulSoup(html, "html.parser")
    valid_links = set()

    # ---------------------------------------------------
    # 1️⃣ Extract from .col-md-9 → section → article → a
    # ---------------------------------------------------
    container = soup.find("div", class_="col-md-9")
    if container:
        for section in container.find_all("section"):
            for article in section.find_all("article"):
                sub_time = article.select_one(".sub-time")
                if not sub_time:
                    continue

                if TODAY not in sub_time.get_text(strip=True):
                    continue

                a = article.find("a", href=True)
                if a:
                    href = a["href"]
                    if not href.startswith("http"):
                        href = "https://thuvienphapluat.vn" + href
                    valid_links.add(href)

    # ---------------------------------------------------
    # 2️⃣ Extract from a.news-card
    # ---------------------------------------------------
    for card in soup.select("a.news-card"):
        parent = card.parent
        sub_time = parent.select_one(".sub-time")
        if not sub_time:
            continue

        if TODAY not in sub_time.get_text(strip=True):
            continue

        href = card.get("href")
        if not href:
            continue

        if not href.startswith("http"):
            href = "https://thuvienphapluat.vn" + href

        valid_links.add(href)

    return valid_links


def crawl_all():
    for p in params:
        url = BASE_URL + p
        print("\nCrawling:", url)

        html = crawl_page(url)
        if not html:
            continue

        links = extract_links(html)
        print(f" → Found {len(links)} links today")

        # Save each param to its own file
        save_urls_for_param(p, links)


if __name__ == "__main__":
    print("Today date filter:", TODAY)
    crawl_all()
    print("\nDONE.")
