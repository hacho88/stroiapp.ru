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

r = post_action("db/select", {"sql": "SELECT COUNT(*) as total, COUNT(DISTINCT product_id) as products FROM oc_product_geo"})
total = r['rows'][0]['total']
products = r['rows'][0]['products']
print(f"Geo pages: {total} | Products done: {products}/585")
pct = int(products) / 585 * 100
print(f"Progress: {pct:.1f}%")

# Estimate time
# Each product takes ~30s (DeepSeek + 213 cities + insert)
remaining = 585 - int(products)
eta_min = remaining * 30 / 60
print(f"Estimated remaining: {eta_min:.0f} min ({eta_min/60:.1f} hours)")
