import React from "react";
import { Truck, RefreshCw, Plus, Trash2, Pencil, Fuel, Wrench, CircleDot } from "lucide-react";
import { apiGet, apiPost, apiPut, apiDelete } from "../lib/api";

const money = (n) => new Intl.NumberFormat("ru-RU").format(Math.round(Number(n) || 0)) + " ₽";
const num = (v) => { const n = parseFloat(String(v).replace(",", ".")); return Number.isFinite(n) ? n : 0; };

const EXP_TYPES = {
  fuel: { label: "Бензин", cls: "bg-amber-500/15 text-amber-400" },
  repair: { label: "Ремонт", cls: "bg-red-500/15 text-red-400" },
  service: { label: "ТО", cls: "bg-sky-500/15 text-sky-400" },
  parking: { label: "Парковка", cls: "bg-violet-500/15 text-violet-400" },
  fine: { label: "Штраф", cls: "bg-orange-500/15 text-orange-400" },
  other: { label: "Прочее", cls: "bg-slate-700/50 text-slate-300" },
};

const V_TYPES = {
  car: "Легковой", van: "Фургон", truck: "Грузовой", semi: "Фура", other: "Другое",
};

const EMPTY_V = {
  name: "", vehicle_type: "van", vin: "", plate_number: "", driver_name: "", driver_phone: "",
  max_weight_kg: "", max_volume_m3: "", max_length_mm: "", fuel_rate_l100km: "",
  cost_per_km: "", base_cost: "", min_cost: "", odometer_km: "",
};
const EMPTY_E = { expense_type: "fuel", amount: "", liters: "", odometer_km: "", comment: "", expense_date: "" };

const inputCls = "w-full rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-emerald-500/60 focus:outline-none";
const labelCls = "mb-1 block text-[11px] font-medium uppercase tracking-wide text-slate-500";

function Field({ label, children }) {
  return <label className="block"><span className={labelCls}>{label}</span>{children}</label>;
}

export default function FleetPanel() {
  const [fleet, setFleet] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [ok, setOk] = React.useState("");

  const [showForm, setShowForm] = React.useState(false);
  const [editId, setEditId] = React.useState(null);
  const [vf, setVf] = React.useState(EMPTY_V);
  const [vinBusy, setVinBusy] = React.useState(false);

  const [sel, setSel] = React.useState(null);          // выбранная машина
  const [expenses, setExpenses] = React.useState([]);
  const [ef, setEf] = React.useState(EMPTY_E);

  async function load() {
    setLoading(true); setError("");
    try {
      const d = await apiGet("/logistics/fleet");
      setFleet(d.fleet || []);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  React.useEffect(() => { load(); }, []);

  function flash(m) { setOk(m); setTimeout(() => setOk(""), 3000); }

  async function decodeVin() {
    if (!vf.vin.trim()) return;
    setVinBusy(true); setError("");
    try {
      const d = await apiPost("/logistics/vehicles/decode-vin", { vin: vf.vin.trim() });
      if (d.status !== "ok") throw new Error(d.message || "VIN не распознан");
      setVf((p) => ({
        ...p,
        name: p.name || d.name,
        max_weight_kg: p.max_weight_kg || (d.max_weight_kg ? String(d.max_weight_kg) : ""),
      }));
      flash(`VIN: ${d.name || "?"} ${d.year || ""}`.trim());
    } catch (e) { setError(e.message); }
    finally { setVinBusy(false); }
  }

  async function saveVehicle(e) {
    e.preventDefault(); setError("");
    const body = {
      name: vf.name, vehicle_type: vf.vehicle_type, vin: vf.vin, plate_number: vf.plate_number,
      driver_name: vf.driver_name, driver_phone: vf.driver_phone,
      max_weight_kg: num(vf.max_weight_kg), max_volume_m3: num(vf.max_volume_m3),
      max_length_mm: num(vf.max_length_mm), fuel_rate_l100km: num(vf.fuel_rate_l100km),
      cost_per_km: num(vf.cost_per_km), base_cost: num(vf.base_cost),
      min_cost: num(vf.min_cost), odometer_km: num(vf.odometer_km),
    };
    try {
      if (editId) await apiPut(`/logistics/vehicles/${editId}`, body);
      else await apiPost("/logistics/vehicles", body);
      setShowForm(false); setEditId(null); setVf(EMPTY_V);
      flash(editId ? "Машина обновлена" : "Машина добавлена");
      load();
    } catch (e2) { setError(e2.message); }
  }

  function startEdit(v) {
    setEditId(v.id);
    setVf({
      name: v.name || "", vehicle_type: v.vehicle_type || "van", vin: v.vin || "", plate_number: v.plate_number || "",
      driver_name: v.driver_name || "", driver_phone: v.driver_phone || "",
      max_weight_kg: v.max_weight_kg ?? "", max_volume_m3: v.max_volume_m3 ?? "",
      max_length_mm: v.max_length_mm ?? "", fuel_rate_l100km: v.fuel_rate_l100km ?? "",
      cost_per_km: v.cost_per_km ?? "", base_cost: v.base_cost ?? "",
      min_cost: v.min_cost ?? "", odometer_km: v.odometer_km ?? "",
    });
    setShowForm(true);
  }

  async function removeVehicle(id) {
    if (!window.confirm("Удалить машину и её расходы?")) return;
    try {
      await apiDelete(`/logistics/vehicles/${id}`);
      if (sel === id) { setSel(null); setExpenses([]); }
      load();
    } catch (e) { setError(e.message); }
  }

  async function selectVehicle(id) {
    if (sel === id) { setSel(null); setExpenses([]); return; }
    setSel(id); setError("");
    try {
      const d = await apiGet(`/logistics/vehicles/${id}/expenses`);
      setExpenses(d.expenses || []);
    } catch (e) { setError(e.message); }
  }

  async function addExpense(e) {
    e.preventDefault(); setError("");
    try {
      await apiPost(`/logistics/vehicles/${sel}/expenses`, {
        expense_type: ef.expense_type, amount: num(ef.amount), liters: num(ef.liters),
        odometer_km: num(ef.odometer_km), comment: ef.comment, expense_date: ef.expense_date,
      });
      setEf(EMPTY_E); flash("Расход записан");
      selectVehicle(sel); setSel(null); selectVehicle(sel); // перезагрузить
      const d = await apiGet(`/logistics/vehicles/${sel}/expenses`);
      setExpenses(d.expenses || []);
      load();
    } catch (e2) { setError(e2.message); }
  }

  async function removeExpense(id) {
    try {
      await apiDelete(`/logistics/expenses/${id}`);
      setExpenses((p) => p.filter((x) => x.id !== id));
      load();
    } catch (e) { setError(e.message); }
  }

  const selStats = fleet.find((f) => f.vehicle.id === sel);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <Truck size={20} className="text-emerald-400" /> Автопарк
        </h2>
        <div className="flex items-center gap-2">
          <button onClick={load} className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800">
            <RefreshCw size={14} className={loading ? "inline animate-spin" : "inline"} /> Обновить
          </button>
          <button
            onClick={() => { setShowForm(!showForm); setEditId(null); setVf(EMPTY_V); }}
            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
          >
            <Plus size={14} className="inline" /> Машина
          </button>
        </div>
      </div>

      {error && <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300">{error}</div>}
      {ok && <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-300">{ok}</div>}

      {/* Форма машины */}
      {showForm && (
        <form onSubmit={saveVehicle} className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="mb-3 text-sm font-bold text-slate-200">{editId ? "Редактировать машину" : "Новая машина"}</div>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Field label="VIN">
              <div className="flex gap-1">
                <input className={inputCls} value={vf.vin} onChange={(e) => setVf({ ...vf, vin: e.target.value })} placeholder="17 символов" />
                <button type="button" onClick={decodeVin} disabled={vinBusy}
                  className="shrink-0 rounded-lg bg-sky-600 px-2 text-[11px] font-semibold text-white hover:bg-sky-500 disabled:opacity-50">
                  {vinBusy ? "…" : "VIN"}
                </button>
              </div>
            </Field>
            <Field label="Категория">
              <select className={inputCls} value={vf.vehicle_type} onChange={(e) => setVf({ ...vf, vehicle_type: e.target.value })}>
                {Object.entries(V_TYPES).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
              </select>
            </Field>
            <Field label="Название *"><input required className={inputCls} value={vf.name} onChange={(e) => setVf({ ...vf, name: e.target.value })} placeholder="Газель NEXT" /></Field>
            <Field label="Госномер"><input className={inputCls} value={vf.plate_number} onChange={(e) => setVf({ ...vf, plate_number: e.target.value })} placeholder="А123БВ777" /></Field>
            <Field label="Тоннаж, кг *"><input required type="number" className={inputCls} value={vf.max_weight_kg} onChange={(e) => setVf({ ...vf, max_weight_kg: e.target.value })} placeholder="1500" /></Field>
            <Field label="Водитель"><input className={inputCls} value={vf.driver_name} onChange={(e) => setVf({ ...vf, driver_name: e.target.value })} placeholder="Иванов И." /></Field>
            <Field label="Телефон водителя"><input className={inputCls} value={vf.driver_phone} onChange={(e) => setVf({ ...vf, driver_phone: e.target.value })} placeholder="+7…" /></Field>
            <Field label="Объём кузова, м³"><input type="number" className={inputCls} value={vf.max_volume_m3} onChange={(e) => setVf({ ...vf, max_volume_m3: e.target.value })} placeholder="9" /></Field>
            <Field label="Длина кузова, мм"><input type="number" className={inputCls} value={vf.max_length_mm} onChange={(e) => setVf({ ...vf, max_length_mm: e.target.value })} placeholder="3000" /></Field>
            <Field label="Расход, л/100км"><input type="number" step="0.1" className={inputCls} value={vf.fuel_rate_l100km} onChange={(e) => setVf({ ...vf, fuel_rate_l100km: e.target.value })} placeholder="12" /></Field>
            <Field label="Пробег, км"><input type="number" className={inputCls} value={vf.odometer_km} onChange={(e) => setVf({ ...vf, odometer_km: e.target.value })} placeholder="0" /></Field>
            <Field label="Тариф ₽/км"><input type="number" className={inputCls} value={vf.cost_per_km} onChange={(e) => setVf({ ...vf, cost_per_km: e.target.value })} placeholder="30" /></Field>
            <Field label="Подать машину, ₽"><input type="number" className={inputCls} value={vf.base_cost} onChange={(e) => setVf({ ...vf, base_cost: e.target.value })} placeholder="500" /></Field>
            <Field label="Мин. доставка, ₽"><input type="number" className={inputCls} value={vf.min_cost} onChange={(e) => setVf({ ...vf, min_cost: e.target.value })} placeholder="1000" /></Field>
          </div>
          <div className="mt-3 flex gap-2">
            <button className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500">
              {editId ? "Сохранить" : "Добавить"}
            </button>
            <button type="button" onClick={() => { setShowForm(false); setEditId(null); setVf(EMPTY_V); }}
              className="rounded-lg border border-slate-700 px-4 py-2 text-xs text-slate-300 hover:bg-slate-800">Отмена</button>
          </div>
        </form>
      )}

      {/* Таблица машин */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/60 text-[11px] uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-2">Машина</th>
              <th className="px-3 py-2">Госномер / VIN</th>
              <th className="px-3 py-2">Водитель</th>
              <th className="px-3 py-2">Тоннаж / Объём / Длина</th>
              <th className="px-3 py-2">Пробег</th>
              <th className="px-3 py-2">Расход л/100</th>
              <th className="px-3 py-2">Затраты</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {fleet.map((f) => {
              const v = f.vehicle;
              return (
                <React.Fragment key={v.id}>
                  <tr onClick={() => selectVehicle(v.id)}
                    className={`cursor-pointer transition-colors hover:bg-slate-800/50 ${sel === v.id ? "bg-slate-800/60" : ""}`}>
                    <td className="px-3 py-2.5 font-medium text-slate-200">
                      {v.name}
                      {v.vehicle_type && (
                        <span className="ml-2 rounded bg-sky-500/15 px-1.5 py-0.5 text-[10px] font-medium text-sky-400">
                          {V_TYPES[v.vehicle_type] || v.vehicle_type}
                        </span>
                      )}
                      {!v.is_active && <span className="ml-2 rounded bg-slate-700 px-1.5 py-0.5 text-[10px] text-slate-400">неактивна</span>}
                    </td>
                    <td className="px-3 py-2.5 text-slate-400">
                      <div>{v.plate_number || "—"}</div>
                      {v.vin && <div className="text-[10px] text-slate-600">{v.vin}</div>}
                    </td>
                    <td className="px-3 py-2.5 text-slate-400">
                      <div>{v.driver_name || "—"}</div>
                      {v.driver_phone && <div className="text-[10px] text-slate-600">{v.driver_phone}</div>}
                    </td>
                    <td className="px-3 py-2.5 text-slate-400">
                      {v.max_weight_kg >= 1000 ? `${(v.max_weight_kg / 1000).toFixed(1)} т` : `${v.max_weight_kg} кг`}
                      {v.max_volume_m3 ? ` · ${v.max_volume_m3} м³` : ""}
                      {v.max_length_mm ? ` · ${(v.max_length_mm / 1000).toFixed(1)} м` : ""}
                    </td>
                    <td className="px-3 py-2.5 text-slate-400">{v.odometer_km ? `${Math.round(v.odometer_km).toLocaleString("ru-RU")} км` : "—"}</td>
                    <td className="px-3 py-2.5">
                      <span className={f.actual_l100km ? "text-amber-400" : "text-slate-500"}>
                        {f.actual_l100km || v.fuel_rate_l100km || "—"}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 font-semibold text-slate-200">{f.total_amount ? money(f.total_amount) : "—"}</td>
                    <td className="px-3 py-2.5">
                      <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                        <button onClick={() => startEdit(v)} className="rounded p-1 text-slate-500 hover:bg-slate-700 hover:text-slate-200"><Pencil size={14} /></button>
                        <button onClick={() => removeVehicle(v.id)} className="rounded p-1 text-slate-500 hover:bg-red-500/20 hover:text-red-400"><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>

                  {/* Раскрытая карточка: расходы */}
                  {sel === v.id && (
                    <tr><td colSpan={8} className="bg-slate-900/50 px-4 py-4">
                      <div className="mb-3 grid grid-cols-2 gap-3 md:grid-cols-5">
                        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                          <div className="text-[10px] uppercase text-slate-500">Всего расходов</div>
                          <div className="text-lg font-bold text-slate-100">{money(f.total_amount)}</div>
                        </div>
                        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                          <div className="text-[10px] uppercase text-slate-500"><Fuel size={10} className="inline" /> Топливо</div>
                          <div className="text-lg font-bold text-amber-400">{money(f.fuel_amount)}</div>
                          <div className="text-[10px] text-slate-500">{Math.round(f.fuel_liters || 0)} л</div>
                        </div>
                        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                          <div className="text-[10px] uppercase text-slate-500"><Wrench size={10} className="inline" /> Ремонт + ТО</div>
                          <div className="text-lg font-bold text-red-400">{money((f.repair_amount || 0) + (f.service_amount || 0))}</div>
                        </div>
                        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                          <div className="text-[10px] uppercase text-slate-500"><CircleDot size={10} className="inline" /> Пробег учётный</div>
                          <div className="text-lg font-bold text-slate-100">{f.distance_km ? `${Math.round(f.distance_km).toLocaleString("ru-RU")} км` : "—"}</div>
                        </div>
                        <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
                          <div className="text-[10px] uppercase text-slate-500">Расход факт.</div>
                          <div className="text-lg font-bold text-emerald-400">{f.actual_l100km ? `${f.actual_l100km} л/100` : "—"}</div>
                        </div>
                      </div>

                      {/* форма расхода */}
                      <form onSubmit={addExpense} className="mb-3 flex flex-wrap items-end gap-2">
                        <label><span className={labelCls}>Тип</span>
                          <select className={inputCls} value={ef.expense_type} onChange={(e) => setEf({ ...ef, expense_type: e.target.value })}>
                            {Object.entries(EXP_TYPES).map(([k, t]) => <option key={k} value={k}>{t.label}</option>)}
                          </select>
                        </label>
                        <label><span className={labelCls}>Сумма ₽</span>
                          <input required type="number" className={inputCls} style={{ width: 110 }} value={ef.amount} onChange={(e) => setEf({ ...ef, amount: e.target.value })} /></label>
                        {ef.expense_type === "fuel" && (
                          <label><span className={labelCls}>Литров</span>
                            <input type="number" step="0.1" className={inputCls} style={{ width: 90 }} value={ef.liters} onChange={(e) => setEf({ ...ef, liters: e.target.value })} /></label>
                        )}
                        <label><span className={labelCls}>Одометр км</span>
                          <input type="number" className={inputCls} style={{ width: 110 }} value={ef.odometer_km} onChange={(e) => setEf({ ...ef, odometer_km: e.target.value })} /></label>
                        <label><span className={labelCls}>Дата</span>
                          <input type="date" className={inputCls} style={{ width: 140 }} value={ef.expense_date} onChange={(e) => setEf({ ...ef, expense_date: e.target.value })} /></label>
                        <label className="flex-1"><span className={labelCls}>Комментарий</span>
                          <input className={inputCls} value={ef.comment} onChange={(e) => setEf({ ...ef, comment: e.target.value })} placeholder="АЗС Лукойл…" /></label>
                        <button className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500">+ Расход</button>
                      </form>

                      {/* журнал */}
                      <table className="w-full text-left text-xs">
                        <thead className="text-[10px] uppercase text-slate-500">
                          <tr><th className="py-1">Дата</th><th>Тип</th><th>Сумма</th><th>Литры</th><th>Одометр</th><th>Комментарий</th><th></th></tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {expenses.map((x) => (
                            <tr key={x.id} className="text-slate-300">
                              <td className="py-1.5">{x.expense_date}</td>
                              <td><span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${(EXP_TYPES[x.expense_type] || EXP_TYPES.other).cls}`}>
                                {(EXP_TYPES[x.expense_type] || EXP_TYPES.other).label}</span></td>
                              <td className="font-medium">{money(x.amount)}</td>
                              <td>{x.liters ? `${x.liters} л` : "—"}</td>
                              <td>{x.odometer_km ? Math.round(x.odometer_km).toLocaleString("ru-RU") : "—"}</td>
                              <td className="text-slate-500">{x.comment}</td>
                              <td><button onClick={() => removeExpense(x.id)} className="text-slate-600 hover:text-red-400"><Trash2 size={12} /></button></td>
                            </tr>
                          ))}
                          {!expenses.length && <tr><td colSpan={7} className="py-3 text-center text-slate-600">Расходов пока нет</td></tr>}
                        </tbody>
                      </table>
                    </td></tr>
                  )}
                </React.Fragment>
              );
            })}
            {!fleet.length && (
              <tr><td colSpan={8} className="px-3 py-8 text-center text-slate-500">
                {loading ? "Загрузка…" : "Машин нет — добавьте первую"}
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
      {selStats && null}
    </div>
  );
}
