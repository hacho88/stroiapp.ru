import urllib.request, ssl, json, socket, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ip = socket.gethostbyname("stroiapp.ru")
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

ok = 0
fail = 0

# 1. Main page
try:
    req = urllib.request.Request(f"https://{ip}/", headers={"Host": "stroiapp.ru"})
    r = urllib.request.urlopen(req, timeout=15, context=ctx)
    body = r.read().decode("utf-8", errors="replace")
    css = re.findall(r'<link[^>]*href=["\']([^"\']*\.css[^"\']*)["\']', body, re.I)
    desc = re.search(r'<meta name="description" content="([^"]*)"', body, re.I)
    escaped = desc and "&lt;" in desc.group(1)
    print(f"1. stroiapp.ru:      HTTP {r.status}, {len(body)} bytes, {len(css)} CSS, meta={'OK' if not escaped else 'BROKEN'}")
    ok += 1
except Exception as e:
    print(f"1. stroiapp.ru:      FAIL - {e}")
    fail += 1

# 2. Blog
try:
    req = urllib.request.Request(f"https://{ip}/index.php?route=blog/blog", headers={"Host": "stroiapp.ru"})
    r = urllib.request.urlopen(req, timeout=15, context=ctx)
    print(f"2. Blog:             HTTP {r.status}, {len(r.read())} bytes")
    ok += 1
except Exception as e:
    print(f"2. Blog:             FAIL - {e}")
    fail += 1

# 3. API health
try:
    d = json.dumps({}).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action=site/health", data=d, headers=h, method="POST")
    r = urllib.request.urlopen(req, timeout=15, context=ctx)
    data = json.loads(r.read().decode())
    print(f"3. API health:       {data.get('status')} (PHP {data.get('php')})")
    ok += 1
except Exception as e:
    print(f"3. API health:       FAIL - {e}")
    fail += 1

# 4. DB query
try:
    d = json.dumps({"sql": "SELECT COUNT(*) as cnt FROM oc_openproduct"}).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action=db/executeSql", data=d, headers=h, method="POST")
    r = urllib.request.urlopen(req, timeout=15, context=ctx)
    data = json.loads(r.read().decode())
    rows = data.get("rows", [])
    print(f"4. DB query:         {rows}")
    ok += 1
except Exception as e:
    print(f"4. DB query:         FAIL - {e}")
    fail += 1

# 5. Backend
try:
    r = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5)
    print(f"5. Backend:          {r.read().decode()}")
    ok += 1
except Exception as e:
    print(f"5. Backend:          FAIL - {e}")
    fail += 1

# 6. Backend - blog auto-status
try:
    r = urllib.request.urlopen("http://127.0.0.1:8000/api/blog/auto-status", timeout=5)
    print(f"6. Blog auto-status: {r.read().decode()[:100]}")
    ok += 1
except Exception as e:
    print(f"6. Blog auto-status: FAIL - {e}")
    fail += 1

# 7. Backend - dashboard stats
try:
    r = urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard/stats", timeout=5)
    print(f"7. Dashboard stats:  {r.read().decode()[:100]}")
    ok += 1
except Exception as e:
    print(f"7. Dashboard stats:  FAIL - {e}")
    fail += 1

# 8. Frontend
try:
    r = urllib.request.urlopen("http://127.0.0.1:5173/", timeout=5)
    body = r.read().decode()
    print(f"8. Frontend:         HTTP {r.status}, {len(body)} bytes, root={'yes' if 'id=\"root\"' in body else 'no'}")
    ok += 1
except Exception as e:
    print(f"8. Frontend:         FAIL - {e}")
    fail += 1

print(f"\n{'='*40}")
print(f"Result: {ok} OK, {fail} FAIL")
if fail == 0:
    print("ALL GOOD!")
