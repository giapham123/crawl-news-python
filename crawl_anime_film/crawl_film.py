import pychrome
import time

VIDEO_KEYWORDS = [".m3u8", ".mp4", ".ts"]

browser = pychrome.Browser(url="http://127.0.0.1:9222")

# Lấy tab đang mở
tabs = browser.list_tab()
if not tabs:
    print("❌ No tab found")
    exit()

tab = tabs[0]
tab.start()

print("[+] Attached to Chrome tab")

tab.call_method("Network.enable")

def on_request(**kwargs):
    request = kwargs.get("request", {})
    url = request.get("url", "")

    if any(k in url for k in VIDEO_KEYWORDS):
        headers = request.get("headers", {})

        print("\n=== VIDEO REQUEST ===")
        print("URL     :", url)
        print("Referer :", headers.get("Referer") or headers.get("referer"))
        print("Origin  :", headers.get("Origin"))
        print("UA      :", headers.get("User-Agent"))

tab.set_listener("Network.requestWillBeSent", on_request)

print("[*] Listening network... Play video now.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[✓] Stop")

tab.stop()
