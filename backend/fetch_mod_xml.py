import urllib.request, ssl, json, socket, time, re, os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
socket.setdefaulttimeout(60)

try:
    socket.getaddrinfo("stroiapp.ru", 443)
    BASE = "https://stroiapp.ru"
    h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token"}
except Exception:
    BASE = "https://188.225.23.151"
    h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, data=None, retries=5):
    url = f"{BASE}/index.php?route=api/ai_manager&action={action}"
    d = json.dumps(data).encode() if data else b""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=d, headers=h, method="POST")
            with urllib.request.urlopen(req, context=ctx, timeout=60) as r:
                return json.loads(r.read().decode("utf-8-sig"))
        except Exception as e:
            if attempt == retries - 1:
                return {"error": str(e)}
            time.sleep(3)

# Get XML for mods 3, 6, 17
out_dir = r"d:\Projects\ai.stroiapp.ru\ai.stroiapp.ru\backend\mod_xml"
os.makedirs(out_dir, exist_ok=True)

for mod_id in [3, 6, 17]:
    r = post("db/select", {"sql": f"SELECT modification_id, name, xml FROM oc_openmodification WHERE modification_id = {mod_id}"})
    if "rows" in r and r["rows"]:
        row = r["rows"][0]
        xml = row.get("xml", "")
        name = row.get("name", f"mod_{mod_id}")
        fname = f"mod_{mod_id}_{name.replace(' ', '_').replace('/', '_')}.xml"
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"Saved {fname} ({len(xml)} chars)")
    else:
        print(f"Mod {mod_id}: {json.dumps(r, ensure_ascii=False)[:200]}")

print("DONE")
