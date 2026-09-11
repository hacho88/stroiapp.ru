import urllib.request, ssl, socket, http.cookiejar, re, json, os
from urllib.parse import urlencode, urlparse

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
socket.setdefaulttimeout(30)

BASE = "https://188.225.23.151"
HOST = "stroiapp.ru"
API_TOKEN = "change_this_ai_manager_token"

cj = http.cookiejar.CookieJar()

class CustomRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlparse(newurl)
        new_url = BASE + parsed.path + (("?" + parsed.query) if parsed.query else "")
        new_req = urllib.request.Request(new_url, headers={"Host": HOST})
        for key, val in req.header_items():
            if key.lower() not in ('host', 'content-length', 'content-type'):
                new_req.add_header(key, val)
        return new_req

opener = urllib.request.build_opener(
    CustomRedirectHandler(),
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPSHandler(context=ctx)
)

def fetch(path, data=None, extra_headers=None, timeout=30, json_body=None):
    headers = {"Host": HOST}
    if extra_headers:
        headers.update(extra_headers)
    body_data = None
    if json_body is not None:
        body_data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif data is not None:
        body_data = data.encode("utf-8") if isinstance(data, str) else data
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(BASE + path, data=body_data, headers=headers)
    try:
        r = opener.open(req, timeout=timeout)
        return r.status, r.read(), r.url
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, 'read') else b''
        return e.code, body, getattr(e, 'url', '')
    except Exception as e:
        return 0, str(e).encode(), ''

disabled_mods = []

# Step 1: Login
print("=== Step 1: Login ===")
status, body, url = fetch("/admin/index.php?route=common/login")
print(f"Login page: {status}")

data = urlencode({"username": "admin", "password": "303997sk"})
status, body, url = fetch("/admin/index.php?route=common/login", data=data)
body_str = body.decode("utf-8", errors="replace")
print(f"Login POST: {status}, URL: {url}")

m = re.search(r'user_token=([a-zA-Z0-9]+)', url + body_str)
if not m:
    print("FAILED to login! Password might be wrong.")
    print(body_str[:2000])
    exit(1)
user_token = m.group(1)
print(f"User token: {user_token}")

# Step 2: Disable mod_17
print("\n=== Step 2: Disable mod_17 ===")
status, body, url = fetch(f"/admin/index.php?route=marketplace/modification/disable&user_token={user_token}&modification_id=17")
print(f"Disable mod_17: {status}")
disabled_mods.append("17")

# Step 3: Refresh cache
print("\n=== Step 3: Refresh cache ===")
status, body, url = fetch(f"/admin/index.php?route=marketplace/modification/refresh&user_token={user_token}", timeout=120)
print(f"Refresh cache: {status}")

# Step 4: Test site
print("\n=== Step 4: Test site ===")
status, body, url = fetch("/", timeout=30)
body_str = body.decode("utf-8", errors="replace")
print(f"Homepage: {status}, len={len(body)}")

status, body, url = fetch("/index.php?route=api/ai_manager&action=site/health",
                          extra_headers={"X-AI-Token": API_TOKEN}, timeout=30)
body_str = body.decode("utf-8", errors="replace")
print(f"API health: {status}, body: {body_str[:300]}")

api_works = (status == 200)

# If API doesn't work, try disabling all modifications
if not api_works:
    print("\n=== API not working, disabling all modifications ===")
    status, body, url = fetch(f"/admin/index.php?route=marketplace/modification&user_token={user_token}")
    body_str = body.decode("utf-8", errors="replace")
    mod_ids = list(set(re.findall(r'modification_id=(\d+)', body_str)))
    print(f"Found modification IDs: {mod_ids}")
    for mid in mod_ids:
        if mid not in disabled_mods:
            status, body, url = fetch(f"/admin/index.php?route=marketplace/modification/disable&user_token={user_token}&modification_id={mid}")
            print(f"  Disable mod {mid}: {status}")
            disabled_mods.append(mid)
    # Refresh cache
    status, body, url = fetch(f"/admin/index.php?route=marketplace/modification/refresh&user_token={user_token}", timeout=120)
    print(f"Refresh cache: {status}")
    # Test API again
    status, body, url = fetch("/index.php?route=api/ai_manager&action=site/health",
                              extra_headers={"X-AI-Token": API_TOKEN}, timeout=30)
    body_str = body.decode("utf-8", errors="replace")
    print(f"API health (retry): {status}, body: {body_str[:300]}")
    api_works = (status == 200)

if not api_works:
    print("\nAPI still not working! Cannot proceed with remote fix.")
    print("You need to upload fixer.php manually via hosting file manager.")
    exit(1)

print("\n=== API works! Proceeding with fix ===")

# Step 5: Write fixed XML to catalog/mod_17_fixed.xml
print("\n=== Step 5: Write fixed XML ===")
xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mod_xml", "mod_17_FIXED.xml")
with open(xml_path, "r", encoding="utf-8") as f:
    fixed_xml = f.read()
print(f"XML size: {len(fixed_xml)} bytes")

status, body, url = fetch("/index.php?route=api/ai_manager&action=file/writeSafe",
                          json_body={"path": "catalog/mod_17_fixed.xml", "content": fixed_xml},
                          extra_headers={"X-AI-Token": API_TOKEN}, timeout=60)
body_str = body.decode("utf-8", errors="replace")
print(f"Write XML: {status}, body: {body_str[:300]}")

# Step 6: Write fixer script
print("\n=== Step 6: Write fixer script ===")
fixer_php = """<?php
require_once __DIR__ . '/../admin/config.php';
$conn = new mysqli(DB_HOSTNAME, DB_USERNAME, DB_PASSWORD, DB_DATABASE);
if ($conn->connect_error) {
    die("DB connection failed: " . $conn->connect_error);
}
$xml = file_get_contents(__DIR__ . '/mod_17_fixed.xml');
if (!$xml) {
    die("Failed to read XML file");
}
$sql = "UPDATE " . DB_PREFIX . "modification SET xml = ? WHERE modification_id = 17";
$stmt = $conn->prepare($sql);
if (!$stmt) {
    die("Prepare failed: " . $conn->error);
}
$stmt->bind_param("s", $xml);
$stmt->execute();
echo "Affected rows: " . $stmt->affected_rows . "\\n";
if ($stmt->error) {
    echo "Error: " . $stmt->error . "\\n";
}
$stmt->close();
$conn->close();
echo "XML updated successfully!\\n";
?>"""

status, body, url = fetch("/index.php?route=api/ai_manager&action=file/writeSafe",
                          json_body={"path": "catalog/fixer_temp_x9k2.php", "content": fixer_php},
                          extra_headers={"X-AI-Token": API_TOKEN}, timeout=30)
body_str = body.decode("utf-8", errors="replace")
print(f"Write fixer: {status}, body: {body_str[:300]}")

# Step 7: Run fixer script
print("\n=== Step 7: Run fixer script ===")
status, body, url = fetch("/catalog/fixer_temp_x9k2.php", timeout=30)
body_str = body.decode("utf-8", errors="replace")
print(f"Run fixer: {status}, body: {body_str[:500]}")

if status != 200 or "success" not in body_str.lower():
    print("Fixer script failed!")
    exit(1)

# Step 8: Re-enable mod_17 and other disabled mods
print("\n=== Step 8: Re-enable modifications ===")
for mid in disabled_mods:
    status, body, url = fetch(f"/admin/index.php?route=marketplace/modification/enable&user_token={user_token}&modification_id={mid}")
    print(f"  Enable mod {mid}: {status}")

# Step 9: Refresh cache
print("\n=== Step 9: Refresh cache ===")
status, body, url = fetch(f"/admin/index.php?route=marketplace/modification/refresh&user_token={user_token}", timeout=120)
print(f"Refresh cache: {status}")

# Step 10: Test site
print("\n=== Step 10: Test site ===")
status, body, url = fetch("/", timeout=30)
body_str = body.decode("utf-8", errors="replace")
print(f"Homepage: {status}, len={len(body)}")
print(f"Preview: {body_str[:300]}")

# Test a product page
status, body, url = fetch("/index.php?route=product/product&product_id=1", timeout=30)
body_str = body.decode("utf-8", errors="replace")
print(f"Product page: {status}, len={len(body)}")

# Test API
status, body, url = fetch("/index.php?route=api/ai_manager&action=site/health",
                          extra_headers={"X-AI-Token": API_TOKEN}, timeout=30)
body_str = body.decode("utf-8", errors="replace")
print(f"API health: {status}, body: {body_str[:300]}")

# Step 11: Clean up
print("\n=== Step 11: Clean up ===")
for path in ["catalog/fixer_temp_x9k2.php", "catalog/mod_17_fixed.xml"]:
    status, body, url = fetch("/index.php?route=api/ai_manager&action=file/writeSafe",
                              json_body={"path": path, "content": ""},
                              extra_headers={"X-AI-Token": API_TOKEN}, timeout=30)
    print(f"  Clear {path}: {status}")

# Also try to delete the old refresh script
status, body, url = fetch("/index.php?route=api/ai_manager&action=file/writeSafe",
                          json_body={"path": "catalog/refresh_mods7_temp_x9k2.php", "content": ""},
                          extra_headers={"X-AI-Token": API_TOKEN}, timeout=30)
print(f"  Clear refresh script: {status}")

print("\n=== DONE! ===")
