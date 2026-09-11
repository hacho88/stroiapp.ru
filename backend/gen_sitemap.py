import urllib.request, ssl, json, socket, re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ip = socket.gethostbyname("stroiapp.ru")
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=60):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# 1. Get all product SEO keywords
print("=== Fetching product SEO keywords ===")
r1 = post("db/select", {"sql": "SELECT keyword, query FROM oc_openseo_url WHERE query LIKE 'product_id=%' AND store_id = 0"})
keywords = r1.get('rows', [])
print(f"  Found {len(keywords)} product keywords")

# 2. Get all distinct city_ids from geo pages
r2 = post("db/select", {"sql": "SELECT DISTINCT city_id FROM oc_product_geo"})
cities = [row['city_id'] for row in r2.get('rows', [])]
print(f"  Found {len(cities)} cities with geo pages")

# 3. Get product IDs that have geo pages
r3 = post("db/select", {"sql": "SELECT DISTINCT product_id FROM oc_product_geo"})
geo_products = set(int(row['product_id']) for row in r3.get('rows', []))
print(f"  Found {len(geo_products)} products with geo pages")

# 4. Build sitemap entries
print("\n=== Building sitemap ===")
base_url = "https://stroiapp.ru"
urls = []

# Static pages
static_urls = [
    f"{base_url}/",
    f"{base_url}/o-kompanii",
    f"{base_url}/kontakty",
    f"{base_url}/dostavka",
    f"{base_url}/oplata",
    f"{base_url}/garantiya",
]
for u in static_urls:
    urls.append(f"  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>")

# Product pages
product_count = 0
for kw_row in keywords:
    query = kw_row['query']
    keyword = kw_row['keyword']
    pid = int(query.split('=')[1])
    urls.append(f"  <url><loc>{base_url}/{keyword}</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>")
    product_count += 1

# Geo pages
geo_count = 0
for kw_row in keywords:
    keyword = kw_row['keyword']
    pid = int(kw_row['query'].split('=')[1])
    if pid in geo_products:
        for city_id in cities:
            urls.append(f"  <url><loc>{base_url}/geo/{keyword}/{city_id}</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>")
            geo_count += 1

print(f"  Product URLs: {product_count}")
print(f"  Geo URLs: {geo_count}")
print(f"  Total URLs: {len(urls)}")

# 5. Write sitemap
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sitemap += '\n'.join(urls)
sitemap += '\n</urlset>\n'

print(f"\n  Sitemap size: {len(sitemap)} bytes")

# Split if too large (limit ~1MB per write to avoid 400)
if len(sitemap) > 1000000:
    chunk_size = 500
    chunks = [urls[i:i+chunk_size] for i in range(0, len(urls), chunk_size)]
    print(f"  Splitting into {len(chunks)} sitemaps...")
    
    # Write a PHP script that generates sitemaps on the server directly from DB
    gen_php = """<?php
class ControllerApiGenSitemap extends Controller {
    public function index() {
        error_reporting(E_ALL);
        ini_set('display_errors', 1);
        $base = 'https://stroiapp.ru';
        
        // Get product keywords
        $products = $this->db->query("SELECT keyword, query FROM " . DB_PREFIX . "seo_url WHERE query LIKE 'product_id=%' AND store_id = 0");
        
        // Get cities
        $cities = $this->db->query("SELECT DISTINCT city_id FROM oc_product_geo");
        $city_ids = [];
        foreach ($cities->rows as $c) $city_ids[] = $c['city_id'];
        
        // Get products with geo pages
        $geo_products = $this->db->query("SELECT DISTINCT product_id FROM oc_product_geo");
        $geo_pids = [];
        foreach ($geo_products->rows as $g) $geo_pids[$g['product_id']] = true;
        
        // Build all URLs
        $urls = [];
        // Static
        $urls[] = $base . '/';
        $urls[] = $base . '/o-kompanii';
        $urls[] = $base . '/kontakty';
        $urls[] = $base . '/dostavka';
        $urls[] = $base . '/oplata';
        $urls[] = $base . '/garantiya';
        
        // Products
        $product_urls = [];
        foreach ($products->rows as $p) {
            $urls[] = $base . '/' . $p['keyword'];
            $pid = (int)str_replace('product_id=', '', $p['query']);
            if (isset($geo_pids[$pid])) {
                foreach ($city_ids as $cid) {
                    $urls[] = $base . '/geo/' . $p['keyword'] . '/' . $cid;
                }
            }
        }
        
        echo "Total URLs: " . count($urls) . "\\n";
        
        // Split into chunks of 5000
        $chunk_size = 5000;
        $chunks = array_chunk($urls, $chunk_size);
        echo "Sitemaps: " . count($chunks) . "\\n";
        
        $doc_root = dirname(DIR_APPLICATION);
        
        for ($i = 0; $i < count($chunks); $i++) {
            $xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\\n";
            $xml .= '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\\n";
            foreach ($chunks[$i] as $u) {
                $xml .= '  <url><loc>' . htmlspecialchars($u) . '</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>' . "\\n";
            }
            $xml .= '</urlset>' . "\\n";
            
            $fname = 'sitemap-' . ($i+1) . '.xml';
            file_put_contents($doc_root . '/' . $fname, $xml);
            echo "  $fname: " . count($chunks[$i]) . " URLs, " . strlen($xml) . " bytes\\n";
        }
        
        // Sitemap index
        $index = '<?xml version="1.0" encoding="UTF-8"?>' . "\\n";
        $index .= '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\\n";
        for ($i = 0; $i < count($chunks); $i++) {
            $index .= '  <sitemap><loc>' . $base . '/sitemap-' . ($i+1) . '.xml</loc></sitemap>' . "\\n";
        }
        $index .= '</sitemapindex>' . "\\n";
        file_put_contents($doc_root . '/sitemap.xml', $index);
        echo "  sitemap.xml (index): " . strlen($index) . " bytes\\n";
        
        echo "DONE\\n";
    }
}
?>"""
    
    r_php = post("file/writeSafe", {"path": "catalog/controller/api/gen_sitemap.php", "content": gen_php})
    print(f"  PHP script: {r_php}")
    
    url2 = f"https://{ip}/index.php?route=api/gen_sitemap"
    req2 = urllib.request.Request(url2, headers={"Host": "stroiapp.ru"})
    try:
        with urllib.request.urlopen(req2, timeout=120, context=ctx) as r:
            result = r.read().decode('utf-8', errors='replace')
            print(f"  Result:\n  {result.replace(chr(10), chr(10)+'  ')}")
    except Exception as e:
        print(f"  Error: {e}")
        if hasattr(e, 'read'):
            print(f"  Body: {e.read().decode('utf-8', errors='replace')[:500]}")
    
    # Cleanup
    post("file/writeSafe", {"path": "catalog/controller/api/gen_sitemap.php", "content": "<?php // deleted"})
else:
    r4 = post("file/writeSafe", {"path": "sitemap.xml", "content": sitemap})
    print(f"  sitemap.xml: {r4}")

# 6. Verify
print("\n=== Verifying sitemap ===")
req = urllib.request.Request(f"https://{ip}/sitemap.xml", headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        body = r.read()
        print(f"  HTTP {r.status}, {len(body)} bytes")
        # Count URLs
        count = body.decode('utf-8', errors='replace').count('<url><loc>')
        print(f"  URLs in sitemap: {count}")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== DONE ===")
