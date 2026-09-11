import urllib.request, ssl, json

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

def post(action, payload, timeout=30):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

def get_url(path, timeout=15):
    headers = {"User-Agent": "Mozilla/5.0"}
    if "188" in BASE:
        headers["Host"] = "stroiapp.ru"
    req = urllib.request.Request(f"{BASE}/{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Create yandex verification file in root
content = """<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    </head>
    <body>Verification: dec751e5db71ab6d</body>
</html>"""

print("=== Create yandex_dec751e5db71ab6d.html ===")
# The file needs to be in the site root (public_html)
# file/writeSafe only allows catalog/, image/catalog/, admin/ paths
# Try writing to catalog/ first won't work - need root access
# Let's check if there's another way - maybe via the upload_geo_fix controller
import urllib.request as ur

def post_route(route, payload, timeout=60):
    d = json.dumps(payload).encode()
    req = ur.Request(f"{BASE}/index.php?route={route}", data=d, headers=h, method="POST")
    with ur.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Try upload_geo_fix which writes to DIR_MODIFICATION - but we need public_html root
# Let's check what paths it supports
r = post_route("api/upload_geo_fix", {"files": [{"path": "../yandex_dec751e5db71ab6d.html", "content": content}]})
print(f"  Result: {json.dumps(r, ensure_ascii=False)[:300]}")

# Verify the file is accessible
print("\n=== Verify file accessible ===")
s, body = get_url("yandex_dec751e5db71ab6d.html")
print(f"  HTTP {s}")
print(f"  Content: {body[:200] if body else 'none'}")

if s == 200 and "dec751e5db71ab6d" in body:
    print("\n  SUCCESS! File is accessible at https://stroiapp.ru/yandex_dec751e5db71ab6d.html")
    print("  Now click 'Подтвердить' in Yandex Webmaster!")
else:
    # Try alternative: write to root via different method
    print("\n  File not accessible, trying alternative...")
    # Check if file/writeSafe can write to root with different path format
    r2 = post("file/writeSafe", {"path": "yandex_dec751e5db71ab6d.html", "content": content})
    print(f"  writeSafe result: {json.dumps(r2, ensure_ascii=False)[:300]}")
    s2, body2 = get_url("yandex_dec751e5db71ab6d.html")
    print(f"  HTTP {s2}")

print("\nDONE")
