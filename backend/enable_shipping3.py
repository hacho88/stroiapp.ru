import urllib.request, ssl, json, socket

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ip = socket.gethostbyname("stroiapp.ru")
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=30):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

settings = [
    ("shipping_stroiapp_logistics_status", "1"),
    ("shipping_stroiapp_logistics_sort_order", "1"),
]

for key, value in settings:
    r3 = post("db/select", {"sql": f"SELECT * FROM oc_opensetting WHERE `key` = '{key}' AND store_id = 0"})
    if r3.get('rows', []):
        post("db/executeSql", {"sql": f"UPDATE oc_opensetting SET `value` = '{value}' WHERE `key` = '{key}' AND store_id = 0"})
        print(f"  Updated {key} = {value}")
    else:
        sql = f"INSERT INTO oc_opensetting (store_id, code, `key`, `value`, serialized) VALUES (0, 'stroiapp_logistics', '{key}', '{value}', 0)"
        r5 = post("db/executeSql", {"sql": sql})
        print(f"  Added {key} = {value}: {r5}")

# Verify
r6 = post("db/select", {"sql": "SELECT * FROM oc_opensetting WHERE code = 'stroiapp_logistics'"})
print(f"\nSettings: {json.dumps(r6.get('rows', []), ensure_ascii=False)}")

# List shipping extensions
r7 = post("db/select", {"sql": "SELECT * FROM oc_openextension WHERE type = 'shipping'"})
print(f"\nShipping extensions: {json.dumps(r7.get('rows', []), ensure_ascii=False)}")

print("\n=== DONE ===")
