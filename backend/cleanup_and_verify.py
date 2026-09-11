import urllib.request, ssl, json, socket, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
socket.setdefaulttimeout(30)

BASE = "https://stroiapp.ru"
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token"}

def post(action, data=None, retries=3):
    url = f"{BASE}/index.php?route=api/ai_manager&action={action}"
    d = json.dumps(data).encode() if data else b""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=d, headers=h, method="POST")
            with urllib.request.urlopen(req, context=ctx) as r:
                return json.loads(r.read().decode("utf-8-sig"))
        except Exception as e:
            if attempt == retries - 1:
                return {"error": str(e)}
            time.sleep(2)

def get(path, retries=2):
    url = f"{BASE}{path}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ctx) as r:
                return r.status, r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt == retries - 1:
                return None, str(e)
            time.sleep(2)

# 1. Test geo page
print("=== Geo page test ===")
st, body = get("/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg-dmitrovsky")
print(f"Status: {st}, Length: {len(body) if body else 0}")

# 2. Test sitemap
print("\n=== Sitemap test ===")
st, body = get("/sitemap.xml")
print(f"Status: {st}, Length: {len(body) if body else 0}")

# 3. Clean up temp files
print("\n=== Cleanup temp files ===")
temp_files = [
    "catalog/diag_temp_x9k2.php",
    "catalog/diag2_temp_x9k2.php",
    "catalog/fix_cart_temp_x9k2.php",
    "catalog/fix_cart2_temp_x9k2.php",
    "catalog/fix_cart3_temp_x9k2.php",
    "catalog/fix_cart4_temp_x9k2.php",
    "catalog/fix_cart5_temp_x9k2.php",
    "catalog/fix_all_temp_x9k2.php",
    "catalog/diag_output.txt",
    "catalog/refresh_mods_temp_x9k2.php",
    "catalog/fatal_catch_temp_x9k2.php",
    "catalog/fatal_catch2_temp_x9k2.php",
    "catalog/fatal_catch3_temp_x9k2.php",
    "catalog/dump_cart_temp_x9k2.php",
]
for f in temp_files:
    r = post("file/writeSafe", {"path": f, "content": ""})
    print(f"  {f}: {r.get('status', 'error')}")

print("\nDONE")
