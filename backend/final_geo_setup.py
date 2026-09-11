import urllib.request, ssl, json, socket

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

hostname = "stroiapp.ru"
try:
    ip = socket.gethostbyname(hostname)
    ip_url = f"https://{ip}"
except:
    ip_url = f"https://{hostname}"

headers = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": hostname}

def post_action(action, payload=None, timeout=120):
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(f"{ip_url}/index.php?route=api/ai_manager&action={action}", data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8-sig"))

# 1. Upload final geo.php (no debug)
print("1. Uploading final geo.php...")
with open(r"d:\Projects\ai.stroiapp.ru\stroiapp.ru\public_html\catalog\controller\product\geo.php", "r", encoding="utf-8") as f:
    content = f.read()
r = post_action("file/writeSafe", {"path": "catalog/controller/product/geo.php", "content": content})
print(f"   {r}")

# 2. Clear cache
print("2. Clearing cache...")
r = post_action("site/clearCache", {})
print(f"   {r}")

# 3. Regenerate sitemap with geo pages
print("3. Regenerating sitemap with geo pages...")
r = post_action("site/generateSitemap", {})
print(f"   {r}")

# 4. Test geo page again
print("4. Final test...")
try:
    req = urllib.request.Request(
        f"{ip_url}/index.php?route=product/geo&product_id=50&city_id=khimki",
        headers={"Host": hostname, "User-Agent": "Mozilla/5.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        html = resp.read().decode("utf-8-sig")
    import re
    title_match = re.search(r'<title>([^<]+)</title>', html)
    print(f"   HTTP: {resp.status}, Length: {len(html)}")
    if title_match:
        print(f"   Title: {title_match.group(1)}")
    print(f"   Has Химки: {'Химки' in html}")
except Exception as e:
    print(f"   Error: {e}")

# 5. Test another city
print("5. Testing another city (mytishchi)...")
try:
    req = urllib.request.Request(
        f"{ip_url}/index.php?route=product/geo&product_id=50&city_id=mytishchi",
        headers={"Host": hostname, "User-Agent": "Mozilla/5.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        html = resp.read().decode("utf-8-sig")
    import re
    title_match = re.search(r'<title>([^<]+)</title>', html)
    print(f"   HTTP: {resp.status}")
    if title_match:
        print(f"   Title: {title_match.group(1)}")
    print(f"   Has Мытищи: {'Мытищи' in html}")
except Exception as e:
    print(f"   Error: {e}")

print("\n=== ALL DONE ===")
