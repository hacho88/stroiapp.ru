import urllib.request, ssl, json, re, socket

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

# 1. Test SEO URL geo pages with delivery prices
print("=== SEO URL geo pages ===")
for city, slug in [("Химки", "khimki"), ("Балашиха", "balashikha"), ("Москва", "moscow")]:
    url = f"https://{ip}/geo/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg/{slug}"
    req = urllib.request.Request(url, headers={"Host": "stroiapp.ru"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            body = r.read().decode('utf-8', errors='replace')
            title = re.search(r'<title>(.*?)</title>', body)
            meta = re.search(r'<meta name="description" content="([^"]*)"', body)
            h1 = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.DOTALL)
            print(f"\n{city} ({slug}):")
            print(f"  HTTP {r.status}, {len(body)} bytes")
            if title: print(f"  Title: {title.group(1)[:100]}")
            if meta: print(f"  Meta: {meta.group(1)[:120]}")
            if h1:
                clean = re.sub(r'<[^>]+>', '', h1.group(1)).strip()
                print(f"  H1: {clean[:80]}")
            # Find delivery text
            for m in re.finditer(r'[Дд]оставка[^<]{0,100}', body):
                print(f"  Delivery: {m.group()[:100]}")
                break
    except Exception as e:
        print(f"  {city}: {e}")

# 2. Check delivery costs in DB
print("\n=== DB delivery costs (product 50) ===")
r1 = post("db/select", {"sql": "SELECT city_id, city_name, delivery_cost, delivery_time_hours FROM oc_product_geo WHERE product_id = 50 AND city_id IN ('moscow', 'khimki', 'balashikha', 'tver', 'podolsk', 'dolgoprudny', 'mytishchi') ORDER BY delivery_cost"})
for row in r1.get('rows', []):
    print(f"  {row['city_name']:20s}: {row['delivery_cost']}₽, {row['delivery_time_hours']}h")

# 3. Generation progress
r2 = post("db/select", {"sql": "SELECT COUNT(DISTINCT product_id) as products, COUNT(*) as total FROM oc_product_geo"})
print(f"\nGeneration: {json.dumps(r2.get('rows', []), ensure_ascii=False)}")

# 4. Check modification is in DB
r3 = post("db/select", {"sql": "SELECT modification_id, name, code, version, status FROM oc_openmodification WHERE code = 'geo_seo_routing'"})
print(f"\nGeo modification: {json.dumps(r3.get('rows', []), ensure_ascii=False)}")

# 5. Verify modification cache has geo routing
check_php = """<?php
class ControllerApiVerifyGeo extends Controller {
    public function index() {
        $mod_seo = DIR_STORAGE . 'modification/catalog/controller/startup/seo_url.php';
        if (file_exists($mod_seo)) {
            $content = file_get_contents($mod_seo);
            echo "mod_seo_exists=YES\\n";
            echo "mod_seo_size=" . filesize($mod_seo) . "\\n";
            echo "has_geo_decode=" . (strpos($content, 'Geo page routing') !== false ? 'YES' : 'NO') . "\\n";
            // Count modification files
            $mod_dir = DIR_STORAGE . 'modification/';
            $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($mod_dir, RecursiveDirectoryIterator::SKIP_DOTS));
            $count = 0;
            foreach($it as $f) { if ($f->isFile() && $f->getFilename() != 'index.html') $count++; }
            echo "total_mod_files=$count\\n";
        } else {
            echo "mod_seo_exists=NO\\n";
        }
    }
}
?>"""
r4 = post("file/writeSafe", {"path": "catalog/controller/api/verify_geo.php", "content": check_php})
url2 = f"https://{ip}/index.php?route=api/verify_geo"
req2 = urllib.request.Request(url2, headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req2, timeout=15, context=ctx) as r:
        print(f"\nVerification:\n  {r.read().decode('utf-8', errors='replace').replace(chr(10), chr(10)+'  ')}")
except Exception as e:
    print(f"\nVerification error: {e}")

# Clean up
post("file/writeSafe", {"path": "catalog/controller/api/verify_geo.php", "content": "<?php // deleted"})

print("\nDONE")
