import csv
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from common_func import clean_and_parse_json, clean_and_parse_json_html

from config import DOMAIN_SELECTOR_MAP
from gemini_api import generate_text
from prompts import PROMPT_CLEAN_HTML, PROMPT_TITLE, PROMPT_TAGS_META


# =============================
# SELECTOR FROM DOMAIN
# =============================
def get_selectors(url):
    hostname = urllib.parse.urlparse(url).hostname
    return DOMAIN_SELECTOR_MAP.get(hostname, None)


# =============================
# WAIT PAGE LOADED
# =============================
def wait_for_page_ready(driver, timeout=20):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return (window.__pending_ajax_count || 0) === 0;")
        )
    except:
        pass

    time.sleep(1)


def inject_ajax_counter(driver):
    script = """
        if (!window.__ajax_monitor_installed) {
            window.__pending_ajax_count = 0;
            const origFetch = window.fetch;
            window.fetch = function(...args) {
                window.__pending_ajax_count++;
                return origFetch(...args).finally(() => {
                    window.__pending_ajax_count--;
                });
            };

            const origOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(...args) {
                this.addEventListener('loadend', function() {
                    window.__pending_ajax_count--;
                });
                window.__pending_ajax_count++;
                origOpen.apply(this, args);
            };

            window.__ajax_monitor_installed = true;
        }
    """
    driver.execute_script(script)


# =============================
# SETUP SELENIUM
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
        return ("ERROR: selector not found", "ERROR: selector not found")

    title_selector = selectors.get("title", "")
    body_selector = selectors.get("body", "")

    driver.get(url)
    wait_for_page_ready(driver)

    title_text = "ERROR: cannot extract title"
    body_html = "ERROR: cannot extract body"

    # TITLE
    try:
        if title_selector:
            title_el = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))
            )
            title_text = title_el.text.strip() or title_el.get_attribute("innerText").strip()
    except:
        pass

    # BODY
    try:
        if body_selector:
            body_el = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, body_selector))
            )
            body_html = body_el.get_attribute("outerHTML")
    except:
        pass

    return title_text, body_html


# =============================
# LOAD URLS
# =============================

def load_urls(file_path="urls.txt"):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


# =============================
# MAIN
# =============================
if __name__ == "__main__":
    driver = setup_driver()

    dataCrawled = []
    success = []
    fail = []

    urls = load_urls()

    for url in urls:
        title_text, body_html = crawl(driver, url)

        # Nếu crawl lỗi → đưa vào fail CSV
        if "ERROR" in title_text or "ERROR" in body_html:
            fail.append({"url": url, "title": title_text, "body": body_html})
            continue

        # CALL GEMINI
        try:
            clean_prompt =  f"{PROMPT_CLEAN_HTML}\n{body_html}"
            prompt_title = f"{PROMPT_TITLE}\n{title_text}"

            # =============================
            # CRAWL DATA HERE
            # =============================
            dataCrawled.append({"url": url, "title": prompt_title, "body": clean_prompt})

            # =============================
            # THIS CODE BELOW USING GEMINI TO GENERATE CONTENT
            # =============================
            # result_body = generate_text(clean_prompt)
            # clean_prompt_meta_tag =  f"{PROMPT_TAGS_META}\n{result_body}"
            # result_meta_tag= generate_text(clean_prompt_meta_tag)
            # result_title = generate_text(prompt_title)
            #
            # parsed_title = clean_and_parse_json(result_title)
            # parsed_meta_tag = clean_and_parse_json(result_meta_tag)
            # # parsed_body = clean_and_parse_json_html(result_body)
            #
            # result_title_text = parsed_title.get("title", "")
            # result_slug = parsed_title.get("slug", "")
            # result_focus = parsed_title.get("focus_keyphrase", "")
            #
            # # clean_html = parsed_body.get("clean_html", "")
            # result_meta = parsed_meta_tag.get("meta_description", "")
            # result_tags = parsed_meta_tag.get("tags", "")
            #
            # if not result_title or not result_body:
            #     fail.append({"url": url, "title": "API EMPTY", "body": "API EMPTY"})
            #     continue
            # success.append({
            #     "url": url,
            #     "title": result_title_text,
            #     "body": result_body,
            #     "slug": result_slug,
            #     "meta": result_meta,
            #     "focus_key": result_focus,
            #     "tags": result_tags,
            # })
        except Exception as e:
            fail.append({"url": url, "title": "API ERROR", "body": str(e)})
            continue

    driver.quit()

    # =============================
    # EXPORT SUCCESS FILE
    # =============================
    with open("success_results.csv", "w", newline="", encoding="utf-8") as csvfile:
        columns = ["title", "body", "slug", "meta", "focus_key", "tags", "url"]
        writer = csv.DictWriter(csvfile, fieldnames=columns, delimiter="|", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in success:
            writer.writerow(row)

    # =============================
    # EXPORT FAIL FILE
    # =============================
    with open("fail_results.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter="|", quoting=csv.QUOTE_ALL)
        writer.writerow(["url", "title", "body"])
        for row in fail:
            writer.writerow([row["url"], row["title"], row["body"]])

    # =============================
    # EXPORT AI DATA FILE (NEW)
    # Format: link | title | data
    # =============================
    with open("ai_data.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter="|", quoting=csv.QUOTE_ALL)
        writer.writerow(["link", "title", "data"])

        for row in dataCrawled:
            writer.writerow([
                row["url"],
                row["title"],
                row["body"]  # đây là clean HTML để train AI
            ])

    print("\n==============================")
    print(f"✅ SUCCESS: {len(success)} URLs")
    print(f"✅ SUCCESS CRAWL: {len(dataCrawled)} URLs")
    print(f"❌ FAIL: {len(fail)} URLs")
    print("📁 File xuất:")
    print("  - success_results.csv")
    print("  - fail_results.csv")
    print("  - ai_data.csv   (NEW)")
    print("==============================")
