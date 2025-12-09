import requests
from bs4 import BeautifulSoup
import re


# ====================================
# GET ORIGINAL LINKS FROM BAOMOI
# ====================================
def get_original_links():
    url = "https://baomoi.com/dak-lak-tag351.epi"

    try:
        response = requests.get(url, timeout=10)
    except Exception:
        return []

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Find .epi links inside content-list → h3 → a
    epi_links = []
    for a in soup.select(".content-list h3 a[href$='.epi']"):
        epi_links.append(a.get("href"))

    original_urls = []
    count = 0

    for link in epi_links:
        if count >= 50:
            break

        try:
            epi_page = requests.get("https://baomoi.com" + link, timeout=10).text
        except Exception:
            continue

        # find: originalUrl":"https://something.com"
        match = re.findall(r'originalUrl":"(https?:\/\/[^"]+)"', epi_page)

        if match:
            original_url = match[-1]  # take last detected
            original_urls.append(original_url)
            count += 1

    # Unique results
    return list(set(original_urls))


# ====================================
# SAVE LINKS TO urls.txt
# ====================================
def save_to_file(urls, file_name="urls.txt"):
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            for url in urls:
                f.write(url + "\n")
        return True
    except Exception as e:
        print("Error writing file:", e)
        return False


# ====================================
# RUN SCRIPT
# ====================================
if __name__ == "__main__":
    links = get_original_links()

    if not links:
        print("No original links found.")
    else:
        print("Found", len(links), "original links:")
        for l in links:
            print(l)

        if save_to_file(links):
            print("\n✅ Saved to urls.txt")
        else:
            print("\n❌ Failed to save file")
