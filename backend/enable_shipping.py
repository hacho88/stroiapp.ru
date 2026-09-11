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

def post_action(action, payload=None, timeout=30):
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(f"{ip_url}/index.php?route=api/ai_manager&action={action}", data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8-sig"))

# 1. Check if extension exists
r = post_action("db/select", {"sql": "SELECT * FROM oc_openextension WHERE type = 'shipping' AND code = 'stroiapp_logistics'"})
print(f"Extension exists: {r.get('rows', [])}")

# 2. Add extension
if not r.get('rows', []):
    r2 = post_action("db/executeSql", {"sql": "INSERT INTO oc_openextension (type, code) VALUES ('shipping', 'stroiapp_logistics')"})
    print(f"Extension added: {r2}")

# 3. Add settings for the shipping module
settings = [
    ("shipping_stroiapp_logistics_status", "1"),
    ("shipping_stroiapp_logistics_sort_order", "1"),
]

for key, value in settings:
    r3 = post_action("db/select", {"sql": f"SELECT * FROM oc_opensetting WHERE `key` = '{key}' AND store_id = 0"})
    if r3.get('rows', []):
        post_action("db/executeSql", {"sql": f"UPDATE oc_opensetting SET `value` = '{value}' WHERE `key` = '{key}' AND store_id = 0"})
        print(f"  Updated {key} = {value}")
    else:
        post_action("db/executeSql", {"sql": f"INSERT INTO oc_opensetting (store_id, `group`, `key`, `value`, serialized) VALUES (0, 'stroiapp_logistics', '{key}', '{value}', 0)"})
        print(f"  Added {key} = {value}")

# 4. Verify
r6 = post_action("db/select", {"sql": "SELECT * FROM oc_opensetting WHERE `group` = 'stroiapp_logistics'"})
print(f"\nSettings: {json.dumps(r6.get('rows', []), ensure_ascii=False)}")

# 5. List all shipping extensions
r7 = post_action("db/select", {"sql": "SELECT * FROM oc_openextension WHERE type = 'shipping'"})
print(f"\nAll shipping extensions: {json.dumps(r7.get('rows', []), ensure_ascii=False)}")

print("\n=== DONE ===")
print("Shipping module 'stroiapp_logistics' is enabled.")
print("It will show delivery cost in cart based on:")
print("  - Total cart weight → auto-select vehicle type")
print("  - Shipping address → zone type (city/region)")
print("  - Distance → cost calculation via logistics API")
