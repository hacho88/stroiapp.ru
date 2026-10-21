import React, { useEffect, useState } from "react";
import { Smartphone, Loader2, CheckCircle2, AlertCircle, RotateCcw } from "lucide-react";
import { apiGet, apiPut } from "../lib/api";

// Менеджер мобильных тем — 10 премиальных систем для moscow.stroiapp.ru.
// Активная тема хранится на бэке (PUT /admin/set-active-theme →
// data/theme_settings.json), витрина читает публичный /storefront/theme и
// вешает .theme-any + .theme-<имя> на <html> только на мобильных ≤820px.
// "default" — мгновенный откат на оригинальный дизайн.

const THEMES = [
  {
    id: "linear", name: "Linear Cyber Dark", desc: "Тёмный графит, микро-бордеры",
    bg: "#0c0d0e", surface: "#121316", text: "#e8eaed",
    mode: "тёмная", font: "Inter", title: "12.5px / 600", pad: 14, radius: 10, meta: "sans 11px",
  },
  {
    id: "stripe", name: "Stripe Minimalist", desc: "Чистый B2B, высокий контраст",
    bg: "#f6f9fc", surface: "#ffffff", text: "#0a2540",
    mode: "светлая", font: "Geologica", title: "13.5px / 600", pad: 16, radius: 12, meta: "sans 11.5px",
  },
  {
    id: "vercel", name: "Vercel Mono", desc: "Строгий монохром, плавающий навбар",
    bg: "#000000", surface: "#0a0a0a", text: "#ededed",
    mode: "тёмная", font: "system-ui", title: "12.5px / 600", pad: 12, radius: 4, meta: "sans 11px",
  },
  {
    id: "airbnb", name: "Airbnb Soft", desc: "Мягкие карточки, крупные радиусы",
    bg: "#f7f7f7", surface: "#ffffff", text: "#222222",
    mode: "светлая", font: "Geologica round", title: "14px / 650", pad: 16, radius: 20, meta: "sans 12px",
  },
  {
    id: "apple", name: "Apple Executive", desc: "Нейтральный люкс, премиум-типографика",
    bg: "#f5f5f7", surface: "#ffffff", text: "#1d1d1f",
    mode: "светлая", font: "SF/Helvetica", title: "14px / 600", pad: 18, radius: 18, meta: "sans 12px",
  },
  {
    id: "github", name: "GitHub Structured", desc: "Разработческая табличная плотность",
    bg: "#0d1117", surface: "#161b22", text: "#e6edf3",
    mode: "тёмная", font: "Segoe/Noto", title: "12.5px / 600", pad: 12, radius: 6, meta: "mono 11px",
  },
  {
    id: "supabase", name: "Supabase Emerald", desc: "Тёмный изумрудный tech-стиль",
    bg: "#101214", surface: "#1b1e21", text: "#ededed",
    mode: "тёмная", font: "Geologica", title: "13px / 500", pad: 14, radius: 8, meta: "sans 11.5px",
  },
  {
    id: "raycast", name: "Raycast Dense", desc: "Сверхплотные utility-списки",
    bg: "#0f1011", surface: "#1b1d1f", text: "#f2f2f2",
    mode: "тёмная", font: "system-ui", title: "12px / 600", pad: 10, radius: 10, meta: "mono 10.5px",
  },
  {
    id: "tailwind", name: "Tailwind Cyber", desc: "Светлый cyber-cyan, плавные радиусы",
    bg: "#f8fafc", surface: "#ffffff", text: "#0f172a",
    mode: "светлая", font: "system-ui", title: "13px / 600", pad: 14, radius: 14, meta: "sans 11.5px",
  },
  {
    id: "cal", name: "Cal Ultra-Minimal", desc: "Монохром, максимум воздуха",
    bg: "#fafafa", surface: "#ffffff", text: "#111111",
    mode: "светлая", font: "Geologica", title: "13px / 500", pad: 16, radius: 8, meta: "sans 11.5px",
  },
  {
    id: "pwa", name: "PWA Native", desc: "Нативный app-look: iOS-группа, system-шрифт",
    bg: "#f2f2f7", surface: "#ffffff", text: "#1c1c1e",
    mode: "светлая", font: "system-ui (SF/Roboto)", title: "12.5px / 600", pad: 14, radius: 12, meta: "sans 11px",
  },
];

const BRAND = "#a6192e"; // фирменный бордовый StroiApp — CTA в любой теме

function PaletteDots({ t }) {
  return (
    <span className="inline-flex items-center gap-1.5" title={`bg ${t.bg} · surface ${t.surface} · text ${t.text} · CTA ${BRAND}`}>
      {[t.bg, t.surface, t.text, BRAND].map((c) => (
        <span key={c} className="h-4 w-4 rounded-full border border-slate-600/60" style={{ background: c }} />
      ))}
    </span>
  );
}

export default function ThemeManager() {
  const [active, setActive] = useState("default");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(""); // id темы, которую сейчас сохраняем
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet("/admin/theme-settings")
      .then((r) => setActive(r.active_theme || "default"))
      .catch((e) => setError(e.message || "Не удалось прочитать настройку"))
      .finally(() => setLoading(false));
  }, []);

  const activate = async (id) => {
    if (saving) return;
    const prev = active;
    setActive(id); // оптимистично — при ошибке откатим
    setSaving(id);
    setError("");
    try {
      const r = await apiPut("/admin/set-active-theme", { theme: id });
      setActive(r.active_theme || "default");
    } catch (e) {
      setActive(prev); // сервер не принял — возвращаем исходное состояние
      setError(e.message || "Не удалось сохранить");
    } finally {
      setSaving("");
    }
  };

  const isDefault = active === "default";

  return (
    <div className="rounded-2xl border border-slate-700/30 glass p-6 lg:col-span-2">
      <div className="mb-1 flex items-center gap-2 text-emerald-400">
        <Smartphone size={20} />
        <h3 className="font-bold">Менеджер мобильных тем (10 Премиум Систем)</h3>
      </div>
      <p className="mb-4 text-sm text-slate-400">
        Премиальные темы для moscow.stroiapp.ru. Применяются только на мобильных
        экранах (≤820px) — десктопная версия не меняется. CTA-кнопки во всех темах
        сохраняют фирменный бордовый цвет.
      </p>

      {error && (
        <div className="mb-4 inline-flex items-center gap-1.5 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-400">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Откат на стандартную тему */}
      <div className={`mb-4 flex items-center justify-between gap-4 rounded-xl border px-4 py-3 ${
        isDefault ? "border-emerald-500/40 bg-emerald-500/10" : "border-slate-700/40 bg-slate-950/60"
      }`}>
        <div className="min-w-0">
          <div className="text-sm font-semibold text-slate-100">Стандартная тема StroiApp</div>
          <div className="mt-0.5 text-[11px] text-slate-500">
            {loading ? "загрузка…" : isDefault
              ? <span className="inline-flex items-center gap-1 text-emerald-400"><CheckCircle2 size={12} /> Сейчас активна</span>
              : "Оригинальный дизайн — без премиум-оверлея"}
          </div>
        </div>
        {!isDefault && (
          <button
            type="button"
            disabled={loading || !!saving}
            onClick={() => activate("default")}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-slate-700 px-3 py-2 text-xs font-bold text-slate-100 hover:bg-slate-600 disabled:opacity-60"
          >
            {saving === "default" ? <Loader2 size={13} className="animate-spin" /> : <RotateCcw size={13} />}
            Вернуть стандарт
          </button>
        )}
      </div>

      {/* Грид 10 тем */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {THEMES.map((t) => {
          const on = active === t.id;
          const busy = saving === t.id;
          return (
            <div
              key={t.id}
              className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-3 transition-colors ${
                on ? "border-emerald-500/50 bg-emerald-500/10" : "border-slate-700/40 bg-slate-950/60 hover:border-slate-600/60"
              }`}
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                  <span className="truncate">{t.name}</span>
                  {on && <CheckCircle2 size={14} className="shrink-0 text-emerald-400" />}
                </div>
                <div className="mt-0.5 text-[11px] text-slate-500">{t.desc}</div>
                <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-slate-500">
                  <span className={t.mode === "тёмная" ? "text-slate-400" : "text-amber-300/80"}>{t.mode}</span>
                  <span>{t.font}</span>
                  <span>title {t.title}</span>
                  <span>pad {t.pad}px</span>
                  <span>R{t.radius}</span>
                  <span>{t.meta}</span>
                </div>
                <div className="mt-2"><PaletteDots t={t} /></div>
              </div>
              <button
                type="button"
                disabled={loading || !!saving}
                onClick={() => activate(on ? "default" : t.id)}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-bold transition-colors disabled:opacity-60 ${
                  on
                    ? "bg-emerald-500 text-slate-950 hover:bg-emerald-400"
                    : "bg-slate-700 text-slate-100 hover:bg-slate-600"
                }`}
              >
                {busy ? <Loader2 size={13} className="animate-spin" /> : on ? "Активна" : "Активировать"}
              </button>
            </div>
          );
        })}
      </div>

      {!isDefault && (
        <p className="mt-4 text-[11px] leading-snug text-slate-500">
          Мгновенный откат: активируйте «Стандартная тема StroiApp» — витрина вернётся
          к оригинальному дизайну при следующей загрузке страницы (пересборка не нужна).
        </p>
      )}
    </div>
  );
}
