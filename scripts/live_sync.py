"""
Live Sync — мгновенная синхронизация файлов с production-хостингом stroiapp.ru

Что делает:
1. Отслеживает изменения в stroiapp.ru/public_html
2. При изменении файла (.php, .twig, .css, .js, .xml, .json) → отправляет через API ai_manager.php
3. Автоматически очищает кэш OpenCart после загрузки файлов
4. Debounce: группирует изменения за 2 секунды

Запуск:
    python scripts/live_sync.py
    Или двойным кликом по sync.bat
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from threading import Timer
from dotenv import load_dotenv

# Настройка путей
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR / "backend"))

# Загружаем .env
env_path = PROJECT_DIR / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Конфигурация
OPENCART_URL = os.getenv("OPENCART_SYNC_URL", "https://stroiapp.ru")
OPENCART_TOKEN = os.getenv("OPENCART_SYNC_TOKEN", os.getenv("OPENCART_API_TOKEN", "change_this_ai_manager_token"))
WATCH_DIR = (PROJECT_DIR.parent / "stroiapp.ru" / "public_html").resolve()

ALLOWED_EXTENSIONS = {'.php', '.twig', '.css', '.js', '.xml', '.json', '.txt', '.html', '.htm'}
ALLOWED_PREFIXES = ('catalog/', 'image/catalog/', 'admin/controller/', 'admin/model/', 'admin/view/', 'admin/language/')
BLOCKED_PATHS = ('system/', 'vendor/', 'storage/cache/', 'storage/session/', 'storage/logs/', 'image/cache/', 'node_modules', '.git', 'ai_backups/')

DEBOUNCE_SECONDS = 2.0

print(f"=== AI StroiApp Live Sync ===")
print(f"Watching : {WATCH_DIR}")
print(f"Target   : {OPENCART_URL}")
print(f"Token    : {'*' * len(OPENCART_TOKEN)}")
print("")

# --- Debounced batch uploader ---
_pending_paths = set()
_flush_timer = None


def _flush_uploads():
    global _pending_paths, _flush_timer
    _flush_timer = None
    if not _pending_paths:
        return

    batch = list(_pending_paths)
    _pending_paths.clear()

    print(f"\n[FLUSH] Uploading {len(batch)} file(s)...")
    for rel_path in batch:
        upload_file(rel_path)

    if batch:
        clear_cache()
        print(f"[OK] {len(batch)} file(s) synced + cache cleared\n")


def schedule_upload(rel_path: str):
    global _pending_paths, _flush_timer
    _pending_paths.add(rel_path)
    if _flush_timer:
        _flush_timer.cancel()
    _flush_timer = Timer(DEBOUNCE_SECONDS, _flush_uploads)
    _flush_timer.daemon = True
    _flush_timer.start()
    print(f"  queued: {rel_path}")


# --- API helpers ---

def upload_file(rel_path: str) -> bool:
    """Upload a single file via ai_manager.php file/writeSafe"""
    abs_path = WATCH_DIR / rel_path
    if not abs_path.exists() or not abs_path.is_file():
        print(f"  skip (not found): {rel_path}")
        return False

    # Проверяем whitelist
    rel_unix = rel_path.replace('\\', '/')
    if not any(rel_unix.startswith(p) for p in ALLOWED_PREFIXES):
        print(f"  skip (not allowed prefix): {rel_path}")
        return False

    if any(bp in rel_unix for bp in BLOCKED_PATHS):
        print(f"  skip (blocked path): {rel_path}")
        return False

    ext = abs_path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        print(f"  skip (bad ext): {rel_path}")
        return False

    try:
        raw = abs_path.read_bytes()
        # Remove UTF-8 BOM if present
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        content = raw.decode('utf-8')
    except Exception as e:
        print(f"  ERROR reading {rel_path}: {e}")
        return False

    url = f"{OPENCART_URL}/index.php?route=api/ai_manager&action=file/writeSafe&token={OPENCART_TOKEN}"
    payload = {"path": rel_unix, "content": content}

    try:
        resp = requests.post(url, json=payload, timeout=30)
        raw = resp.content
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        data = json.loads(raw.decode('utf-8'))
        if data.get("status") == "written":
            print(f"  uploaded: {rel_path}")
            return True
        else:
            print(f"  API error ({rel_path}): {data}")
            return False
    except Exception as e:
        print(f"  NETWORK error ({rel_path}): {e}")
        return False


def clear_cache():
    """Clear OpenCart cache via ai_manager.php site/clearCache"""
    url = f"{OPENCART_URL}/index.php?route=api/ai_manager&action=site/clearCache&token={OPENCART_TOKEN}"
    try:
        resp = requests.post(url, timeout=30)
        raw = resp.content
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        data = json.loads(raw.decode('utf-8'))
        print(f"  cache cleared: {data.get('deleted', 0)} files")
    except Exception as e:
        print(f"  cache clear error: {e}")


def full_sync():
    """One-shot sync all allowed files"""
    print("\n=== FULL SYNC ===")
    count = 0
    for root, dirs, files in os.walk(WATCH_DIR):
        # Исключаем блокированные папки
        dirs[:] = [d for d in dirs if not any(bp in d for bp in ('node_modules', '.git', 'cache', 'session', 'logs', 'ai_backups'))]

        for fname in files:
            fpath = Path(root) / fname
            rel = str(fpath.relative_to(WATCH_DIR)).replace('\\', '/')

            if not any(rel.startswith(p) for p in ALLOWED_PREFIXES):
                continue
            if any(bp in rel for bp in BLOCKED_PATHS):
                continue
            if fpath.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue

            if upload_file(rel):
                count += 1

    if count:
        clear_cache()
        print(f"[OK] Full sync complete: {count} files\n")
    else:
        print("[OK] Nothing to sync\n")


# --- Watchdog handlers ---

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("\n[WARN] watchdog not installed. Install via:")
    print("  pip install -r scripts/requirements.txt")
    print("\nRunning ONE-SHOT sync instead...")
    full_sync()
    sys.exit(0)


class SyncHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        rel = str(Path(event.src_path).relative_to(WATCH_DIR)).replace('\\', '/')
        schedule_upload(rel)

    def on_created(self, event):
        if event.is_directory:
            return
        rel = str(Path(event.src_path).relative_to(WATCH_DIR)).replace('\\', '/')
        schedule_upload(rel)

    def on_moved(self, event):
        if event.is_directory:
            return
        rel = str(Path(event.dest_path).relative_to(WATCH_DIR)).replace('\\', '/')
        schedule_upload(rel)


# --- Main ---

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Live Sync for StroiApp")
    parser.add_argument("--full", action="store_true", help="One-shot full sync then exit")
    parser.add_argument("--watch", action="store_true", help="Watch mode (default)")
    args = parser.parse_args()

    if args.full:
        full_sync()
        sys.exit(0)

    observer = Observer()
    handler = SyncHandler()
    observer.schedule(handler, str(WATCH_DIR), recursive=True)
    observer.start()

    print("[WATCH MODE] Press Ctrl+C to stop\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down...")
        observer.stop()
    observer.join()
    print("[DONE] Live sync stopped.")
