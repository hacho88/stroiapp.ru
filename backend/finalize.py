import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ip = "stroiapp.ru"
h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=60):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Update the modification XML to only add the decode block (rewrite already in original)
mod_xml = """<?xml version="1.0" encoding="UTF-8"?>
<modification>
<name>Geo Page SEO Routing</name>
<code>geo_seo_routing</code>
<version>1.1</version>
<author>AI Manager</author>
    <file path="catalog/controller/startup/seo_url.php">
        <operation error="skip">
            <search><![CDATA[array_pop($parts);]]></search>
            <add position="after"><![CDATA[

		// Geo page routing: /geo/product-keyword/city-id
		if (count($parts) >= 3 && $parts[0] == 'geo') {
			$pquery = $this->db->query("SELECT * FROM " . DB_PREFIX . "seo_url WHERE keyword = '" . $this->db->escape($parts[1]) . "' AND store_id = '" . (int)$this->config->get('config_store_id') . "'");
			if ($pquery->num_rows) {
				$purl = explode('=', $pquery->row['query']);
				if ($purl[0] == 'product_id') {
					$this->request->get['product_id'] = $purl[1];
					$this->request->get['city_id'] = $parts[2];
					$this->request->get['route'] = 'product/geo';
					return;
				}
			}
		}
]]></add>
        </operation>
    </file>
</modification>"""

xml_escaped = mod_xml.replace("'", "\\'")
r1 = post("db/executeSql", {"sql": f"UPDATE oc_openmodification SET xml = '{xml_escaped}', version = '1.1' WHERE code = 'geo_seo_routing'"})
print(f"Updated modification: {r1}")

# Verify
r2 = post("db/select", {"sql": "SELECT modification_id, name, code, version, status FROM oc_openmodification WHERE code = 'geo_seo_routing'"})
print(f"Verify: {json.dumps(r2.get('rows', []), ensure_ascii=False)}")

# Now check geo page content - delivery price display
print("\n=== Checking geo page delivery price ===")
import re
url = f"https://{ip}/geo/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg/khimki"
req = urllib.request.Request(url, headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        body = r.read().decode('utf-8', errors='replace')
        title = re.search(r'<title>(.*?)</title>', body)
        if title:
            print(f"  Title: {title.group(1)[:100]}")
        for match in re.finditer(r'[Дд]оставка[^<]{0,100}', body):
            print(f"  Delivery: {match.group()[:100]}")
            break
        # Check meta description
        meta = re.search(r'<meta name="description" content="([^"]*)"', body)
        if meta:
            print(f"  Meta: {meta.group(1)[:120]}")
        # Check h1
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.DOTALL)
        if h1:
            print(f"  H1: {h1.group(1).strip()[:80]}")
except Exception as e:
    print(f"  Error: {e}")

# Check a second city
print("\n=== Checking Balashikha ===")
url2 = f"https://{ip}/geo/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg/balashikha"
req2 = urllib.request.Request(url2, headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req2, timeout=15, context=ctx) as r:
        body2 = r.read().decode('utf-8', errors='replace')
        title2 = re.search(r'<title>(.*?)</title>', body2)
        if title2:
            print(f"  Title: {title2.group(1)[:100]}")
        for match in re.finditer(r'[Дд]оставка[^<]{0,100}', body2):
            print(f"  Delivery: {match.group()[:100]}")
            break
        meta2 = re.search(r'<meta name="description" content="([^"]*)"', body2)
        if meta2:
            print(f"  Meta: {meta2.group(1)[:120]}")
except Exception as e:
    print(f"  Error: {e}")

# Check generation progress
print("\n=== Generation progress ===")
r3 = post("db/select", {"sql": "SELECT COUNT(DISTINCT product_id) as products, COUNT(*) as total FROM oc_product_geo"})
print(f"  Geo pages: {json.dumps(r3.get('rows', []), ensure_ascii=False)}")

# Clean up temporary PHP files
print("\n=== Cleaning up temporary PHP files ===")
cleanup_files = [
    "catalog/controller/api/db_info.php",
    "catalog/controller/api/check_errors.php",
    "catalog/controller/api/check_mod.php",
    "catalog/controller/api/clear_mod_cache.php",
    "catalog/controller/api/fix_mod_cache.php",
    "catalog/controller/api/manual_rebuild.php",
    "catalog/controller/api/manual_rebuild2.php",
    "catalog/controller/api/rebuild_mods.php",
    "catalog/controller/api/rebuild_mods2.php",
    "catalog/controller/api/rebuild_mods3.php",
    "catalog/controller/api/rebuild_mods4.php",
    "catalog/controller/api/refresh_mods.php",
    "catalog/controller/api/refresh_mods5.php",
    "catalog/controller/api/restore_mods.php",
]
for f in cleanup_files:
    try:
        r4 = post("file/writeSafe", {"path": f, "content": "<?php // deleted"})
        print(f"  {f}: cleaned")
    except:
        pass

# Clear cache
r5 = post("site/clearCache", {})
print(f"\nCache cleared: {r5}")

print("\n=== DONE ===")
