import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime

TODAY = datetime.now().strftime("%d/%m/%Y")

OUTPUT_FOLDER = "baomoi_data"
GLOBAL_FILE = "all_urls.txt"
DATE_FILE = "last_date.txt"
RESULT_FILE = "urls.txt"


def ensure_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


# ==============================
# RESET GLOBAL FILE IF NEW DAY
# ==============================
def reset_if_new_day():
    ensure_folder()

    date_path = os.path.join(OUTPUT_FOLDER, DATE_FILE)
    all_path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)

    if os.path.exists(date_path):
        with open(date_path, "r") as f:
            last = f.read().strip()
    else:
        last = None

    if last != TODAY:
        print("🔄 New day detected → reset all_urls.txt")

        if os.path.exists(all_path):
            os.remove(all_path)

        with open(date_path, "w") as f:
            f.write(TODAY)


# ==============================
# LOAD GLOBAL URL MEMORY
# ==============================
def load_all_urls():
    path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)

    if not os.path.exists(path):
        return set()

    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


# ==============================
# SAVE GLOBAL MEMORY
# ==============================
def save_to_global(urls):
    path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)

    with open(path, "a", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")


# ==============================
# GET ORIGINAL LINKS
# ==============================
def get_original_links():
    url = "https://baomoi.com/dak-lak-tag351.epi"

    try:
        response = requests.get(url, timeout=10)
    except Exception:
        return []

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    epi_links = []
    for a in soup.select(".content-list h3 a[href$='.epi']"):
        epi_links.append(a.get("href"))

    original_urls = []
    count = 0

    for link in epi_links:
        if count >= 15:
            break

        try:
            epi_page = requests.get("https://baomoi.com" + link, timeout=10).text
        except Exception:
            continue

        match = re.findall(r'originalUrl":"(https?:\/\/[^"]+)"', epi_page)

        if match:
            original_urls.append(match[-1])
            count += 1

    return list(set(original_urls))


# ==============================
# SAVE ONLY NEW LINKS
# ==============================
def save_new_links_only(new_links):
    path = os.path.join(OUTPUT_FOLDER, RESULT_FILE)

    # overwrite old file
    with open(path, "w", encoding="utf-8") as f:
        for u in new_links:
            f.write(u + "\n")


# ==============================
# RUN SCRIPT
# ==============================
if __name__ == "__main__":
    ensure_folder()
    reset_if_new_day()

    crawled_before = load_all_urls()

    links = get_original_links()

    if not links:
        print("No original links found.")
        save_new_links_only([])
    else:
        new_links = list(set(links) - crawled_before)

        print("Found:", len(links))
        print("New:", len(new_links))

        for l in new_links:
            print(l)

        # overwrite urls.txt with only new links
        save_new_links_only(new_links)

        if new_links:
            save_to_global(new_links)

        print("\n✅ urls.txt updated with only NEW links")
