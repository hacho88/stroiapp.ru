import urllib.request, ssl, json, socket, time, base64

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    ip = socket.gethostbyname("stroiapp.ru")
except:
    ip = "188.225.23.151"

h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=30):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# PHP patcher — adds blog routing to seo_url.php
patch_php = """<?php
class ControllerApiPatchSeoRouter extends Controller {
    public function index() {
        $catalog_dir = defined('DIR_APPLICATION') ? DIR_APPLICATION : '';
        $router_path = $catalog_dir . 'controller/startup/seo_url.php';

        $r = array();
        $content = file_get_contents($router_path);
        $r[] = "Original size: " . strlen($content);

        // Check if already patched
        if (strpos($content, 'Blog article routing') !== false) {
            $r[] = "Already patched!";
            echo json_encode(array("status" => "ok", "results" => $r));
            exit;
        }

        // Find the geo routing block to insert after it
        $geo_marker = "// Geo page routing: /geo/product-keyword/city-id";
        $geo_pos = strpos($content, $geo_marker);

        if ($geo_pos === false) {
            $r[] = "Geo marker not found, trying alternative";
            // Try to find the foreach loop
            $foreach_marker = "foreach ($parts as $part)";
            $foreach_pos = strpos($content, $foreach_marker);
            if ($foreach_pos === false) {
                $r[] = "Cannot find insertion point!";
                echo json_encode(array("status" => "error", "results" => $r));
                exit;
            }
            // Insert before foreach
            $insert_pos = $foreach_pos;
        } else {
            // Find the end of the geo block — look for the closing } after geo return
            $geo_return = strpos($content, "return;", $geo_pos);
            if ($geo_return === false) {
                $r[] = "Cannot find geo return!";
                echo json_encode(array("status" => "error", "results" => $r));
                exit;
            }
            // Find the closing } of the geo if block
            $insert_pos = strpos($content, "}", $geo_return) + 1;
        }

        // Blog article routing: /blog/article-slug
        $blog_block = '
                        // Blog article routing: /blog/article-slug
                        if (count($parts) >= 2 && $parts[0] == \'blog\') {
                            $this->request->get[\'route\'] = \'blog/blog\';
                            if (isset($parts[1]) && $parts[1]) {
                                $aquery = $this->db->query("SELECT article_id FROM `" . DB_PREFIX . "blog_article` WHERE slug = \'" . $this->db->escape($parts[1]) . "\' AND status = 1");
                                if ($aquery->num_rows) {
                                    $this->request->get[\'article_id\'] = $aquery->row[\'article_id\'];
                                }
                            }
                            return;
                        }
';

        $new_content = substr($content, 0, $insert_pos) . $blog_block . substr($content, $insert_pos);

        // Backup and write
        $backup_path = $router_path . '.bak_' . date('Ymd_His');
        copy($router_path, $backup_path);
        $r[] = "Backup: " . $backup_path;

        file_put_contents($router_path, $new_content);
        $r[] = "New size: " . strlen($new_content);
        $r[] = "Inserted " . strlen($blog_block) . " bytes at position " . $insert_pos;

        // Verify
        $verify = file_get_contents($router_path);
        $r[] = "Verify: Blog routing present: " . (strpos($verify, 'Blog article routing') !== false ? "yes" : "no");

        echo json_encode(array("status" => "ok", "results" => $r));
        exit;
    }
}
"""

print("=== Writing SEO router patcher ===")
r1 = post("file/writeSafe", {"path": "catalog/controller/api/patch_seo.php", "content": patch_php})
print(f"  {r1}")

time.sleep(1)
print("\n=== Patching SEO router ===")
req = urllib.request.Request(f"https://{ip}/index.php?route=api/patch_seo", headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        body = r.read().decode('utf-8', errors='replace')
        print(f"  HTTP {r.status}")
        try:
            data = json.loads(body)
            for line in data.get('results', []):
                print(f"  {line}")
        except:
            print(f"  Raw: {body[:2000]}")
except Exception as e:
    print(f"  Error: {e}")
    if hasattr(e, 'read'):
        print(f"  Body: {e.read().decode('utf-8','replace')[:500]}")

# Clear cache
print("\n=== Clear cache ===")
r2 = post("site/clearCache", {})
print(f"  {r2}")

# Test
time.sleep(3)

print("\n=== Test /blog (listing) ===")
req2 = urllib.request.Request(f"https://{ip}/blog", headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req2, timeout=15, context=ctx) as r:
        body2 = r.read().decode('utf-8', errors='replace')
        print(f"  HTTP {r.status}, {len(body2)} bytes")
        if 'штукатурк' in body2.lower():
            print("  ✓ Blog listing works!")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Test /blog/kak-vybrat-shtukaturku (article via SEO) ===")
req3 = urllib.request.Request(f"https://{ip}/blog/kak-vybrat-shtukaturku", headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req3, timeout=15, context=ctx) as r:
        body3 = r.read().decode('utf-8', errors='replace')
        print(f"  HTTP {r.status}, {len(body3)} bytes")
        if 'Виды штукатурки' in body3:
            print("  ✓ Article via SEO URL works!")
        import re
        title = re.search(r'<title>(.*?)</title>', body3)
        if title:
            print(f"  Title: {title.group(1)[:80]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Test /index.php?route=blog/blog&article_id=1 (direct route) ===")
req4 = urllib.request.Request(f"https://{ip}/index.php?route=blog/blog&article_id=1", headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req4, timeout=15, context=ctx) as r:
        body4 = r.read().decode('utf-8', errors='replace')
        print(f"  HTTP {r.status}, {len(body4)} bytes")
        if 'Виды штукатурки' in body4:
            print("  ✓ Article via direct route works!")
except Exception as e:
    print(f"  Error: {e}")

print("\nDONE")
