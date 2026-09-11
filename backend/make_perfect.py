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

# 1. Create an OpenCart modification (ocmod) that adds geo-routing to seo_url.php
# This ensures geo routing survives any modification cache refresh
mod_xml = """<?xml version="1.0" encoding="UTF-8"?>
<modification>
<name>Geo Page SEO Routing</name>
<code>geo_seo_routing</code>
<version>1.0</version>
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
    <file path="catalog/controller/startup/seo_url.php">
        <operation error="skip">
            <search><![CDATA[if ($data['route'] == 'product/product' && $key == 'product_id') {]]></search>
            <add position="before"><![CDATA[
			if ($data['route'] == 'product/geo' && $key == 'product_id') {
				$query = $this->db->query("SELECT * FROM " . DB_PREFIX . "seo_url WHERE `query` = '" . $this->db->escape('product_id=' . (int)$value) . "' AND store_id = '" . (int)$this->config->get('config_store_id') . "' AND language_id = '" . (int)$this->config->get('config_language_id') . "'");
				if ($query->num_rows && $query->row['keyword']) {
					$url .= '/geo/' . $query->row['keyword'];
					if (isset($data['city_id'])) {
						$url .= '/' . $data['city_id'];
						unset($data['city_id']);
					}
					unset($data[$key]);
					unset($data['route']);
				}
			}
]]></add>
        </operation>
    </file>
</modification>"""

# Insert modification into DB
print("=== Adding geo_seo_routing modification to DB ===")

# Check if already exists
r0 = post("db/select", {"sql": "SELECT * FROM oc_openmodification WHERE code = 'geo_seo_routing'"})
if r0.get('rows'):
    print(f"  Already exists (id={r0['rows'][0]['modification_id']}), updating XML...")
    r1 = post("db/executeSql", {"sql": f"UPDATE oc_openmodification SET xml = '{mod_xml.replace(chr(39), chr(92)+chr(39))}', status = 1 WHERE code = 'geo_seo_routing'"})
else:
    # Escape single quotes for SQL
    xml_escaped = mod_xml.replace("'", "\\'")
    r1 = post("db/executeSql", {"sql": f"INSERT INTO oc_openmodification (extension_install_id, name, code, author, version, link, xml, status, date_added) VALUES (0, 'Geo Page SEO Routing', 'geo_seo_routing', 'AI Manager', '1.0', '', '{xml_escaped}', 1, NOW())"})
print(f"  Insert/Update: {r1}")

# 2. Also restore original seo_url.php (remove geo code from it, since the modification will add it)
print("\n=== Restoring original seo_url.php (without inline geo code) ===")
# Read current file
import urllib.parse
url = f"https://{ip}/index.php?route=api/ai_manager&action=file/readSafe&path={urllib.parse.quote('catalog/controller/startup/seo_url.php')}"
req = urllib.request.Request(url, headers={"X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}, method="GET")
with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
    r2 = json.loads(r.read().decode("utf-8-sig"))
content = r2.get("content", "")
print(f"  Current file: {len(content)} chars, has geo: {'Geo page routing' in content}")

# Remove the inline geo routing block (the modification will add it)
if "Geo page routing" in content:
    # Remove the decode block
    start_marker = "\n\t\t// Geo page routing: /geo/product-keyword/city-id\n"
    end_marker = "\t\t}\n\t\t}\n\t\t}\n\n\t\tforeach"
    idx = content.find(start_marker)
    if idx >= 0:
        end_idx = content.find("\n\t\tforeach", idx)
        if end_idx >= 0:
            content = content[:idx] + "\n" + content[end_idx+1:]
            print(f"  Removed decode block, new size: {len(content)}")
    
    # Remove the rewrite block
    rewrite_marker = "if ($data['route'] == 'product/geo'"
    idx2 = content.find(rewrite_marker)
    if idx2 >= 0:
        # Find the closing brace - it's before the next if block
        next_if = content.find("if ($data['route'] == 'product/product'", idx2)
        if next_if >= 0:
            # Find the opening tab before this block
            block_start = content.rfind("\n\t\t\t", 0, idx2)
            content = content[:block_start+1] + "\t\t\t" + content[next_if:]
            print(f"  Removed rewrite block, new size: {len(content)}")
    
    r3 = post("file/writeSafe", {"path": "catalog/controller/startup/seo_url.php", "content": content})
    print(f"  Write: {r3}")

# 3. Refresh modification cache to apply the new modification
print("\n=== Refreshing modification cache ===")
refresh_php = """<?php
class ControllerApiRefreshMods5 extends Controller {
    public function index() {
        error_reporting(E_ALL);
        ini_set('display_errors', 1);
        
        $modifications = $this->db->query("SELECT * FROM " . DB_PREFIX . "modification WHERE status = 1");
        echo "Modifications: " . $modifications->num_rows . "\\n";
        
        $mod_dir = DIR_STORAGE . 'modification/';
        
        // Clear modification directory first
        $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($mod_dir, RecursiveDirectoryIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
        foreach($it as $f) {
            if ($f->isFile() && $f->getFilename() != 'index.html') {
                @unlink($f->getPathname());
            } elseif ($f->isDir()) {
                @rmdir($f->getPathname());
            }
        }
        
        // Recreate base dirs
        $dirs = ['', 'admin', 'catalog', 'system', 'catalog/controller', 'catalog/controller/startup', 'catalog/controller/product', 'catalog/controller/common', 'catalog/controller/checkout', 'catalog/controller/account', 'catalog/controller/mail', 'catalog/controller/api', 'catalog/controller/information', 'catalog/controller/extension', 'catalog/model', 'catalog/model/catalog', 'catalog/model/account', 'catalog/model/design', 'admin/controller', 'admin/controller/common', 'admin/controller/catalog', 'admin/controller/extension', 'admin/model', 'admin/model/catalog'];
        foreach ($dirs as $d) {
            $path = $mod_dir . $d;
            if (!is_dir($path)) mkdir($path, 0755, true);
            @file_put_contents($path . '/index.html', '');
        }
        
        $applied = 0;
        foreach ($modifications->rows as $mod) {
            echo "\\nProcessing: " . $mod['name'] . "\\n";
            $xml = $mod['xml'];
            if (empty($xml)) { echo "  No XML\\n"; continue; }
            
            $dom = new DOMDocument('1.0', 'UTF-8');
            $dom->preserveWhiteSpace = false;
            if (!@$dom->loadXML($xml)) { echo "  Invalid XML\\n"; continue; }
            
            $files = $dom->getElementsByTagName('file');
            foreach ($files as $file) {
                $path_attr = $file->getAttribute('path');
                $filepath = '';
                if (strpos($path_attr, '.php') !== false) {
                    $filepath = $path_attr;
                } else {
                    $name_attr = $file->getAttribute('name');
                    $filepath = $path_attr . $name_attr;
                }
                if (!$filepath) { echo "  No filepath\\n"; continue; }
                
                $orig = DIR_APPLICATION . '../' . $filepath;
                if (!file_exists($orig)) $orig = DIR_APPLICATION . $filepath;
                if (!file_exists($orig)) { echo "  Skip: $filepath\\n"; continue; }
                
                $content = file_get_contents($orig);
                $changed = false;
                
                $operations = $file->getElementsByTagName('operation');
                foreach ($operations as $op) {
                    $searches = $op->getElementsByTagName('search');
                    $adds = $op->getElementsByTagName('add');
                    for ($i = 0; $i < $searches->length; $i++) {
                        $search_text = $searches->item($i)->textContent;
                        $position = $searches->item($i)->getAttribute('position') ?: 'replace';
                        $add_text = $adds->length > $i ? $adds->item($i)->textContent : '';
                        
                        if (strpos($content, $search_text) !== false) {
                            if ($position == 'replace') {
                                $content = str_replace($search_text, $add_text, $content);
                            } elseif ($position == 'before') {
                                $content = str_replace($search_text, $add_text . $search_text, $content);
                            } elseif ($position == 'after') {
                                $content = str_replace($search_text, $search_text . $add_text, $content);
                            }
                            $changed = true;
                        } else {
                            echo "  Search not found in $filepath\\n";
                        }
                    }
                }
                
                if ($changed) {
                    $mod_path = $mod_dir . $filepath;
                    $dir_name = dirname($mod_path);
                    if (!is_dir($dir_name)) mkdir($dir_name, 0755, true);
                    file_put_contents($mod_path, $content);
                    echo "  Applied: $filepath\\n";
                    $applied++;
                }
            }
        }
        
        echo "\\nTotal applied: $applied files\\n";
        
        // Clear cache
        $cache_dir = DIR_STORAGE . 'cache/';
        $files = glob($cache_dir . '*');
        $c = 0;
        foreach ($files as $f) { if (is_file($f)) { @unlink($f); $c++; } }
        echo "Cleared $c cache files\\n";
        
        echo "DONE\\n";
    }
}
?>"""

r4 = post("file/writeSafe", {"path": "catalog/controller/api/refresh_mods5.php", "content": refresh_php})
print(f"  Write: {r4}")

url2 = f"https://{ip}/index.php?route=api/refresh_mods5"
req2 = urllib.request.Request(url2, headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req2, timeout=60, context=ctx) as r:
        result = r.read().decode('utf-8', errors='replace')
        print(f"  Result:\n  {result.replace(chr(10), chr(10)+'  ')}")
except Exception as e:
    print(f"  Error: {e}")
    if hasattr(e, 'read'):
        print(f"  Body: {e.read().decode('utf-8', errors='replace')[:1000]}")

# 4. Test
print("\n=== Testing site ===")
for test_url, label in [
    (f"https://{ip}/index.php?route=common/home", "Homepage"),
    (f"https://{ip}/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg", "Product page"),
    (f"https://{ip}/geo/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg/khimki", "Geo page"),
]:
    req = urllib.request.Request(test_url, headers={"Host": "stroiapp.ru"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            body = r.read()
            print(f"  {label}: HTTP {r.status}, {len(body)} bytes")
            if len(body) > 100:
                print(f"    ✓ Content OK")
    except Exception as e:
        print(f"  {label}: {e}")

print("\n=== DONE ===")
