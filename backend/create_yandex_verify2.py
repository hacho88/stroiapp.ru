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

def post_route(route, payload, timeout=60):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/index.php?route={route}", data=d, headers=h, method="POST")
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

content = """<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    </head>
    <body>Verification: dec751e5db71ab6d</body>
</html>"""

# DIR_MODIFICATION = /home/c/ct45965/stroiapp.ru/storage/modification/
# public_html root = /home/c/ct45965/stroiapp.ru/public_html/
# So need ../../public_html/yandex_dec751e5db71ab6d.html
print("=== Write to public_html root ===")
r = post_route("api/upload_geo_fix", {"files": [{"path": "../../public_html/yandex_dec751e5db71ab6d.html", "content": content}]})
print(f"  Result: {json.dumps(r, ensure_ascii=False)[:300]}")

# Verify
print("\n=== Verify ===")
s, body = get_url("yandex_dec751e5db71ab6d.html")
print(f"  HTTP {s}")
print(f"  Content: {body[:150] if body else 'none'}")

if s == 200 and "dec751e5db71ab6d" in body:
    print("\n  SUCCESS! Файл доступен: https://stroiapp.ru/yandex_dec751e5db71ab6d.html")
    print("  Теперь нажмите 'Подтвердить' в Яндекс.Вебмастере!")
else:
    print("\n  FAILED - file not accessible")

print("\nDONE")
