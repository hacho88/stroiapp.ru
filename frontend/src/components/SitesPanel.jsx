import { useCallback, useEffect, useState } from "react";
import { ExternalLink, FileText, Globe, MapPin, Pencil, Plus, RefreshCw, ShoppingCart, Trash2, Wrench, X } from "lucide-react";
import { apiGet, apiPost } from "../lib/api";
import SiteContentEditor from "./SiteContentEditor";

const TYPE_META = {
  opencart: { label: "OpenCart", icon: ShoppingCart, cls: "text-sky-400" },
  admin: { label: "Админка", icon: Wrench, cls: "text-violet-400" },
  geo: { label: "Гео", icon: MapPin, cls: "text-emerald-400" },
};

const EMPTY_FORM = { slug: "", name: "", region: "", hours: 24, cost: 500 };

export default function SitesPanel({ addToast }) {
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ total: 0, online: 0 });
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null); // db_id being edited
  const [editSite, setEditSite] = useState(null); // site opened in content editor
  const [form, setForm] = useState(EMPTY_FORM);
  const notify = useCallback((m, t = "info") => addToast && addToast(m, t), [addToast]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await apiGet("/sites/list?check=true");
      if (d.status === "error") throw new Error(d.detail || "ошибка");
      setSites(d.sites || []);
      setStats({ total: d.total || 0, online: d.online || 0 });
    } catch (e) { notify("Ошибка: " + e.message, "error"); }
    finally { setLoading(false); }
  }, [notify]);

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const saveSite = async () => {
    if (!form.slug.trim() || !form.name.trim()) return notify("Укажи slug и название", "error");
    const payload = editing
      ? { id: editing, ...form }
      : form;
    const r = await apiPost(editing ? "/sites/update" : "/sites/add", payload).catch((e) => ({ error: e.message }));
    if (r.error || r.status === "error") return notify(r.error || r.detail, "error");
    notify(editing ? "Поддомен обновлён" : `Поддомен ${form.slug}.stroiapp.ru добавлен`, "success");
    setShowForm(false); setEditing(null); setForm(EMPTY_FORM);
    load();
  };

  const startEdit = (s) => {
    setEditing(s.db_id);
    setForm({ slug: s.slug, name: s.city, region: s.region || "", hours: s.hours ?? 24, cost: s.cost ?? 500 });
    setShowForm(true);
  };

  const removeSite = async (s) => {
    if (!window.confirm(`Удалить ${s.domain} из списка? (файлы на сервере не трогаем)`)) return;
    const r = await apiPost("/sites/delete", { id: s.db_id }).catch((e) => ({ error: e.message }));
    if (r.error || r.status === "error") return notify(r.error || r.detail, "error");
    notify(`${s.domain} удалён`, "success");
    load();
  };

  const toggleEnabled = async (s) => {
    const r = await apiPost("/sites/update", { id: s.db_id, enabled: !s.enabled }).catch((e) => ({ error: e.message }));
    if (r.error || r.status === "error") return notify(r.error || r.detail, "error");
    load();
  };

  const groups = [
    { key: "geo", title: "Гео-поддомены" },
  ];

  if (editSite) {
    return <SiteContentEditor site={editSite} onBack={() => setEditSite(null)} addToast={addToast} />;
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2"><Globe size={20} className="text-emerald-400" /> Сайты</h2>
            <p className="text-sm text-slate-400 mt-0.5">
              {stats.total} сайтов · <span className="text-emerald-400">{stats.online} онлайн</span>
              {stats.total > stats.online && <span className="text-red-400"> · {stats.total - stats.online} офлайн</span>}
            </p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => { setEditing(null); setForm(EMPTY_FORM); setShowForm(!showForm); }}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">
              <Plus size={15} /> Поддомен
            </button>
            <button onClick={load} disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700 disabled:opacity-50">
              <RefreshCw size={15} className={loading ? "animate-spin" : ""} /> Проверить
            </button>
          </div>
        </div>

        {showForm && (
          <div className="mt-4 rounded-xl border border-emerald-500/30 bg-slate-900/60 p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-sm font-bold">{editing ? "Редактировать поддомен" : "Новый гео-поддомен"}</div>
              <button onClick={() => { setShowForm(false); setEditing(null); }} className="text-slate-500 hover:text-slate-300"><X size={16} /></button>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <div>
                <label className="mb-1 block text-xs text-slate-400">Slug (поддомен)</label>
                <div className="flex items-center gap-1">
                  <input value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} placeholder="tula"
                    className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                  <span className="whitespace-nowrap text-xs text-slate-500">.stroiapp.ru</span>
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-400">Город</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Тула"
                  className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-400">Регион</label>
                <input value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} placeholder="Тульская область"
                  className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-400">Доставка, ч</label>
                <input type="number" value={form.hours} onChange={(e) => setForm({ ...form, hours: e.target.value })}
                  className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-slate-400">Доставка, ₽</label>
                <input type="number" value={form.cost} onChange={(e) => setForm({ ...form, cost: e.target.value })}
                  className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
              </div>
            </div>
            <div className="mt-3 flex gap-2">
              <button onClick={saveSite} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">
                {editing ? "Сохранить" : "Добавить"}
              </button>
              <button onClick={() => { setShowForm(false); setEditing(null); }} className="rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700">Отмена</button>
            </div>
          </div>
        )}
      </div>

      {groups.map((g) => {
        const list = sites.filter((s) => s.type === g.key);
        if (!list.length) return null;
        return (
          <div key={g.key} className="rounded-2xl border border-slate-700/30 glass p-4">
            <h3 className="mb-3 text-sm font-bold text-slate-300">{g.title} <span className="text-slate-500">({list.length})</span></h3>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {list.map((s) => {
                const meta = TYPE_META[s.type] || TYPE_META.geo;
                const Icon = meta.icon;
                return (
                  <div key={s.id} className={`flex items-center gap-3 rounded-xl border border-slate-700/40 bg-slate-900/60 p-3 ${s.enabled === false ? "opacity-50" : ""}`}>
                    <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${s.online ? "bg-emerald-400" : s.http_code === 0 ? "bg-slate-600" : "bg-red-400"}`}
                      title={s.online ? "онлайн" : "офлайн"} />
                    <Icon size={18} className={`shrink-0 ${meta.cls}`} />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium" title={s.name}>{s.city || s.name}</div>
                      <div className="truncate text-xs text-slate-500">{s.domain}</div>
                    </div>
                    <div className="shrink-0 text-right">
                      <div className={`text-xs font-bold ${s.online ? "text-emerald-400" : "text-red-400"}`}>
                        {s.http_code ? s.http_code : "—"}
                      </div>
                      {s.response_ms != null && s.online && <div className="text-[10px] text-slate-500">{s.response_ms} мс</div>}
                    </div>
                    <button onClick={() => setEditSite(s)} className="shrink-0 rounded-lg bg-slate-800 p-2 hover:bg-emerald-600 hover:text-slate-950" title="Редактировать контент">
                      <FileText size={14} />
                    </button>
                    <a href={s.url} target="_blank" rel="noreferrer" className="shrink-0 rounded-lg bg-slate-800 p-2 hover:bg-slate-700" title="Открыть">
                      <ExternalLink size={14} />
                    </a>
                    {s.type === "geo" && (
                      <>
                        <button onClick={() => startEdit(s)} className="shrink-0 rounded-lg bg-slate-800 p-2 hover:bg-slate-700" title="Редактировать">
                          <Pencil size={14} />
                        </button>
                        <button onClick={() => removeSite(s)} className="shrink-0 rounded-lg bg-red-950/60 p-2 text-red-400 hover:bg-red-900" title="Удалить из списка">
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {!loading && !sites.length && <div className="py-10 text-center text-sm text-slate-500">Нет данных</div>}
      {loading && !sites.length && <div className="py-10 text-center text-sm text-slate-500">Проверяю сайты...</div>}
    </div>
  );
}
