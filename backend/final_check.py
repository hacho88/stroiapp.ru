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

# 1. Template vs AI
r1 = post_action("db/select", {"sql": "SELECT COUNT(*) as template_cnt FROM oc_product_geo WHERE description LIKE '%профессиональное решение для строительных%'"})
r2 = post_action("db/select", {"sql": "SELECT COUNT(*) as total FROM oc_product_geo"})
template_cnt = int(r1['rows'][0]['template_cnt'])
total = int(r2['rows'][0]['total'])
ai_cnt = total - template_cnt
print(f"AI descriptions: {ai_cnt}/{total} ({ai_cnt/total*100:.1f}%)")
print(f"Template fallback: {template_cnt}/{total}")

# 2. Uniqueness across ALL products
r3 = post_action("db/select", {"sql": "SELECT COUNT(DISTINCT description) as uniq, COUNT(*) as total FROM oc_product_geo"})
uniq = int(r3['rows'][0]['uniq'])
print(f"\nGlobal uniqueness: {uniq}/{total} ({uniq/total*100:.1f}%)")

# 3. Per-product uniqueness for 3 products
for pid in [50, 52, 78]:
    r = post_action("db/select", {"sql": f"SELECT COUNT(DISTINCT description) as u, COUNT(*) as t FROM oc_product_geo WHERE product_id={pid}"})
    u = int(r['rows'][0]['u'])
    t = int(r['rows'][0]['t'])
    print(f"  Product {pid}: {u}/{t} unique ({u/t*100:.1f}%)")

# 4. Test live page
print("\n=== Live page test ===")
try:
    req = urllib.request.Request(
        f"{ip_url}/index.php?route=product/geo&product_id=50&city_id=khimki",
        headers={"Host": hostname, "User-Agent": "Mozilla/5.0"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        html = resp.read().decode("utf-8-sig")
    import re
    title = re.search(r'<title>([^<]+)</title>', html)
    print(f"  HTTP {resp.status} | Title: {title.group(1) if title else 'NONE'}")
    print(f"  Has AI text: {'высококачественная' in html or 'сертифицирована' in html}")
except Exception as e:
    print(f"  Error: {e}")

# 5. DeepSeek API cost estimate
products_done = 31
products_total = 585
api_calls = products_total  # 1 per product
cost_per_call = 0.0014  # ~$0.0014 per call (600 tokens in, 600 out)
total_cost = api_calls * cost_per_call
print(f"\nDeepSeek API cost: ~${total_cost:.2f} for {products_total} products")
