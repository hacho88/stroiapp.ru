import urllib.request, ssl, json, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ip = "188.225.23.151"
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def get_route(route, timeout=120):
    req = urllib.request.Request(f"https://{ip}/index.php?route={route}", headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

def post(action, payload, timeout=30):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Check current state
r = post("db/executeSql", {"sql": "SELECT COUNT(*) as cnt FROM `oc_openseo_url` WHERE `query` LIKE 'product/product&geo_id=%'"})
current = int(r.get("rows", [{}])[0].get("cnt", 0))
print(f"Current geo SEO URLs: {current}")
print(f"Remaining: {124605 - current}")

total_inserted = 0
step = 13  # Continue from where we stopped

print(f"\n=== Continuing from step {step} ===")
while step <= 30:
    try:
        result = get_route(f"api/gen_geo_seo&step={step}", timeout=120)
        inserted = result.get("inserted", 0)
        total_inserted += inserted
        print(f"  Step {step}: inserted={inserted}, skipped={result.get('skipped',0)}, has_more={result.get('has_more')}")
        if not result.get("has_more"):
            print("  DONE!")
            break
        step += 1
        time.sleep(2)
    except Exception as e:
        print(f"  Step {step}: ERROR {str(e)[:80]}")
        time.sleep(5)
        step += 1

# Final
r2 = post("db/executeSql", {"sql": "SELECT COUNT(*) as cnt FROM `oc_openseo_url` WHERE `query` LIKE 'product/product&geo_id=%'"})
geo_count = r2.get("rows", [{}])[0].get("cnt", '?')
r3 = post("db/executeSql", {"sql": "SELECT COUNT(*) as cnt FROM `oc_openseo_url`"})
total_count = r3.get("rows", [{}])[0].get("cnt", '?')
print(f"\n=== FINAL ===")
print(f"  Geo SEO URLs: {geo_count}")
print(f"  Total SEO URLs: {total_count}")
print(f"  Inserted this run: {total_inserted}")
