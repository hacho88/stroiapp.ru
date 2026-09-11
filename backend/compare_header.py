import urllib.request, ssl, json, socket, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    ip = socket.gethostbyname("stroiapp.ru")
except:
    ip = "188.225.23.151"

h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=60):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# Compare original and modified header.php, and check event/theme.php
compare_php = r"""<?php
class ControllerApiCompareHeader extends Controller {
    public function index() {
        $result = array();
        $mod_dir = DIR_MODIFICATION;
        $root = dirname(DIR_APPLICATION);

        // 1. Compare header.php
        $orig_header = $root . '/catalog/controller/common/header.php';
        $mod_header = $mod_dir . 'catalog/controller/common/header.php';

        $orig_content = file_get_contents($orig_header);
        $mod_content = file_get_contents($mod_header);

        // Find differences
        $orig_lines = explode("\n", $orig_content);
        $mod_lines = explode("\n", $mod_content);

        $diffs = array();
        $max = max(count($orig_lines), count($mod_lines));
        for ($i = 0; $i < $max; $i++) {
            $o = isset($orig_lines[$i]) ? $orig_lines[$i] : '';
            $m = isset($mod_lines[$i]) ? $mod_lines[$i] : '';
            if ($o !== $m) {
                $diffs[] = array('line' => $i, 'orig' => $o, 'mod' => $m);
            }
        }
        $result['header_diffs'] = array_slice($diffs, 0, 20);

        // 2. Check event/theme.php — this is where unishop2 might add styles
        $mod_theme = $mod_dir . 'catalog/controller/event/theme.php';
        $orig_theme = $root . '/catalog/controller/event/theme.php';

        if (file_exists($mod_theme)) {
            $result['mod_theme_size'] = filesize($mod_theme);
            $result['mod_theme_content'] = file_get_contents($mod_theme);
        }
        if (file_exists($orig_theme)) {
            $result['orig_theme_size'] = filesize($orig_theme);
        }

        // 3. Check the unishop2 modification XML for header.php
        $mods = $this->db->query("SELECT xml FROM `" . DB_PREFIX . "modification` WHERE name LIKE '%UniShop2 template%' AND status = 1");
        if ($mods->num_rows) {
            $xml = simplexml_load_string($mods->row['xml']);
            $header_ops = array();
            foreach ($xml->file as $file) {
                $path = (string)$file['path'];
                $name = (string)$file['name'];
                if ($path == 'catalog/controller/common/header.php' || strpos($path, 'header.php') !== false) {
                    foreach ($file->operation as $op) {
                        $header_ops[] = array(
                            'position' => isset($op['position']) ? (string)$op['position'] : 'replace',
                            'search' => substr((string)$op->search, 0, 300),
                            'add' => substr((string)$op->add, 0, 500),
                        );
                    }
                }
            }
            $result['header_mod_ops'] = $header_ops;
        }

        // 4. Check for unishop2 settings in DB (config_unishop2)
        $settings = $this->db->query("SELECT * FROM `" . DB_PREFIX . "setting` WHERE `key` = 'config_unishop2' AND store_id = 0");
        $result['unishop2_settings'] = $settings->num_rows;
        if ($settings->num_rows) {
            $val = json_decode($settings->row['value'], true);
            if (is_array($val)) {
                // Check for stylesheet-related settings
                $style_keys = array();
                foreach ($val as $k => $v) {
                    if (strpos($k, 'style') !== false || strpos($k, 'css') !== false || strpos($k, 'sheet') !== false) {
                        $style_keys[$k] = $v;
                    }
                }
                $result['unishop2_style_settings'] = $style_keys;
                $result['unishop2_total_keys'] = count($val);
            }
        }

        echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
        exit;
    }
}
"""

print("=== Writing compare controller ===")
r1 = post("file/writeSafe", {"path": "catalog/controller/api/compare_header.php", "content": compare_php})
print(f"  {r1}")

time.sleep(1)
print("\n=== Comparing ===")
req = urllib.request.Request(f"https://{ip}/index.php?route=api/compare_header", headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        body = r.read().decode('utf-8', errors='replace')
        data = json.loads(body)

        print(f"\n--- HEADER.PHP DIFFS ---")
        for d in data.get('header_diffs', []):
            print(f"  Line {d['line']}:")
            print(f"    ORIG: {d['orig'][:200]}")
            print(f"    MOD:  {d['mod'][:200]}")

        print(f"\n--- HEADER MOD OPS ---")
        for op in data.get('header_mod_ops', []):
            print(f"  Position: {op['position']}")
            print(f"  Search: {op['search'][:200]}")
            print(f"  Add: {op['add'][:300]}")

        print(f"\n--- EVENT/THEME.PHP ---")
        print(f"  Orig size: {data.get('orig_theme_size', 'N/A')}")
        print(f"  Mod size: {data.get('mod_theme_size', 'N/A')}")
        if data.get('mod_theme_content'):
            print(f"  Content (first 2000):")
            print(data['mod_theme_content'][:2000])

        print(f"\n--- UNISHOP2 SETTINGS ---")
        print(f"  Settings found: {data.get('unishop2_settings')}")
        print(f"  Total keys: {data.get('unishop2_total_keys')}")
        print(f"  Style settings: {data.get('unishop2_style_settings')}")

except Exception as e:
    print(f"  Error: {e}")

print("\nDONE")
