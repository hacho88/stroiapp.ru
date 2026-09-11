import { useState } from "react";
import { Upload, Calculator, Download, AlertCircle, CheckCircle, Table, FileSpreadsheet } from "lucide-react";

const API_BASE = "http://127.0.0.1:8010/api";

async function apiPost(path, body) {
  const r = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export default function ForemanUploader({ addToast }) {
  const [skuInput, setSkuInput] = useState("");
  const [marginRetail, setMarginRetail] = useState(1.35);
  const [marginWholesale, setMarginWholesale] = useState(1.25);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fileLoading, setFileLoading] = useState(false);

  async function calculate() {
    const skus = skuInput
      .split(/[\n,;]/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (!skus.length) {
      addToast("Введите хотя бы один артикул (SKU)", "error");
      return;
    }
    setLoading(true);
    try {
      const data = await apiPost("/product/foreman/calculatePrices", {
        skus,
        margin_retail: marginRetail,
        margin_wholesale: marginWholesale,
      });
      setResults(data);
      addToast(`Расчёт выполнен: ${data.found} найдено, ${data.not_found} не найдено`, "success");
    } catch (err) {
      addToast("Ошибка расчёта: " + err.message, "error");
    }
    setLoading(false);
  }

  async function handleFileUpload(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileLoading(true);

    const ext = file.name.split('.').pop().toLowerCase();
    const isText = ['csv', 'txt', 'tsv'].includes(ext);

    try {
      if (isText) {
        const text = await file.text();
        const lines = text.split(/[\r\n]+/).map((l) => l.trim()).filter(Boolean);
        const skus = lines.map((line) => line.split(/[;,\t]/)[0].trim());
        setSkuInput(skus.join("\n"));
        addToast(`Загружено ${skus.length} SKU из текстового файла`, "success");
      } else {
        // PDF / Фото → отправляем на backend для OCR + DeepSeek
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/product/foreman/uploadDocument`, {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (data.skus && data.skus.length) {
          setSkuInput(data.skus.join("\n"));
          addToast(`Распознано ${data.skus.length} SKU (${data.source})`, "success");
        } else {
          addToast(`SKU не распознаны: ${data.error || 'неизвестная ошибка'}`, "error");
        }
      }
    } catch (err) {
      addToast("Ошибка загрузки файла: " + err.message, "error");
    }
    setFileLoading(false);
    e.target.value = "";
  }

  function exportCSV() {
    if (!results?.items?.length) return;
    const header = "SKU;Наименование;Найден;Себест.нал;Себест.б/нал;Розница;Опт;Ожид.прибыль;ROI\n";
    const rows = results.items
      .map(
        (r) =>
          `${r.sku};${r.name || "—"};${r.found ? "Да" : "Нет"};${r.cost_price_cash ?? "—"};${r.cost_price_cashless ?? "—"};${r.retail_price ?? "—"};${r.wholesale_price ?? "—"};${r.expected_profit ?? "—"};${r.roi ?? "—"}`
      )
      .join("\n");
    const bom = "\uFEFF";
    const blob = new Blob([bom + header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `price_list_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    addToast("Прайс-лист скачан", "success");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-6 py-3">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <FileSpreadsheet size={16} className="text-emerald-400" />
          Калькулятор цен для прораба
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-4xl space-y-6">
          {/* Upload Section */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
            <div className="mb-4 flex items-center gap-2 text-base font-bold text-white">
              <Upload size={16} className="text-blue-400" />
              Загрузка списка товаров
            </div>
            <div className="mb-4 flex gap-3">
              <label className="flex cursor-pointer items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-blue-500/20 transition-all hover:shadow-blue-500/40">
                <Upload size={14} />
                {fileLoading ? "Загрузка..." : "Загрузить документ"}
                <input type="file" accept=".csv,.txt,.pdf,.jpg,.jpeg,.png,.webp" className="hidden" onChange={handleFileUpload} />
              </label>
              <span className="self-center text-xs text-slate-500">или введите артикулы вручную:</span>
            </div>
            <textarea
              value={skuInput}
              onChange={(e) => setSkuInput(e.target.value)}
              placeholder="Введите SKU через запятую, точку с запятой или с новой строки...&#10;Например:&#10;0001&#10;0002&#10;0003"
              className="h-32 w-full rounded-xl border border-white/[0.08] bg-white/[0.03] p-4 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500/50"
            />
          </div>

          {/* Margin Settings */}
          <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
            <div className="mb-4 flex items-center gap-2 text-base font-bold text-white">
              <Calculator size={16} className="text-amber-400" />
              Настройки наценки
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-400">Коэфф. розницы</label>
                <input
                  type="number"
                  step="0.01"
                  value={marginRetail}
                  onChange={(e) => setMarginRetail(parseFloat(e.target.value) || 1.35)}
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm text-white outline-none focus:border-amber-500/50"
                />
                <p className="mt-1 text-[11px] text-slate-500">Например: 1.35 = +35%</p>
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-400">Коэфф. опта</label>
                <input
                  type="number"
                  step="0.01"
                  value={marginWholesale}
                  onChange={(e) => setMarginWholesale(parseFloat(e.target.value) || 1.25)}
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm text-white outline-none focus:border-amber-500/50"
                />
                <p className="mt-1 text-[11px] text-slate-500">Например: 1.25 = +25%</p>
              </div>
            </div>
          </div>

          {/* Calculate Button */}
          <button
            onClick={calculate}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 py-3 text-sm font-extrabold text-white shadow-lg shadow-emerald-500/20 transition-all hover:shadow-emerald-500/40 disabled:opacity-40"
          >
            <Calculator size={16} />
            {loading ? "Расчёт..." : "Рассчитать цены"}
          </button>

          {/* Results */}
          {results && (
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2 text-base font-bold text-white">
                  <Table size={16} className="text-violet-400" />
                  Результаты расчёта
                </div>
                <button
                  onClick={exportCSV}
                  className="flex items-center gap-2 rounded-lg bg-white/[0.05] px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:bg-white/[0.1] hover:text-white"
                >
                  <Download size={13} /> Скачать CSV
                </button>
              </div>

              <div className="mb-3 flex gap-4 text-xs">
                <span className="text-slate-400">
                  Всего: <span className="font-bold text-white">{results.total}</span>
                </span>
                <span className="text-emerald-400">
                  <CheckCircle size={12} className="mr-1 inline" />
                  Найдено: <span className="font-bold">{results.found}</span>
                </span>
                <span className="text-rose-400">
                  <AlertCircle size={12} className="mr-1 inline" />
                  Не найдено: <span className="font-bold">{results.not_found}</span>
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-white/[0.08] text-slate-500">
                      <th className="py-2 pr-4">SKU</th>
                      <th className="py-2 pr-4">Наименование</th>
                      <th className="py-2 pr-4">Себест. нал</th>
                      <th className="py-2 pr-4">Себест. б/нал</th>
                      <th className="py-2 pr-4">Розница</th>
                      <th className="py-2 pr-4">Опт</th>
                      <th className="py-2 pr-4">Прибыль</th>
                      <th className="py-2 pr-4">ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.items.map((item) => (
                      <tr
                        key={item.sku}
                        className={`border-b border-white/[0.04] transition hover:bg-white/[0.02] ${
                          !item.found ? "opacity-50" : ""
                        }`}
                      >
                        <td className="py-2 pr-4 font-mono text-slate-300">{item.sku}</td>
                        <td className="py-2 pr-4 text-white">{item.name || "—"}</td>
                        <td className="py-2 pr-4 text-slate-400">{item.cost_price_cash ?? "—"}</td>
                        <td className="py-2 pr-4 text-slate-400">{item.cost_price_cashless ?? "—"}</td>
                        <td className="py-2 pr-4 font-bold text-emerald-400">
                          {item.retail_price ? item.retail_price + " ₽" : "—"}
                        </td>
                        <td className="py-2 pr-4 font-bold text-blue-400">
                          {item.wholesale_price ? item.wholesale_price + " ₽" : "—"}
                        </td>
                        <td className="py-2 pr-4 text-amber-400">
                          {item.expected_profit ?? "—"}
                        </td>
                        <td className="py-2 pr-4 text-violet-400">{item.roi ? item.roi + "%" : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
