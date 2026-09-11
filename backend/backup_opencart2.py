"""
Backup OpenCart: DB tables + config + key files via single PHP controller
"""
import urllib.request, ssl, json, socket, time, os, datetime

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    ip = socket.gethostbyname("stroiapp.ru")
except:
    ip = "188.225.23.151"

h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=120):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

def get(route, timeout=60):
    req = urllib.request.Request(f"https://{ip}/index.php?route={route}", headers={"Host": "stroiapp.ru"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read().decode('utf-8', errors='replace')

backup_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = os.path.join(os.path.dirname(__file__), "..", "backups", f"opencart_{backup_name}")
os.makedirs(backup_dir, exist_ok=True)
os.makedirs(os.path.join(backup_dir, "db"), exist_ok=True)
os.makedirs(os.path.join(backup_dir, "files"), exist_ok=True)

print(f"=== Backup to {backup_dir} ===")

# Single PHP controller that dumps everything
backup_php = r"""<?php
class ControllerApiFullBackup extends Controller {
    public function index() {
        $result = array();
        $root = dirname(DIR_APPLICATION);

        // 1. DB tables
        $tables = array('setting', 'modification', 'seo_url', 'blog_article', 'store', 'layout', 'layout_route', 'layout_module');
        $result['db'] = array();
        foreach ($tables as $t) {
            $q = $this->db->query("SELECT * FROM `" . DB_PREFIX . $t . "`");
            $result['db'][$t] = $q->rows;
        }

        // 2. Config files
        $result['config'] = array();
        $cfg1 = $root . '/config.php';
        if (file_exists($cfg1)) $result['config']['config.php'] = file_get_contents($cfg1);
        $cfg2 = $root . '/admin/config.php';
        if (file_exists($cfg2)) $result['config']['admin_config.php'] = file_get_contents($cfg2);

        // 3. Key controllers and templates
        $key_files = array(
            'catalog/controller/common/header.php',
            'catalog/controller/common/footer.php',
            'catalog/controller/common/menu.php',
            'catalog/controller/startup/seo_url.php',
            'catalog/controller/startup/startup.php',
            'catalog/controller/event/theme.php',
            'catalog/controller/blog/blog.php',
            'catalog/controller/api/blog_publish.php',
            'catalog/controller/api/ai_manager.php',
            'catalog/controller/extension/module/uni_new_data.php',
            'catalog/view/theme/unishop2/template/common/header.twig',
            'catalog/view/theme/unishop2/template/common/footer.twig',
        );
        $result['files'] = array();
        foreach ($key_files as $f) {
            $full = $root . '/' . $f;
            if (file_exists($full)) {
                $result['files'][$f] = file_get_contents($full);
            }
        }

        // 4. Modification cache file list
        $mod_dir = DIR_MODIFICATION;
        $result['mod_cache_files'] = array();
        foreach (array('catalog', 'admin', 'system') as $d) {
            $path = $mod_dir . $d;
            if (is_dir($path)) {
                $rii = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($path, FilesystemIterator::SKIP_DOTS));
                foreach ($rii as $f) {
                    if ($f->isFile()) {
                        $rel = str_replace($mod_dir, '', $f->getPathname());
                        $result['mod_cache_files'][$rel] = file_get_contents($f->getPathname());
                    }
                }
            }
        }

        echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        exit;
    }
}
"""

print("Writing backup controller...")
r = post("file/writeSafe", {"path": "catalog/controller/api/full_backup.php", "content": backup_php})
print(f"  {r}")

time.sleep(1)
print("Running backup (this may take a moment)...")
try:
    raw = get("api/full_backup", timeout=120)
    data = json.loads(raw)

    # Save DB
    db_data = data.get("db", {})
    for table, rows in db_data.items():
        with open(os.path.join(backup_dir, "db", f"{table}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"  ✓ DB {table}: {len(rows)} rows")

    # Save config
    cfg = data.get("config", {})
    for name, content in cfg.items():
        with open(os.path.join(backup_dir, "files", name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ config: {name}")

    # Save key files
    files = data.get("files", {})
    for path, content in files.items():
        local = os.path.join(backup_dir, "files", path.replace("/", os.sep))
        os.makedirs(os.path.dirname(local), exist_ok=True)
        with open(local, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ {path}")

    # Save mod cache
    mod_files = data.get("mod_cache_files", {})
    mod_dir_local = os.path.join(backup_dir, "modification")
    os.makedirs(mod_dir_local, exist_ok=True)
    for rel, content in mod_files.items():
        local = os.path.join(mod_dir_local, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(local), exist_ok=True)
        with open(local, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"  ✓ modification cache: {len(mod_files)} files")

except Exception as e:
    print(f"  Error: {e}")
    # Save raw response for debugging
    with open(os.path.join(backup_dir, "raw_response.txt"), "w", encoding="utf-8") as f:
        f.write(raw[:5000] if 'raw' in dir() else str(e))

# Summary
total_files = sum(len(files) for _, _, files in os.walk(backup_dir))
total_size = sum(os.path.getsize(os.path.join(r, f)) for r, _, files in os.walk(backup_dir) for f in files)
print(f"\n=== Backup complete: {backup_dir} ===")
print(f"  Files: {total_files}, Size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
