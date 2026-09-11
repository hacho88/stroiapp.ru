import urllib.request, urllib.parse, ssl, json, socket

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    socket.getaddrinfo("stroiapp.ru", 443, socket.AF_INET)
    BASE = "https://stroiapp.ru"
except:
    BASE = "https://188.225.23.151"

h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token"}
if "188" in BASE:
    h["Host"] = "stroiapp.ru"

def post(action, payload, timeout=60, params=None):
    url = f"{BASE}/index.php?route=api/ai_manager&action={action}"
    if params:
        url += "&" + "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    d = json.dumps(payload).encode() if payload else b""
    req = urllib.request.Request(url, data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Upload reverted header.php
LOCAL_PATH = r"d:\Projects\ai.stroiapp.ru\stroiapp.ru\public_html\catalog\controller\common\header.php"
with open(LOCAL_PATH, "r", encoding="utf-8") as f:
    content = f.read()
r = post("file/writeSafe", {"path": "catalog/controller/common/header.php", "content": content})
print(f"Reverted header.php uploaded: {r.get('status')}")

r2 = post("site/clearCache", {})
print(f"Cache: {r2}")

# Test site
headers = {"User-Agent": "Mozilla/5.0"}
if "188" in BASE:
    headers["Host"] = "stroiapp.ru"
try:
    req = urllib.request.Request(f"{BASE}/", headers=headers)
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        print(f"Homepage status: {resp.status} - SITE OK")
except urllib.error.HTTPError as e:
    print(f"Homepage: HTTP {e.code} - still broken")

print("\nDONE")
