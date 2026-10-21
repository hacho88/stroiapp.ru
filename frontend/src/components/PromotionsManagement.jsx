import React from "react";
import { Tag, RefreshCw, Plus, Trash2, Package } from "lucide-react";
import { apiGet, apiPost } from "../lib/api";

const money = (n) => new Intl.NumberFormat("ru-RU").format(Math.round(Number(n) || 0)) + " ₽";

const P_STATUS = {
  active: "bg-emerald-500/15 text-emerald-400",
  paused: "bg-amber-500/15 text-amber-400",
  disabled: "bg-stone-700/40 text-stone-400",
};

const TYPE_LABEL = { bundle: "Связка", discount: "Скидка", sale: "Распродажа", kit: "Комплект" };

// Форма спецификации комплекта: "ключевые слова × кол-во" по строкам
const itemsToText = (items) =>
  (items || []).map((i) => `${(i.keys || [i.name]).filter(Boolean).join(", ")} × ${i.qty || 1}`).join("\n");

const textToItems = (text) =>
  String(text || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [keysRaw, qtyRaw] = line.split("×").map((s) => s.trim());
      const keys = (keysRaw || "").split(",").map((k) => k.trim().toLowerCase()).filter(Boolean);
      return { keys, qty: Math.max(1, parseInt(qtyRaw || "1", 10) || 1) };
    })
    .filter((i) => i.keys.length > 0);

export default function PromotionsManagement() {
  const [promos, setPromos] = React.useState([]);
  const [kits, setKits] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [ok, setOk] = React.useState("");

  // создание акции
  const [pName, setPName] = React.useState("");
  const [pType, setPType] = React.useState("bundle");
  const [pDisc, setPDisc] = React.useState("");

  // создание комплекта
  const [kTitle, setKTitle] = React.useState("");
  const [kNote, setKNote] = React.useState("");
  const [kItems, setKItems] = React.useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [p, k] = await Promise.all([
        apiGet("/promotions/list"),
        apiGet("/promotions/kits/list"),
      ]);
      setPromos(p.promotions || []);
      setKits(k.kits || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => { load(); }, []);

  function flash(msg) {
    setOk(msg);
    setTimeout(() => setOk(""), 3000);
  }

  async function createPromo(e) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/promotions/create", {
        name: pName, type: pType, discount_pct: Number(pDisc) || 0,
      });
      setPName(""); setPDisc("");
      flash("Акция создана для moscow.stroiapp.ru");
      load();
    } catch (e2) {
      setError(e2.message);
    }
  }

  async function setPromoStatus(p, status) {
    try {
      await apiPost(`/promotions/update/${p.id}`, { status });
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function removePromo(p) {
    if (!window.confirm(`Удалить акцию «${p.name}»?`)) return;
    try {
      await apiPost(`/promotions/delete/${p.id}`, {});
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function createKit(e) {
    e.preventDefault();
    setError("");
    try {
      await apiPost("/promotions/kits/create", {
        title: kTitle, note: kNote, items: textToItems(kItems),
      });
      setKTitle(""); setKNote(""); setKItems("");
      flash("Комплект добавлен в карусель moscow.stroiapp.ru");
      load();
    } catch (e2) {
      setError(e2.message);
    }
  }

  async function setKitStatus(k, status) {
    try {
      await apiPost(`/promotions/kits/update/${k.id}`, { status });
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function removeKit(k) {
    if (!window.confirm(`Удалить комплект «${k.title}»?`)) return;
    try {
      await apiPost(`/promotions/kits/delete/${k.id}`, {});
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-stone-800 bg-stone-900 p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/15 p-2.5"><Tag size={22} className="text-emerald-400" /></div>
            <div>
              <h2 className="text-lg font-bold text-white">Акции — moscow.stroiapp.ru</h2>
              <p className="text-sm text-stone-400">
                Скидки, бандлы и комплекты карусели. Все записи создаются с <code className="text-emerald-400">site_owner=moscow</code>
              </p>
            </div>
          </div>
          <button onClick={load} disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-stone-950 hover:bg-emerald-400 disabled:opacity-50">
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            {loading ? "Загрузка..." : "Обновить"}
          </button>
        </div>

        {error && <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-300">{error}</div>}
        {ok && <div className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2.5 text-sm text-emerald-300">{ok}</div>}

        {/* Новая акция */}
        <form onSubmit={createPromo} className="mb-6 rounded-xl border border-stone-800 bg-stone-950/60 p-4">
          <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">Новая акция / скидка</div>
          <div className="flex flex-wrap gap-2">
            <input value={pName} onChange={(e) => setPName(e.target.value)} placeholder="Название акции" required
              className="min-w-[220px] flex-1 rounded-lg border border-stone-800 bg-stone-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500" />
            <select value={pType} onChange={(e) => setPType(e.target.value)}
              className="rounded-lg border border-stone-800 bg-stone-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500">
              {Object.keys(TYPE_LABEL).map((t) => <option key={t} value={t}>{TYPE_LABEL[t]}</option>)}
            </select>
            <input type="number" value={pDisc} onChange={(e) => setPDisc(e.target.value)} placeholder="Скидка %" min="0" max="100" step="0.5"
              className="w-28 rounded-lg border border-stone-800 bg-stone-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500" />
            <button type="submit" className="flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-stone-950 hover:bg-emerald-400">
              <Plus size={16} /> Создать
            </button>
          </div>
        </form>

        {/* Список акций */}
        <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-stone-500">Активные акции ({promos.length})</h3>
        {promos.length === 0 ? (
          <div className="mb-8 rounded-xl border border-dashed border-stone-800 px-4 py-8 text-center text-sm text-stone-500">
            Акций пока нет — создайте первую выше
          </div>
        ) : (
          <div className="mb-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {promos.map((p) => (
              <div key={p.id} className="rounded-xl border border-stone-800 bg-stone-950/60 p-4">
                <div className="mb-2 flex items-start justify-between gap-2">
                  <span className="font-semibold text-white">{p.name}</span>
                  <span className={`rounded-md px-2 py-0.5 text-xs font-semibold ${P_STATUS[p.status] || "bg-stone-800 text-stone-300"}`}>
                    {p.status}
                  </span>
                </div>
                <div className="mb-3 text-xs text-stone-400">
                  Тип: {TYPE_LABEL[p.type] || p.type}
                  {Number(p.discount_pct) > 0 && <> · скидка <b className="text-emerald-400">{p.discount_pct}%</b></>}
                  <div className="mt-1 text-stone-600">#{p.id} · {String(p.created_at || "").slice(0, 10)} · site: {p.site_owner}</div>
                </div>
                <div className="flex gap-2">
                  {p.status === "active" ? (
                    <button onClick={() => setPromoStatus(p, "paused")}
                      className="rounded-lg bg-amber-500/15 px-3 py-1.5 text-xs font-semibold text-amber-400 hover:bg-amber-500/25">
                      Пауза
                    </button>
                  ) : (
                    <button onClick={() => setPromoStatus(p, "active")}
                      className="rounded-lg bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/25">
                      Включить
                    </button>
                  )}
                  <button onClick={() => removePromo(p)}
                    className="flex items-center gap-1 rounded-lg bg-red-500/15 px-3 py-1.5 text-xs font-semibold text-red-400 hover:bg-red-500/25">
                    <Trash2 size={13} /> Удалить
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Комплекты карусели */}
        <div className="rounded-xl border border-stone-800 bg-stone-950/40 p-4">
          <div className="mb-3 flex items-center gap-2">
            <Package size={18} className="text-sky-400" />
            <h3 className="text-sm font-bold uppercase tracking-wider text-stone-400">
              Комплекты карусели /storefront/kits ({kits.length})
            </h3>
          </div>
          <p className="mb-4 text-xs text-stone-500">
            Позиции подбираются из живого каталога по ключевым словам: <code className="text-stone-300">штукатурк, ротбанд × 5</code> — каждая строка = одна позиция.
          </p>

          <form onSubmit={createKit} className="mb-5 rounded-xl border border-stone-800 bg-stone-950/60 p-4">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-stone-500">Новый комплект</div>
            <div className="grid gap-2">
              <div className="flex flex-wrap gap-2">
                <input value={kTitle} onChange={(e) => setKTitle(e.target.value)} placeholder="Название (напр. Штукатурка + грунтовка)" required
                  className="min-w-[220px] flex-1 rounded-lg border border-stone-800 bg-stone-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500" />
                <input value={kNote} onChange={(e) => setKNote(e.target.value)} placeholder="Подпись (~20 м²)"
                  className="min-w-[160px] rounded-lg border border-stone-800 bg-stone-950 px-3 py-2 text-sm text-white outline-none focus:border-emerald-500" />
              </div>
              <textarea value={kItems} onChange={(e) => setKItems(e.target.value)} rows={3} required
                placeholder={"штукатурк, ротбанд × 5\nгрунт × 1"}
                className="w-full rounded-lg border border-stone-800 bg-stone-950 px-3 py-2 font-mono text-xs text-white outline-none focus:border-emerald-500" />
              <div>
                <button type="submit" className="flex items-center gap-2 rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">
                  <Plus size={16} /> Добавить в карусель
                </button>
              </div>
            </div>
          </form>

          {kits.length === 0 ? (
            <div className="rounded-xl border border-dashed border-stone-800 px-4 py-6 text-center text-sm text-stone-500">
              Комплекты из БД не созданы — на сайте показываются базовые (_KIT_DEFS)
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {kits.map((k) => (
                <div key={k.id} className="rounded-xl border border-stone-800 bg-stone-950/60 p-4">
                  <div className="mb-1 flex items-start justify-between gap-2">
                    <span className="font-semibold text-white">{k.title}</span>
                    <span className={`rounded-md px-2 py-0.5 text-xs font-semibold ${P_STATUS[k.status] || "bg-stone-800 text-stone-300"}`}>
                      {k.status}
                    </span>
                  </div>
                  {k.note && <div className="mb-2 text-xs text-stone-500">{k.note}</div>}
                  <pre className="mb-3 whitespace-pre-wrap rounded-lg bg-stone-950 px-3 py-2 font-mono text-[11px] text-stone-400">
                    {itemsToText(k.items)}
                  </pre>
                  <div className="flex gap-2">
                    {k.status === "active" ? (
                      <button onClick={() => setKitStatus(k, "disabled")}
                        className="rounded-lg bg-amber-500/15 px-3 py-1.5 text-xs font-semibold text-amber-400 hover:bg-amber-500/25">
                        Скрыть
                      </button>
                    ) : (
                      <button onClick={() => setKitStatus(k, "active")}
                        className="rounded-lg bg-emerald-500/15 px-3 py-1.5 text-xs font-semibold text-emerald-400 hover:bg-emerald-500/25">
                          Показать
                        </button>
                    )}
                    <button onClick={() => removeKit(k)}
                      className="flex items-center gap-1 rounded-lg bg-red-500/15 px-3 py-1.5 text-xs font-semibold text-red-400 hover:bg-red-500/25">
                      <Trash2 size={13} /> Удалить
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
