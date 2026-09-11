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

# Clear old template-based geo pages
print("Clearing old geo pages...")
r = post_action("db/executeSql", {"sql": "DELETE FROM oc_product_geo"})
print(f"  {r}")

# Verify
r2 = post_action("db/select", {"sql": "SELECT COUNT(*) as cnt FROM oc_product_geo"})
print(f"  After truncate: {r2['rows'][0]['cnt']} rows")

print("=== DONE ===")
