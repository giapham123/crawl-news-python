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
        if count >= 5:
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

    # Unique
    return list(set(original_urls))


# ====================================
# RUN SCRIPT
# ====================================
if __name__ == "__main__":
    links = get_original_links()
    if not links:
        print("No original links found.")
    else:
        print("Original Links:")
        for l in links:
            print(l)
