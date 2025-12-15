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
from prompts import (
    PROMPT_CLEAN_HTML,
    PROMPT_TITLE,
    PROMPT_TAGS_META,
    PROMT_CONTENT_META_TAG,
    PROMT_CREATE_IMAGE
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
# SELECTOR FROM DOMAIN
# =============================
def get_selectors(url):
    hostname = urllib.parse.urlparse(url).hostname
    return DOMAIN_SELECTOR_MAP.get(hostname)

# =============================
# PAGE READY
# =============================
def wait_for_page_ready(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(
                "return (window.__pending_ajax_count || 0) === 0;"
            )
        )
    except:
        pass
    time.sleep(1)

def inject_ajax_counter(driver):
    driver.execute_script("""
        if (!window.__ajax_monitor_installed) {
            window.__pending_ajax_count = 0;
            const origFetch = window.fetch;
            window.fetch = function(...args) {
                window.__pending_ajax_count++;
                return origFetch(...args).finally(() => window.__pending_ajax_count--);
            };
            const origOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(...args) {
                window.__pending_ajax_count++;
                this.addEventListener('loadend', () => window.__pending_ajax_count--);
                origOpen.apply(this, args);
            };
            window.__ajax_monitor_installed = true;
        }
    """)

# =============================
# SETUP DRIVER
# =============================
def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    inject_ajax_counter(driver)
    return driver

# =============================
# CRAWLER
# =============================
def crawl(driver, url):
    selectors = get_selectors(url)
    if not selectors:
        return None, None, None, {
            "stage": "SELECTOR",
            "error_type": "SelectorNotFound",
            "error_message": "No selector mapped for domain"
        }

    title_selector = selectors.get("title")
    body_selector = selectors.get("body")

    try:
        driver.set_page_load_timeout(30)
        driver.get(url)
    except Exception as e:
        driver.execute_script("window.stop();")
        return None, None, None, {
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
        return None, None, None, {
            "stage": "TITLE_EXTRACT",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }

    # ---------- BODY ----------
    try:
        body_el = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, body_selector))
        )
        body_html = body_el.get_attribute("outerHTML")
        body_text = cleanSpaceEnter(
            body_el.text.strip() or body_el.get_attribute("innerText").strip()
        )
    except Exception as e:
        return None, None, None, {
            "stage": "BODY_EXTRACT",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }

    return title, body_html, body_text, None

# =============================
# LOAD URLS
# =============================
def load_urls(file_path="urls.txt"):
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
        title, body_html, body_text, error = crawl(driver, url)

        if error:
            fail.append({
                "url": url,
                **error
            })
            continue

        dataCrawled.append({
            "url": url,
            "title": f"{PROMPT_TITLE}\n{title}",
            "body": f"{PROMT_CONTENT_META_TAG}\n{body_html}",
            "meta_tag": f"{PROMPT_TAGS_META}\n{body_text}",
            "image": f"{PROMT_CREATE_IMAGE}\n{body_text}"
        })

    driver.quit()

    # =============================
    # EXPORT FAIL (DETAILED)
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
    # =============================
    with open(os.path.join(EXPORT_DIR, "ai_data.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|", quoting=csv.QUOTE_ALL)
        writer.writerow(["link", "title", "data", "image", "meta_tag"])
        for r in dataCrawled:
            writer.writerow([r["url"], r["title"], r["body"], r["image"], r["meta_tag"]])

    print("\n==============================")
    print(f"✅ SUCCESS: {len(dataCrawled)}")
    print(f"❌ FAIL: {len(fail)} (see fail_results.csv)")
    print("==============================")
