import os
import re
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ==============================
# CONSTANTS
# ==============================
TODAY = datetime.now().strftime("%d/%m/%Y")

OUTPUT_FOLDER = "baomoi_data"
GLOBAL_FILE = "all_urls.txt"
DATE_FILE = "last_date.txt"
RESULT_FILE = "urls.txt"


# ==============================
# FILE HELPERS
# ==============================
def ensure_folder():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)


def reset_if_new_day():
    ensure_folder()
    date_path = os.path.join(OUTPUT_FOLDER, DATE_FILE)
    all_path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)

    last = None
    if os.path.exists(date_path):
        with open(date_path, "r", encoding="utf-8") as f:
            last = f.read().strip()

    if last != TODAY:
        print("🔄 New day detected → reset all_urls.txt")

        if os.path.exists(all_path):
            os.remove(all_path)

        with open(date_path, "w", encoding="utf-8") as f:
            f.write(TODAY)


def load_all_urls():
    path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)
    if not os.path.exists(path):
        return set()

    with open(path, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def save_to_global(urls):
    path = os.path.join(OUTPUT_FOLDER, GLOBAL_FILE)
    with open(path, "a", encoding="utf-8") as f:
        for u in urls:
            f.write(u + "\n")


def save_new_links_only(new_links):
    path = os.path.join(OUTPUT_FOLDER, RESULT_FILE)
    with open(path, "w", encoding="utf-8") as f:
        for u in new_links:
            f.write(u + "\n")


# ==============================
# SELENIUM DRIVER
# ==============================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )
    return driver


# ==============================
# CORE CRAWLER
# ==============================
def get_original_links():
    driver = get_driver()
    wait = WebDriverWait(driver, 25)

    print("🌐 Open baomoi.com")
    driver.get("https://baomoi.com")

    # ✅ wait đúng container layout mới
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.list.content-list")
        )
    )

    # 🔥 scroll để load lazy cards
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 900);")
        time.sleep(1)

    # ✅ lấy card tin
    cards = driver.find_elements(
        By.CSS_SELECTOR,
        "div.list.content-list div.bm-card"
    )

    print(f"📰 Found cards: {len(cards)}")

    epi_links = []

    for card in cards:
        try:
            a = card.find_element(By.CSS_SELECTOR, "h3 a[href$='.epi']")
            href = a.get_attribute("href")
            if href:
                epi_links.append(href)
        except Exception:
            continue

    print(f"🔗 Found epi links: {len(epi_links)}")

    original_urls = []
    count = 0

    # 🔎 vào từng epi page lấy originalUrl
    for link in epi_links:
        if count >= 15:
            break

        driver.get(link)
        time.sleep(1)

        html = driver.page_source
        match = re.findall(r'originalUrl":"(https?:\/\/[^"]+)"', html)

        if match:
            original_urls.append(match[-1])
            count += 1

    driver.quit()
    return list(set(original_urls))


# ==============================
# RUN SCRIPT
# ==============================
if __name__ == "__main__":
    ensure_folder()
    reset_if_new_day()

    crawled_before = load_all_urls()
    links = get_original_links()

    if not links:
        print("❌ No original links found.")
        save_new_links_only([])
    else:
        new_links = list(set(links) - crawled_before)

        print("✅ Found total:", len(links))
        print("🆕 New links:", len(new_links))

        for l in new_links:
            print(l)

        save_new_links_only(new_links)

        if new_links:
            save_to_global(new_links)

        print("\n🎉 urls.txt updated with ONLY new links")
