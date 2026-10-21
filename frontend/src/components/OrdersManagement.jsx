import React from "react";
import { createPortal } from "react-dom";
import {
  ShoppingBag, RefreshCw, ChevronDown, ChevronRight, Phone, MapPin, Building2,
  Volume2, VolumeX, FileText, FileSpreadsheet, Loader2, CreditCard, User, Printer,
} from "lucide-react";
import { apiGet, apiPost, apiUrl, getToken } from "../lib/api";

const money = (n) => new Intl.NumberFormat("ru-RU").format(Math.round(Number(n) || 0)) + " ₽";

// Вес из названия позиции: "Пескобетон 40кг" -> 40, "…500 г" -> 0.5
const W_RE = /(\d+(?:[.,]\d+)?)\s*(кг|kg|г\b|g\b)/i;
function weightFromName(name) {
  const m = W_RE.exec(name || "");
  if (!m) return 0;
  const v = parseFloat(m[1].replace(",", "."));
  return /^(г|g)$/i.test(m[2]) ? v / 1000 : v;
}

const SRC_BADGE = {
  "stroiapp.ru": "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  "moscow.stroiapp.ru": "bg-sky-500/15 text-sky-400 border-sky-500/30",
};

const STATUS_STYLE = {
  new: "bg-amber-500/15 text-amber-400",
  in_progress: "bg-sky-500/15 text-sky-400",
  done: "bg-emerald-500/15 text-emerald-400",
  canceled: "bg-red-500/15 text-red-400",
};

const STATUS_LABEL = { new: "Новый", in_progress: "В работе", done: "Выполнен", canceled: "Отменён" };

const SRC_FILTERS = [
  { id: "all", label: "Все источники" },
  { id: "stroiapp.ru", label: "stroiapp.ru" },
  { id: "moscow.stroiapp.ru", label: "moscow.stroiapp.ru" },
];

const PAY_FILTERS = [
  { id: "all", label: "Все оплаты" },
  { id: "cash", label: "Наличные" },
  { id: "invoice", label: "Безналичный счёт" },
];

const POLL_MS = 30000;          // авто-опрос новых заказов
const NEW_STATUSES = new Set(["new", "Ожидание"]); // «необработанные» статусы обеих витрин

// CSV для Excel: BOM + «;» — корректно открывается в русской локали
function exportCsv(o, items) {
  const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const rows = [["№", "Артикул", "Наименование", "Кол-во", "Цена", "Сумма"]];
  items.forEach((it, i) => {
    const q = Number(it.qty || it.quantity || 1);
    const p = Number(it.price || 0);
    rows.push([i + 1, it.sku || "", it.name || it.product || it.model || "", q, p, p * q]);
  });
  rows.push([]);
  rows.push(["", "", "", "", "ИТОГО", Number(o.total) || 0]);
  const csv = "\uFEFF" + rows.map((r) => r.map(esc).join(";")).join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `order-${o.order_id}-smeta.csv`;
  a.click();
  URL.revokeObjectURL(a.href);
}

export default function OrdersManagement() {
  const [orders, setOrders] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [src, setSrc] = React.useState("all");
  const [pay, setPay] = React.useState("all");
  const [open, setOpen] = React.useState({});
  const [itemsCache, setItemsCache] = React.useState({}); // oc order_id -> items[]
  const [itemsLoading, setItemsLoading] = React.useState({});
  const [soundOn, setSoundOn] = React.useState(true);
  const [soundBlocked, setSoundBlocked] = React.useState(false);
  const [pdfBusy, setPdfBusy] = React.useState({});
  const [printData, setPrintData] = React.useState(null); // {o, items} — данные для накладной

  function printOrder(o, items) {
    setPrintData({ o, items });
    // печать после отрисовки портала; очистка — по afterprint
    setTimeout(() => window.print(), 60);
  }

  React.useEffect(() => {
    const clear = () => setPrintData(null);
    window.addEventListener("afterprint", clear);
    return () => window.removeEventListener("afterprint", clear);
  }, []);
  const [freshIds, setFreshIds] = React.useState(new Set()); // подсветка «только что пришедших»
  const seenIds = React.useRef(null);   // null = первая загрузка, звука нет
  const audioRef = React.useRef(null);

  function playDing() {
    try {
      if (!audioRef.current) audioRef.current = new Audio("/sounds/new-order.mp3");
      audioRef.current.currentTime = 0;
      const p = audioRef.current.play();
      if (p && p.catch) p.catch(() => setSoundBlocked(true));
    } catch { setSoundBlocked(true); }
  }

  // Анлок автоплея: первый клик/тап по странице «прогревает» Audio
  React.useEffect(() => {
    const unlock = () => {
      try {
        if (!audioRef.current) audioRef.current = new Audio("/sounds/new-order.mp3");
        audioRef.current.muted = true;
        const p = audioRef.current.play();
        if (p && p.then) p.then(() => {
          audioRef.current.pause();
          audioRef.current.muted = false;
          audioRef.current.currentTime = 0;
          setSoundBlocked(false);
        }).catch(() => {});
      } catch { /* noop */ }
    };
    window.addEventListener("pointerdown", unlock, { once: true });
    return () => window.removeEventListener("pointerdown", unlock);
  }, []);

  async function toggle(o) {
    const next = !open[o.id];
    setOpen((m) => ({ ...m, [o.id]: next }));
    // позиции OpenCart-заказов не приходят в list — догружаем по order/get
    if (next && o.source === "stroiapp.ru" && !(o.items || []).length && !itemsCache[o.order_id]) {
      setItemsLoading((m) => ({ ...m, [o.order_id]: true }));
      try {
        const d = await apiGet(`/opencart/orders/${o.order_id}`);
        const items = (d.products || []).map((p) => ({
          name: p.name, qty: p.quantity, price: p.price,
          sku: p.sku || p.product_sku || p.model || (p.product_id ? String(p.product_id) : ""),
          weight: Number(p.product_weight || 0),
        }));
        setItemsCache((m) => ({ ...m, [o.order_id]: items }));
      } catch {
        setItemsCache((m) => ({ ...m, [o.order_id]: [] }));
      } finally {
        setItemsLoading((m) => ({ ...m, [o.order_id]: false }));
      }
    }
  }

  async function load(silent = false) {
    if (!silent) setLoading(true);
    setError("");
    try {
      const data = await apiGet("/promotions/orders?limit=500");
      const list = data.orders || [];
      // детект новых заказов: сравниваем набор id с предыдущим опросом
      if (seenIds.current !== null && soundOn) {
        const fresh = list.filter((o) => !seenIds.current.has(o.id));
        if (fresh.length) {
          playDing();
          setFreshIds(new Set(fresh.map((o) => o.id)));
          setTimeout(() => setFreshIds(new Set()), 20000);
        }
      }
      seenIds.current = new Set(list.map((o) => o.id));
      setOrders(list);
      if (data.status === "partial") setError(data.error || "");
    } catch (e) {
      if (!silent) setError(e.message);
    } finally {
      if (!silent) setLoading(false);
    }
  }

  React.useEffect(() => {
    load();
    const t = setInterval(() => load(true), POLL_MS);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [soundOn]);

  // Скачать счёт 1С PDF — POST на /promotions/orders/invoice-pdf, ответ blob
  async function downloadPdf(o, items) {
    setPdfBusy((m) => ({ ...m, [o.id]: true }));
    try {
      const res = await fetch(apiUrl("/promotions/orders/invoice-pdf"), {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Auth-Token": getToken() },
        body: JSON.stringify({
          order_id: o.order_id, customer: o.customer, phone: o.phone,
          address: o.address, inn: o.inn, items,
        }),
      });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.detail || `HTTP ${res.status}`);
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `schet-${o.order_id}.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setError(`Счёт PDF: ${e.message}`);
    } finally {
      setPdfBusy((m) => ({ ...m, [o.id]: false }));
    }
  }

  const shown = orders.filter((o) =>
    (src === "all" || o.source === src) &&
    (pay === "all" || o.payment_kind === pay)
  );

  async function setStatus(o, status) {
    if (o.source !== "moscow.stroiapp.ru") return;
    try {
      await apiPost(`/promotions/orders/status/${o.order_id}`, { status });
      setOrders((xs) => xs.map((x) => (x.id === o.id ? { ...x, status } : x)));
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-stone-800 bg-stone-900 p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/15 p-2.5"><ShoppingBag size={22} className="text-emerald-400" /></div>
            <div>
              <h2 className="text-lg font-bold text-white">Заказы</h2>
              <p className="text-sm text-stone-400">Сводная лента заказов: stroiapp.ru (OpenCart) и moscow.stroiapp.ru (витрина)</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {soundOn && soundBlocked && (
              <button onClick={playDing}
                className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs font-semibold text-amber-300">
                Звук заблокирован — нажмите
              </button>
            )}
            <button onClick={() => { const v = !soundOn; setSoundOn(v); if (v) playDing(); }}
              title={soundOn ? "Звук новых заказов: вкл" : "Звук новых заказов: выкл"}
              className={`rounded-lg border p-2 transition ${soundOn ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400" : "border-stone-700 bg-stone-950 text-stone-500"}`}>
              {soundOn ? <Volume2 size={16} /> : <VolumeX size={16} />}
            </button>
            <button onClick={() => load()} disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-stone-950 hover:bg-emerald-400 disabled:opacity-50">
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              {loading ? "Загрузка..." : "Обновить"}
            </button>
          </div>
        </div>

        {/* Фильтры */}
        <div className="mb-5 flex flex-wrap gap-2">
          <div className="flex overflow-hidden rounded-lg border border-stone-800">
            {SRC_FILTERS.map((f) => (
              <button key={f.id} onClick={() => setSrc(f.id)}
                className={`px-3.5 py-2 text-xs font-semibold transition ${src === f.id ? "bg-emerald-500 text-stone-950" : "bg-stone-950 text-stone-400 hover:text-white"}`}>
                {f.label}
              </button>
            ))}
          </div>
          <div className="flex overflow-hidden rounded-lg border border-stone-800">
            {PAY_FILTERS.map((f) => (
              <button key={f.id} onClick={() => setPay(f.id)}
                className={`px-3.5 py-2 text-xs font-semibold transition ${pay === f.id ? "bg-sky-500 text-white" : "bg-stone-950 text-stone-400 hover:text-white"}`}>
                {f.label}
              </button>
            ))}
          </div>
          <div className="ml-auto self-center text-xs text-stone-500">
            Показано: <b className="text-white">{shown.length}</b> из {orders.length}
          </div>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-sm text-amber-300">
            {error}
          </div>
        )}

        {/* Таблица заказов */}
        <div className="overflow-auto rounded-xl border border-stone-800">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-stone-950 text-left text-xs uppercase tracking-wider text-stone-500">
                <th className="w-8 px-3 py-3"></th>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Источник заказа</th>
                <th className="px-4 py-3">Дата</th>
                <th className="px-4 py-3">Клиент</th>
                <th className="px-4 py-3">Оплата</th>
                <th className="px-4 py-3 text-right">Сумма</th>
                <th className="px-4 py-3">Статус</th>
              </tr>
            </thead>
            <tbody>
              {!loading && shown.length === 0 && (
                <tr><td colSpan={8} className="px-4 py-10 text-center text-stone-500">
                  Заказов нет — загрузите список или измените фильтры
                </td></tr>
              )}
              {shown.map((o) => {
                const expanded = !!open[o.id];
                const items = (o.items && o.items.length)
                  ? o.items
                  : (itemsCache[o.order_id] || []);
                const itLoading = !!itemsLoading[o.order_id];
                const isNew = NEW_STATUSES.has(o.status || "") || freshIds.has(o.id);
                return (
                  <React.Fragment key={o.id}>
                    <tr className={`border-t border-stone-800/70 hover:bg-stone-800/40 ${isNew ? "order-new-glow" : ""}`}>
                      <td className="px-3 py-3">
                        <button onClick={() => toggle(o)}
                          className="text-stone-500 hover:text-white">
                          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        </button>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-stone-400">
                        <div>№ {o.order_id}</div>
                        {o.daily_no && (
                          <div className="mt-0.5 text-[10px] text-stone-600">
                            {String(o.date || "").slice(0, 10).split("-").reverse().join(".")} / дн.№{o.daily_no}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded-md border px-2 py-0.5 text-xs font-semibold ${SRC_BADGE[o.source] || "bg-stone-800 text-stone-300 border-stone-700"}`}>
                          {o.source}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-stone-400">{String(o.date || "").replace("T", " ").slice(0, 16)}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-white">{o.customer}</div>
                        {o.phone && <div className="text-xs text-stone-500">{o.phone}</div>}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium ${o.payment_kind === "invoice" ? "text-sky-400" : "text-stone-300"}`}>
                          {o.payment}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-bold text-white">{money(o.total)}</td>
                      <td className="px-4 py-3">
                        {o.source === "moscow.stroiapp.ru" ? (
                          <select value={o.status || "new"} onChange={(e) => setStatus(o, e.target.value)}
                            className={`rounded-md border border-stone-700 bg-stone-950 px-2 py-1 text-xs font-semibold outline-none ${STATUS_STYLE[o.status]?.split(" ")[1] || "text-stone-300"}`}>
                            {Object.keys(STATUS_LABEL).map((s) => (
                              <option key={s} value={s} className="text-white">{STATUS_LABEL[s]}</option>
                            ))}
                          </select>
                        ) : (
                          <span className={`rounded-md px-2 py-0.5 text-xs font-semibold ${STATUS_STYLE[o.status] || "bg-stone-800 text-stone-300"}`}>
                            {STATUS_LABEL[o.status] || o.status || "—"}
                          </span>
                        )}
                      </td>
                    </tr>
                    {expanded && (
                      <tr className="border-t border-stone-800/40 bg-stone-950/60">
                        <td colSpan={8} className="px-6 py-4">
                          <div className="grid gap-6 md:grid-cols-12">
                            {/* ЛЕВАЯ КОЛОНКА: карточка клиента + действия */}
                            <div className="md:col-span-4">
                              <div className="rounded-xl border border-stone-800 bg-stone-900/80 p-4">
                                <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-stone-500">
                                  <User size={13} /> Клиент
                                </div>
                                <div className="mb-3 space-y-2">
                                  <div className="text-sm font-bold text-white">{o.customer}</div>
                                  {o.phone && <div className="flex items-center gap-2 text-xs text-stone-400"><Phone size={13} className="text-stone-500" /> {o.phone}</div>}
                                  {o.address && <div className="flex items-center gap-2 text-xs text-stone-400"><MapPin size={13} className="text-stone-500" /> {o.address}</div>}
                                  {o.inn && <div className="flex items-center gap-2 text-xs text-stone-400"><Building2 size={13} className="text-stone-500" /> ИНН {o.inn}</div>}
                                  <div className="flex items-center gap-2 text-xs text-stone-400"><CreditCard size={13} className="text-stone-500" /> {o.payment}</div>
                                </div>
                                <div className="space-y-2 border-t border-stone-800 pt-3">
                                  <button onClick={() => downloadPdf(o, items)} disabled={!items.length || !!pdfBusy[o.id]}
                                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 px-3 py-2 text-xs font-bold text-stone-950 hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40">
                                    {pdfBusy[o.id] ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
                                    Скачать счёт 1С PDF
                                  </button>
                                  <button onClick={() => exportCsv(o, items)} disabled={!items.length}
                                    className="flex w-full items-center justify-center gap-2 rounded-lg border border-sky-500/40 bg-sky-500/10 px-3 py-2 text-xs font-bold text-sky-300 hover:bg-sky-500/20 disabled:cursor-not-allowed disabled:opacity-40">
                                    <FileSpreadsheet size={14} />
                                    Экспорт сметы в Excel
                                  </button>
                                  <button onClick={() => printOrder(o, items)} disabled={!items.length}
                                    className="flex w-full items-center justify-center gap-2 rounded-lg border border-stone-600 bg-stone-800 px-3 py-2 text-xs font-bold text-stone-200 hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-40">
                                    <Printer size={14} />
                                    Печать накладной
                                  </button>
                                  {!items.length && !itLoading && (
                                    <div className="text-center text-[10px] text-stone-600">кнопки активны при наличии состава</div>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="md:col-span-8">
                              {itLoading ? (
                                <div className="text-xs text-stone-500">Загружаю состав…</div>
                              ) : items.length > 0 ? (
                                <div>
                                  <div className="mb-1 flex justify-between text-[11px] uppercase tracking-wider text-stone-500">
                                    <span>Состав заказа</span><span>{items.length} поз.</span>
                                  </div>
                                  <div className="max-h-[450px] overflow-y-auto rounded-xl border border-stone-800 scrollbar-thin">
                                    <table className="w-full text-xs">
                                      <thead className="sticky top-0 bg-stone-900">
                                        <tr className="text-left text-[10px] uppercase text-stone-500">
                                          <th className="w-10 px-2.5 py-2">№</th>
                                          <th className="w-24 px-2 py-2">Артикул</th>
                                          <th className="px-2 py-2">Товар</th>
                                          <th className="w-14 px-2 py-2 text-right">Кол-во</th>
                                          <th className="w-20 px-2 py-2 text-right">Цена</th>
                                          <th className="w-24 px-2.5 py-2 text-right">Сумма</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {items.map((it, i) => {
                                          const q = Number(it.qty || it.quantity || 1);
                                          const p = Number(it.price || 0);
                                          return (
                                            <tr key={i} className="border-b border-stone-800/50 last:border-0 hover:bg-stone-800/30">
                                              <td className="px-2.5 py-1.5 font-mono text-stone-600">{i + 1}</td>
                                              <td className="px-2 py-1.5 font-mono text-[11px] text-stone-500 line-clamp-1">{it.sku || "—"}</td>
                                              <td className="max-w-0 px-2 py-1.5 text-stone-300"><div className="line-clamp-1" title={it.name || ""}>{it.name || it.product || it.model || "—"}</div></td>
                                              <td className="px-2 py-1.5 text-right text-stone-500">{q}</td>
                                              <td className="px-2 py-1.5 text-right text-stone-500">{p ? money(p) : ""}</td>
                                              <td className="px-2.5 py-1.5 text-right text-stone-300">{p ? money(p * q) : ""}</td>
                                            </tr>
                                          );
                                        })}
                                      </tbody>
                                    </table>
                                  </div>
                                </div>
                              ) : (
                                <div className="text-xs text-stone-600">Состав заказа недоступен</div>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      {printData && createPortal(
        <PrintableOrder o={printData.o} items={printData.items} />,
        document.body
      )}
    </div>
  );
}

/* ============ Печатная форма накладной (строго Ч/Б, рендерится порталом в body) ============ */
function PrintableOrder({ o, items }) {
  const dstr = String(o.date || "");
  const date = dstr.slice(0, 10).split("-").reverse().join(".");
  const time = dstr.slice(11, 16);
  const totalWeight = items.reduce(
    (s, it) => s + (Number(it.weight) || weightFromName(it.name || it.product || it.model || ""))
      * Number(it.qty || it.quantity || 1), 0
  );
  const payLabel = o.payment_kind === "invoice"
    ? `Безналичный расчёт (${o.payment || "счёт на оплату"})`
    : `Наличные при получении${o.payment && o.payment !== "Наличные" ? ` (${o.payment})` : ""}`;

  return (
    <div className="printable-order-content">
      <div className="po-title">
        Заказ № {o.order_id} / {date} / № {o.daily_no || "—"}
      </div>
      <div className="po-meta">время заказа: {time || "—"} · источник: {o.source}</div>

      <table className="po-info">
        <tbody>
          <tr><td className="po-k">Клиент:</td><td className="po-v">{o.customer || "—"}</td></tr>
          <tr><td className="po-k">Телефон на объекте:</td><td className="po-v">{o.phone || "—"}</td></tr>
          <tr><td className="po-k">Адрес доставки:</td><td className="po-v">{o.address || "—"}</td></tr>
          {o.inn ? <tr><td className="po-k">ИНН:</td><td className="po-v">{o.inn}</td></tr> : null}
          <tr><td className="po-k">Оплата:</td><td className="po-v">{payLabel}</td></tr>
        </tbody>
      </table>

      <table className="po-items">
        <thead>
          <tr>
            <th>№ п/п</th><th>Артикул</th><th>Наименование</th>
            <th>Кол-во</th><th>Ед.</th><th>Цена</th><th>Сумма</th>
            <th className="po-check">Контроль сборки (V)</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it, i) => {
            const q = Number(it.qty || it.quantity || 1);
            const p = Number(it.price || 0);
            return (
              <tr key={i}>
                <td>{i + 1}</td>
                <td>{it.sku || "—"}</td>
                <td>{it.name || it.product || it.model || "—"}</td>
                <td>{q}</td>
                <td>шт</td>
                <td>{money(p)}</td>
                <td>{money(p * q)}</td>
                <td className="po-check"></td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <div className="po-totals">
        <div>Итого позиций: {items.length}</div>
        <div>Общий вес груза: ~{totalWeight > 0 ? `${Math.round(totalWeight * 10) / 10} кг` : "н/д"}</div>
        <div><b>Всего к оплате: {money(o.total)}</b></div>
      </div>

      <div className="po-sign">
        <span>Склад отгрузил (подпись): _________________</span>
        <span>Водитель/Курьер принял (подпись): _________________</span>
      </div>
    </div>
  );
}
