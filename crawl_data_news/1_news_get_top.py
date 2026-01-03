import re
import requests
from playwright.sync_api import sync_playwright


def get_original_links():
    epi_links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        page.goto("https://baomoi.com", wait_until="networkidle")

        # ✅ chờ 1 trong 2 section render là OK
        page.wait_for_selector(
            ".column.shrink .list.content-list.section-recommend, "
            ".column.shrink .bm-section.block.section-top-2",
            timeout=10000
        )

        cards = page.query_selector_all(
            ".column.shrink "
            ".list.content-list.section-recommend h3 a[href$='.epi'], "
            ".column.shrink "
            ".bm-section.block.section-top-2 h3 a[href$='.epi']"
        )

        for a in cards:
            href = a.get_attribute("href")
            if href:
                epi_links.append(href)

        browser.close()

    print("Found epi links:", len(epi_links))

    # ================================
    # LẤY ORIGINAL URL
    # ================================
    original_urls = []
    count = 0

    for link in dict.fromkeys(epi_links):  # auto unique
        if count >= 14:
            break

        try:
            res = requests.get(
                "https://baomoi.com" + link,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
        except Exception:
            continue

        match = re.findall(
            r'originalUrl":"(https?:\/\/[^"]+)"',
            res.text
        )

        if match:
            original_urls.append(match[-1])
            count += 1

    return original_urls
# ====================================
# SAVE LINKS TO urls.txt
# ====================================
def save_to_file(urls, file_name="urls_top.txt"):
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        return True
    except Exception as e:
        print("Error writing file:", e)
        return False



if __name__ == "__main__":
    links = get_original_links()

    if not links:
        print("❌ No original links found.")
    else:
        print("✅ Found", len(links), "original links:")
        for l in links:
            print(l)
        if save_to_file(links):
            print("\n✅ Saved to urls.txt")
        else:
            print("\n❌ Failed to save file")