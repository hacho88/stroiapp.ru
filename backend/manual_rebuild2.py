import urllib.request, ssl, json, socket

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

# Get all modifications XML
r1 = post("db/select", {"sql": "SELECT * FROM oc_openmodification WHERE status = 1"})
mods = r1.get('rows', [])
print(f"Active modifications: {len(mods)}")

# Build a PHP script with the XML hardcoded
# Actually, let's just pass the XML via the PHP script reading from DB
rebuild_php = """<?php
class ControllerApiManualRebuild2 extends Controller {
    public function index() {
        error_reporting(E_ALL);
        ini_set('display_errors', 1);
        
        $modifications = $this->db->query("SELECT * FROM " . DB_PREFIX . "modification WHERE status = 1");
        echo "Modifications: " . $modifications->num_rows . "\\n";
        
        $mod_dir = DIR_STORAGE . 'modification/';
        
        foreach ($modifications->rows as $mod) {
            echo "\\nProcessing: " . $mod['name'] . "\\n";
            $xml = $mod['xml'];
            if (empty($xml)) { echo "  No XML\\n"; continue; }
            
            $dom = new DOMDocument('1.0', 'UTF-8');
            $dom->preserveWhiteSpace = false;
            if (!@$dom->loadXML($xml)) { echo "  Invalid XML\\n"; continue; }
            
            $files = $dom->getElementsByTagName('file');
            foreach ($files as $file) {
                // The path attribute contains the full path including filename
                $path_attr = $file->getAttribute('path');
                $name_attr = $file->getAttribute('name');
                
                // Use path if it contains a .php file, otherwise use name
                $filepath = '';
                if (strpos($path_attr, '.php') !== false) {
                    $filepath = $path_attr;
                } elseif ($name_attr) {
                    $filepath = $path_attr . $name_attr;
                }
                
                if (!$filepath) { echo "  No valid file path\\n"; continue; }
                
                // Find original file
                $orig = DIR_APPLICATION . '../' . $filepath;
                if (!file_exists($orig)) {
                    $orig = DIR_APPLICATION . $filepath;
                }
                if (!file_exists($orig)) {
                    echo "  Skip (not found): $filepath\\n";
                    continue;
                }
                
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
                        }
                    }
                }
                
                if ($changed) {
                    $mod_path = $mod_dir . $filepath;
                    $dir_name = dirname($mod_path);
                    if (!is_dir($dir_name)) mkdir($dir_name, 0755, true);
                    file_put_contents($mod_path, $content);
                    echo "  Applied: $filepath\\n";
                } else {
                    echo "  No changes needed: $filepath\\n";
                }
            }
        }
        
        // Add geo routing to seo_url.php
        $mod_seo = $mod_dir . 'catalog/controller/startup/seo_url.php';
        $orig_seo = DIR_APPLICATION . 'controller/startup/seo_url.php';
        if (file_exists($orig_seo) && strpos(file_get_contents($orig_seo), 'Geo page routing') !== false) {
            copy($orig_seo, $mod_seo);
            echo "\\nGeo routing copied to modification cache\\n";
        }
        
        // Clear cache
        $cache_dir = DIR_STORAGE . 'cache/';
        $files = glob($cache_dir . '*');
        $c = 0;
        foreach ($files as $f) { if (is_file($f)) { @unlink($f); $c++; } }
        echo "Cleared $c cache files\\n";
        
        echo "\\nDONE\\n";
    }
}
?>"""

r2 = post("file/writeSafe", {"path": "catalog/controller/api/manual_rebuild2.php", "content": rebuild_php})
print(f"  Write: {r2}")

print("\nExecuting rebuild2...")
url = f"https://{ip}/index.php?route=api/manual_rebuild2"
req = urllib.request.Request(url, headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        result = r.read().decode('utf-8', errors='replace')
        print(f"\n  Result:\n  {result.replace(chr(10), chr(10)+'  ')}")
except Exception as e:
    print(f"\n  Error: {e}")
    if hasattr(e, 'read'):
        print(f"  Body: {e.read().decode('utf-8', errors='replace')[:2000]}")

# Test
print("\n=== Testing site ===")
for test_url, label in [
    (f"https://{ip}/index.php?route=common/home", "Homepage"),
    (f"https://{ip}/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg", "Product page"),
    (f"https://{ip}/geo/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg/himki", "Geo page"),
]:
    req = urllib.request.Request(test_url, headers={"Host": "stroiapp.ru"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            body = r.read()
            print(f"  {label}: HTTP {r.status}, {len(body)} bytes")
            if len(body) > 100:
                print(f"    ✓ Content detected!")
    except Exception as e:
        print(f"  {label}: {e}")

print("\n=== DONE ===")
