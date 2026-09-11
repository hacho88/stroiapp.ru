import urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ip = "188.225.23.151"
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=60):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

def get_route(route, timeout=120):
    req = urllib.request.Request(f"https://{ip}/index.php?route={route}", headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Step 1: Upload gen_geo_seo.php
print("=== Uploading gen_geo_seo.php ===")
with open(r"D:\Projects\ai.stroiapp.ru\stroiapp.ru\public_html\catalog\controller\api\gen_geo_seo.php", "r", encoding="utf-8") as f:
    content = f.read()
r = post("file/writeSafe", {"path": "catalog/controller/api/gen_geo_seo.php", "content": content})
print(f"  Upload: {r}")

time.sleep(2)

# Step 2: Get info
print("\n=== Step 0: Info ===")
info = get_route("api/gen_geo_seo&step=0")
print(f"  {json.dumps(info, ensure_ascii=False)}")

total_inserted = 0
step = 1
max_steps = 30  # 30 * 5000 = 150,000 max

# Step 3: Run batches
print(f"\n=== Generating SEO URLs (batch=5000) ===")
while step <= max_steps:
    try:
        result = get_route(f"api/gen_geo_seo&step={step}", timeout=120)
        inserted = result.get("inserted", 0)
        total_inserted += inserted
        print(f"  Step {step}: inserted={inserted}, skipped={result.get('skipped',0)}, errors={result.get('errors',0)}, has_more={result.get('has_more')}")
        if result.get("samples"):
            for s in result["samples"]:
                print(f"    {s}")
        if not result.get("has_more"):
            print(f"\n  DONE! No more pages.")
            break
        step += 1
        time.sleep(1)
    except Exception as e:
        print(f"  Step {step}: ERROR {str(e)[:100]}")
        break

# Final count
print(f"\n=== Final ===")
print(f"  Total inserted: {total_inserted}")
r2 = post("db/executeSql", {"sql": "SELECT COUNT(*) as cnt FROM `oc_openseo_url` WHERE `query` LIKE 'product/product&geo_id=%'"})
print(f"  Geo SEO URLs in DB: {r2.get('rows', [{}])[0].get('cnt', '?')}")

r3 = post("db/executeSql", {"sql": "SELECT COUNT(*) as cnt FROM `oc_openseo_url`"})
print(f"  Total SEO URLs: {r3.get('rows', [{}])[0].get('cnt', '?')}")

# Sample
r4 = post("db/executeSql", {"sql": "SELECT `query`, `keyword` FROM `oc_openseo_url` WHERE `query` LIKE 'product/product&geo_id=%' LIMIT 10"})
print(f"\n  Sample geo SEO URLs:")
for row in r4.get("rows", []):
    print(f"    {row['query']} -> /{row['keyword']}")

print("\nDONE")
