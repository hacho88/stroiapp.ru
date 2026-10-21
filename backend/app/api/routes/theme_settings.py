"""Менеджер мобильных тем витрины (10 премиальных систем).

Сайт moscow.stroiapp.ru собран как статический output:"export", поэтому
состояние темы живёт здесь, на бэке ai.stroiapp.ru.

- PUT/GET  /api/admin/theme-settings    — админка (защищён X-Auth-Token middleware).
- PUT/POST /api/admin/set-active-theme  — выбор активной темы из менеджера.
- GET      /api/storefront/theme        — публичное чтение для витрины
  (/storefront/* уже в белом списке auth_middleware, без токена).

active_theme: "default" | linear|stripe|vercel|airbnb|apple|github|supabase|
raycast|tailwind|cal. "default" — мгновенный откат на оригинальную тему.
Легаси-поля mobile_theme/isLinearThemeActive синхронизируются.

Персист — JSON-файл backend/data/theme_settings.json (атомарная запись
через .tmp + replace), переживает рестарты и перезаливы кода бэкенда.
"""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).resolve().parents[3] / "data" / "theme_settings.json"

# Два роутера: админский (под auth) и публичный для витрины.
admin_router = APIRouter(prefix="/admin", tags=["admin-theme-settings"])
public_router = APIRouter(prefix="/storefront", tags=["storefront-theme"])

KNOWN_THEMES = (
    "linear", "stripe", "vercel", "airbnb", "apple",
    "github", "supabase", "raycast", "tailwind", "cal", "pwa",
)

# Контракт по умолчанию — дефолтная тема, эксперимент выключен.
DEFAULTS = {
    "active_theme": "default",
    "mobile_theme": "default",
    "isLinearThemeActive": False,
}


def _sync(cfg: dict) -> dict:
    """Согласованность нового active_theme с легаси-полями."""
    theme = cfg.get("active_theme") or cfg.get("mobile_theme") or "default"
    if theme not in KNOWN_THEMES:
        theme = "default"
    cfg["active_theme"] = theme
    cfg["isLinearThemeActive"] = theme == "linear"
    cfg["mobile_theme"] = "linear" if cfg["isLinearThemeActive"] else theme
    return cfg


def _read() -> dict:
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cfg = dict(DEFAULTS)
        for k in DEFAULTS:
            if k in raw:
                cfg[k] = raw[k]
        return _sync(cfg)
    except Exception:
        return dict(DEFAULTS)


def _write(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONFIG_PATH)


class ThemeSettingsPayload(BaseModel):
    # булев флаг из старого тогла; допускаем и прямые строки темы
    isLinearThemeActive: bool | None = None
    mobile_theme: str | None = None
    active_theme: str | None = None


class SetActiveThemePayload(BaseModel):
    theme: str


def _payload_to_cfg(p: ThemeSettingsPayload) -> dict:
    cur = _read()
    if p.active_theme is not None:
        cur["active_theme"] = p.active_theme
    if p.mobile_theme is not None:
        cur["active_theme"] = p.mobile_theme
    if p.isLinearThemeActive is not None:
        cur["active_theme"] = "linear" if p.isLinearThemeActive else "default"
    return _sync(cur)


# ---------- Публичное чтение для витрины ----------

@public_router.get("/theme")
def public_theme():
    cfg = _read()
    return {
        "status": "ok",
        "active_theme": cfg["active_theme"],
        "mobile_theme": cfg["mobile_theme"],
    }


# ---------- Админское управление ----------

@admin_router.get("/theme-settings")
def admin_get():
    cfg = _read()
    return {"status": "ok", "themes": list(KNOWN_THEMES), **cfg}


@admin_router.put("/theme-settings")
@admin_router.post("/theme-settings")
def admin_set(payload: ThemeSettingsPayload):
    cfg = _payload_to_cfg(payload)
    _write(cfg)
    return {"status": "ok", **cfg}


@admin_router.put("/set-active-theme")
@admin_router.post("/set-active-theme")
def admin_set_active(payload: SetActiveThemePayload):
    theme = (payload.theme or "").strip().lower()
    if theme != "default" and theme not in KNOWN_THEMES:
        raise HTTPException(status_code=422, detail=f"unknown theme: {theme!r}")
    cfg = _read()
    cfg["active_theme"] = theme
    cfg = _sync(cfg)
    _write(cfg)
    return {"status": "ok", **cfg}
