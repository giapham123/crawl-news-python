from playwright.sync_api import sync_playwright


def get_images():
    images = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0")

        page.goto("https://baomoi.com", wait_until="networkidle")

        # chờ card render
        page.wait_for_selector(".column.shrink .h-full", timeout=10000)

        cards = page.query_selector_all(".column.shrink .h-full")

        for card in cards:
            img_url = None

            # ưu tiên img trong bm-card-content
            img = card.query_selector(".bm-card-content.ml-\\[15px\\] img")

            # fallback: img bất kỳ trong card
            if not img:
                img = card.query_selector("img")

            if img:
                img_url = img.get_attribute("src") or img.get_attribute("data-src")

            if img_url:
                images.append(img_url)

        browser.close()

    return images


# =========================
# SAVE TO FILE
# =========================
def save_to_file(urls, file_name="images.txt"):
    with open(file_name, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")


if __name__ == "__main__":
    images = get_images()

    if images:
        print(f"✅ Found {len(images)} images:")
        for img in images:
            print(img)

        save_to_file(images)
        print("\n✅ Saved to images.txt")
    else:
        print("❌ No images found.")
