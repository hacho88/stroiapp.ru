"""
Live Sync API — управление синхронизацией файлов с production-хостингом.
Endpoints:
  POST /api/sync/full        — полная синхронизация (returns streaming logs)
  POST /api/sync/watch/start — запуск watch-режима
  POST /api/sync/watch/stop  — остановка watch-режима
  GET  /api/sync/status      — статус watch-процесса
"""

import asyncio
import os
import signal
import sys
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/sync", tags=["sync"])

# Путь к live_sync.py
SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"
LIVE_SYNC_PY = SCRIPT_DIR / "live_sync.py"
PYTHON_EXE = sys.executable

# Храним PID watch-процесса
_watch_proc: asyncio.subprocess.Process | None = None


def _sync_env():
    env = os.environ.copy()
    # Убедимся что .env бэкенда доступен live_sync.py
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent.parent)
    return env


@router.post("/full")
async def sync_full():
    """Полная синхронизация всех файлов. Возвращает SSE-поток логов."""

    async def stream_logs():
        proc = await asyncio.create_subprocess_exec(
            PYTHON_EXE, str(LIVE_SYNC_PY), "--full",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=_sync_env(),
        )
        if proc.stdout:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip()
                yield f"data: {text}\n\n"
            await proc.wait()
            yield f"data: [DONE] exit_code={proc.returncode}\n\n"
        else:
            yield "data: [ERROR] no stdout\n\n"

    return StreamingResponse(stream_logs(), media_type="text/event-stream")


@router.post("/watch/start")
async def sync_watch_start():
    """Запуск watch-режима (фоновый процесс)."""
    global _watch_proc

    if _watch_proc is not None and _watch_proc.returncode is None:
        return {"status": "already_running", "pid": _watch_proc.pid}

    _watch_proc = await asyncio.create_subprocess_exec(
        PYTHON_EXE, str(LIVE_SYNC_PY), "--watch",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=_sync_env(),
    )
    return {"status": "started", "pid": _watch_proc.pid}


@router.post("/watch/stop")
async def sync_watch_stop():
    """Остановка watch-режима."""
    global _watch_proc

    if _watch_proc is None:
        return {"status": "not_running"}

    try:
        _watch_proc.send_signal(signal.SIGTERM)
        await asyncio.wait_for(_watch_proc.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        _watch_proc.kill()
        await _watch_proc.wait()
    except Exception:
        pass

    pid = _watch_proc.pid
    _watch_proc = None
    return {"status": "stopped", "pid": pid}


@router.get("/status")
async def sync_status():
    """Статус watch-процесса."""
    global _watch_proc

    if _watch_proc is None:
        return {"running": False, "pid": None}

    returncode = _watch_proc.returncode
    if returncode is None:
        return {"running": True, "pid": _watch_proc.pid}
    else:
        _watch_proc = None
        return {"running": False, "pid": None, "last_exit_code": returncode}
