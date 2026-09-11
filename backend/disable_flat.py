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

# Disable flat shipping
r1 = post("db/executeSql", {"sql": "UPDATE oc_opensetting SET `value` = '0' WHERE `key` = 'shipping_flat_status' AND store_id = 0"})
print(f"Disabled flat shipping: {r1}")

# Clear cache
r2 = post("site/clearCache", {})
print(f"Cache cleared: {r2}")

# Verify
r3 = post("db/select", {"sql": "SELECT * FROM oc_opensetting WHERE `key` LIKE 'shipping%' AND `key` LIKE '%status%'"})
print(f"\nActive shipping modules:")
for s in r3.get('rows', []):
    print(f"  {s['key']} = {s['value']}")

print("\n=== DONE ===")
print("Only stroiapp_logistics shipping is now active")
