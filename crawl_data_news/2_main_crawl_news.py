import os
import csv
import time
import urllib.parse
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from common_func import clean_and_parse_json, clean_and_parse_json_html, cleanSpaceEnter
from config import DOMAIN_SELECTOR_MAP
from gemini_api import generate_text

from prompts_en import (
    PROMPT_TITLE,
    PROMPT_TAGS_META,
    PROMT_CONTENT_META_TAG,
    PROMT_CREATE_IMAGE
)
from prompts_merge import (PROMT_MERGE
)


# =============================
# EXPORT CONFIG
# =============================
EXPORT_DIR = "output"

def prepare_export_folder():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    else:
        for f in os.listdir(EXPORT_DIR):
            fp = os.path.join(EXPORT_DIR, f)
            if os.path.isfile(fp):
                os.remove(fp)

prepare_export_folder()

# =============================
# DOMAIN UTILS
# =============================
def get_domain_name(url):
    hostname = urllib.parse.urlparse(url).hostname
    if hostname:
        return hostname.replace("www.", "")
    return ""

# =============================
# SELECTOR FROM DOMAIN
# =============================
def get_selectors(url):
    hostname = urllib.parse.urlparse(url).hostname
    return DOMAIN_SELECTOR_MAP.get(hostname)

# =============================
# PAGE READY
# =============================
def wait_for_page_ready(driver, timeout=15):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") in ["interactive","complete"]
        )
    except:
        pass


# =============================
# SETUP DRIVER
# =============================
def setup_driver():
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # speed & stability
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-fonts")
    options.add_argument("--disable-logging")
    options.add_argument("--mute-audio")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143 Safari/537.36"
    )

    options.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=options)

    driver.set_page_load_timeout(25)
    driver.set_script_timeout(25)

    return driver


# =============================
# CRAWLER
# =============================
def crawl(driver, url, retry=2):

    selectors = get_selectors(url)
    if not selectors:
        return None, None, None, None, {
            "stage": "SELECTOR",
            "error_type": "SelectorNotFound",
            "error_message": "No selector mapped for domain"
        }

    title_selector = selectors.get("title")
    body_selector = selectors.get("body")

    try:
        driver.get(url)
    except Exception as e:
        try:
            driver.execute_script("window.stop();")
        except:
            pass

        if retry > 0:
            return crawl(driver, url, retry-1)

        return None, None, None, None, {
            "stage": "PAGE_LOAD",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }

    wait_for_page_ready(driver)

    # ---------- TITLE ----------
    try:
        title_el = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))
        )
        title = title_el.text.strip() or title_el.get_attribute("innerText").strip()
    except Exception as e:
        return None, None, None, None, {
            "stage": "TITLE_EXTRACT",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }

    # ---------- BODY ----------
    try:
        body_el = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, body_selector))
        )
        body_html = body_el.get_attribute("outerHTML")
        body_text = cleanSpaceEnter(
            body_el.text.strip() or body_el.get_attribute("innerText").strip()
        )
    except Exception as e:
        return None, None, None, None, {
            "stage": "BODY_EXTRACT",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }

    domain = get_domain_name(url)

    return title, body_html, body_text, domain, None

# =============================
# LOAD URLS
# =============================
def load_urls(file_path="baomoi_data/urls.txt"):
    with open(file_path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

# =============================
# MAIN
# =============================
if __name__ == "__main__":

    driver = setup_driver()

    success = []
    fail = []
    dataCrawled = []

    for url in load_urls():
        title, body_html, body_text, domain, error = crawl(driver, url)

        if error:
            fail.append({
                "url": url,
                **error
            })
            continue
        merged_title = f"Title: {title}\nDomain: {domain}"
        merged_title_content = f"Title: {title}\nDomain: {domain}\n{body_html}"
        dataCrawled.append({
            "url": url,
            "domain": domain,
            "content_title": f"{PROMT_MERGE}\n{merged_title_content}",
            "title": f"{PROMPT_TITLE}\n{merged_title}",
            "body": f"{PROMT_CONTENT_META_TAG}\n{body_html}",
            "ori_html": f"{body_html}",
            "image": f"{PROMT_CREATE_IMAGE}\n{body_text}"
        })

    driver.quit()

    # =============================
    # EXPORT FAIL
    # =============================
    with open(os.path.join(EXPORT_DIR, "fail_results.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|", quoting=csv.QUOTE_ALL)
        writer.writerow(["url", "stage", "error_type", "error_message"])
        for r in fail:
            writer.writerow([
                r["url"],
                r["stage"],
                r["error_type"],
                r["error_message"]
            ])

    # =============================
    # EXPORT AI DATA
    # =============================
    with open(os.path.join(EXPORT_DIR, "ai_data.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|", quoting=csv.QUOTE_ALL)
        writer.writerow(["link", "content_title","title", "data", "image", "ori_html", "domain"])
        for r in dataCrawled:
            writer.writerow([
                r["url"],
                r["content_title"],
                r["title"],
                r["body"],
                r["image"],
                r["ori_html"],
                r["domain"]
            ])

    print("\n==============================")
    print(f"✅ SUCCESS: {len(dataCrawled)}")
    print(f"❌ FAIL: {len(fail)} (see fail_results.csv)")
    print("==============================")
