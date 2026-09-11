"""
Backup OpenCart site to ai.stroiapp.ru/backups/
- DB dump via api/ai_manager db/executeSql (key tables)
- Modification cache files via api/ai_manager file/listSafe + file/readSafe
- Key config files
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

def get(route, timeout=30):
    req = urllib.request.Request(f"https://{ip}/index.php?route={route}", headers={"Host": "stroiapp.ru"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return r.read().decode('utf-8', errors='replace')

# Backup dir
backup_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = os.path.join(os.path.dirname(__file__), "..", "backups", f"opencart_{backup_name}")
os.makedirs(backup_dir, exist_ok=True)
os.makedirs(os.path.join(backup_dir, "modification"), exist_ok=True)
os.makedirs(os.path.join(backup_dir, "config"), exist_ok=True)
os.makedirs(os.path.join(backup_dir, "controllers"), exist_ok=True)

print(f"=== Backup to {backup_dir} ===")

# 1. Backup DB tables (key tables as JSON)
tables = [
    "setting",
    "modification",
    "seo_url",
    "blog_article",
    "product",
    "product_description",
    "product_to_category",
    "category",
    "category_description",
    "layout",
    "layout_route",
    "layout_module",
    "store",
    "setting",
]

print("\n--- Backing up DB tables ---")
for table in tables:
    try:
        sql = f"SELECT * FROM `oc_open{table}` LIMIT 5000"
        r = post("db/executeSql", {"sql": sql})
        if isinstance(r, dict) and r.get("status") == "executed":
            rows = r.get("rows", [])
            with open(os.path.join(backup_dir, f"db_{table}.json"), "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            print(f"  ✓ {table}: {len(rows)} rows")
        else:
            print(f"  ✗ {table}: {r}")
    except Exception as e:
        print(f"  ✗ {table}: {e}")

# 2. Backup modification cache files
print("\n--- Backing up modification cache ---")
# Use a PHP controller to list and read all mod cache files
list_php = r"""<?php
class ControllerApiBackupModCache extends Controller {
    public function index() {
        $mod_dir = DIR_MODIFICATION;
        $files = array();
        foreach (array('catalog', 'admin', 'system') as $d) {
            $path = $mod_dir . $d;
            if (is_dir($path)) {
                $rii = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($path, FilesystemIterator::SKIP_DOTS));
                foreach ($rii as $f) {
                    if ($f->isFile()) {
                        $rel = str_replace($mod_dir, '', $f->getPathname());
                        $files[] = array(
                            'path' => $rel,
                            'content' => file_get_contents($f->getPathname()),
                            'size' => $f->getSize(),
                        );
                    }
                }
            }
        }
        echo json_encode(array('files' => $files, 'count' => count($files)));
        exit;
    }
}
"""

r = post("file/writeSafe", {"path": "catalog/controller/api/backup_mod_cache.php", "content": list_php})
time.sleep(1)
try:
    data = json.loads(get("api/backup_mod_cache"))
    mod_files = data.get("files", [])
    print(f"  Found {data.get('count', 0)} files in mod cache")
    for mf in mod_files:
        rel = mf["path"]
        dest = os.path.join(backup_dir, "modification", rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(mf["content"])
    print(f"  ✓ Saved {len(mod_files)} modification cache files")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 3. Backup config files
print("\n--- Backing up config files ---")
config_files = [
    ("config.php", "config/config.php"),
    ("admin/config.php", "config/admin_config.php"),
]
for remote_path, local_path in config_files:
    try:
        r = post("file/readSafe", {"path": remote_path})
        if isinstance(r, dict) and r.get("content"):
            with open(os.path.join(backup_dir, local_path), "w", encoding="utf-8") as f:
                f.write(r["content"])
            print(f"  ✓ {remote_path}")
        else:
            print(f"  ✗ {remote_path}: {r}")
    except Exception as e:
        print(f"  ✗ {remote_path}: {e}")

# 4. Backup key controllers
print("\n--- Backing up key controllers ---")
controllers = [
    "catalog/controller/common/header.php",
    "catalog/controller/common/footer.php",
    "catalog/controller/common/menu.php",
    "catalog/controller/startup/seo_url.php",
    "catalog/controller/startup/startup.php",
    "catalog/controller/event/theme.php",
    "catalog/controller/blog/blog.php",
    "catalog/controller/api/blog_publish.php",
    "catalog/controller/api/ai_manager.php",
    "catalog/controller/extension/module/uni_new_data.php",
    "catalog/view/theme/unishop2/template/common/header.twig",
]
for ctrl in controllers:
    try:
        r = post("file/readSafe", {"path": ctrl})
        if isinstance(r, dict) and r.get("content"):
            local = os.path.join(backup_dir, "controllers", ctrl.replace("/", os.sep))
            os.makedirs(os.path.dirname(local), exist_ok=True)
            with open(local, "w", encoding="utf-8") as f:
                f.write(r["content"])
            print(f"  ✓ {ctrl}")
        else:
            print(f"  ✗ {ctrl}: {r}")
    except Exception as e:
        print(f"  ✗ {ctrl}: {e}")

# 5. Summary
print(f"\n=== Backup complete: {backup_dir} ===")
total_files = sum(len(files) for _, _, files in os.walk(backup_dir))
total_size = sum(os.path.getsize(os.path.join(r, f)) for r, _, files in os.walk(backup_dir) for f in files)
print(f"  Total files: {total_files}")
print(f"  Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
