import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Copy, ExternalLink, FileText, Folder, FolderPlus, Image as ImageIcon, Link2, Package, RefreshCw, Search, Trash2, Upload, X } from "lucide-react";
import { apiGet, apiPost, apiUpload } from "../lib/api";

const fmtSize = (b) => !b ? "" : b < 1024 ? `${b} Б` : b < 1048576 ? `${(b / 1024).toFixed(1)} КБ` : `${(b / 1048576).toFixed(1)} МБ`;

export default function MediaPanel({ addToast }) {
  const [mode, setMode] = useState("products"); // products | files
  const [path, setPath] = useState("catalog");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [suggestions, setSuggestions] = useState([]); // {name, path, matches[]}
  const [products, setProducts] = useState([]);
  const [prodQuery, setProdQuery] = useState("");
  const [prodPage, setProdPage] = useState(1);
  const [prodLoading, setProdLoading] = useState(false);
  const [assignFor, setAssignFor] = useState(null); // product awaiting photo
  const fileInput = useRef(null);
  const assignInput = useRef(null);
  const notify = useCallback((m, t = "info") => addToast && addToast(m, t), [addToast]);

  // ---------- files mode ----------
  const load = useCallback(async (p) => {
    const target = p || path;
    setLoading(true);
    try {
      const d = await apiGet(`/opencart/media/list?path=${encodeURIComponent(target)}`);
      if (d.status === "error") throw new Error(d.detail || "ошибка");
      setItems(d.items || []);
      setPath(d.path || target);
    } catch (e) { notify("Ошибка: " + e.message, "error"); }
    finally { setLoading(false); }
  }, [path, notify]);

  // ---------- products mode ----------
  const [prodTotal, setProdTotal] = useState(0);
  const loadProducts = useCallback(async (q, pg) => {
    setProdLoading(true);
    try {
      const d = await apiGet(`/opencart/media/products?keyword=${encodeURIComponent(q || "")}&page=${pg || 1}&limit=60`);
      if (d.status === "error") throw new Error(d.detail || "ошибка");
      setProducts(d.products || []);
      setProdTotal(d.total || 0);
    } catch (e) { notify("Ошибка товаров: " + e.message, "error"); }
    finally { setProdLoading(false); }
  }, [notify]);

  useEffect(() => { loadProducts("", 1); /* eslint-disable-next-line */ }, []);

  const assignImage = async (match, imagePath) => {
    const r = await apiPost("/opencart/media/assign", {
      product_id: match.product_id || 0,
      import_id: match.import_id || 0,
      product_name: match.name || "",
      image: imagePath,
    }).catch((e) => ({ error: e.message }));
    if (r.error || r.status === "error") return notify(r.error || r.detail || "ошибка привязки", "error");
    notify(`Фото привязано: ${match.name}`, "success");
    setSuggestions((a) => a.filter((s) => s.path !== imagePath));
    if (mode === "products") loadProducts(prodQuery, prodPage);
  };

  const uploadFiles = async (files) => {
    if (!files?.length) return;
    setUploading(true);
    const uploaded = [];
    let ok = 0;
    for (const f of files) {
      try {
        const r = await apiUpload(`/opencart/media/upload?dir=${encodeURIComponent(path)}`, f);
        if (r.status === "uploaded") { ok++; uploaded.push({ name: f.name, path: r.path }); }
        else notify(`${f.name}: ${r.error || r.detail || "?"}`, "error");
      } catch (e) { notify(`${f.name}: ${e.message}`, "error"); }
    }
    setUploading(false);
    if (ok) notify(`Загружено: ${ok}`, "success");
    if (mode === "files") load();
    // auto-suggest product for each uploaded file
    for (const u of uploaded) {
      try {
        const s = await apiGet(`/opencart/media/suggest?filename=${encodeURIComponent(u.name)}`);
        if (s.products?.length) setSuggestions((a) => [...a, { ...u, matches: s.products }]);
      } catch { /* ignore */ }
    }
  };

  const uploadForProduct = async (file) => {
    if (!file || !assignFor) return;
    setUploading(true);
    try {
      const r = await apiUpload(`/opencart/media/upload?dir=catalog/products&name=${encodeURIComponent(assignFor.name)}`, file);
      if (r.status === "uploaded") {
        await assignImage(assignFor, r.path);
      } else notify(r.error || r.detail || "ошибка загрузки", "error");
    } catch (e) { notify(e.message, "error"); }
    setUploading(false);
    setAssignFor(null);
  };

  const createFolder = async () => {
    const name = window.prompt("Имя папки (латиница):");
    if (!name?.trim()) return;
    const clean = name.trim().replace(/[^a-zA-Z0-9._-]+/g, "_");
    const r = await apiPost("/opencart/media/mkdir", { path: `${path}/${clean}` }).catch((e) => ({ error: e.message }));
    if (r.error) return notify(r.error, "error");
    notify(`Папка ${clean} создана`, "success");
    load();
  };

  const removeFile = async (f) => {
    if (!window.confirm(`Удалить ${f.name}?`)) return;
    const r = await apiPost("/opencart/media/delete", { path: `${path}/${f.name}` }).catch((e) => ({ error: e.message }));
    if (r.error) return notify(r.error, "error");
    notify(`${f.name} удалён`, "success");
    setItems((a) => a.filter((x) => x.name !== f.name));
  };

  const copyUrl = (u) => navigator.clipboard?.writeText(u).then(() => notify("URL скопирован", "success"), () => window.prompt("URL:", u));

  const crumbs = ["image", ...path.split("/").filter(Boolean)];
  const goUp = () => { const p = path.split("/").filter(Boolean); if (p.length > 1) load(p.slice(0, -1).join("/")); };
  const dirs = items.filter((i) => i.type === "directory");
  const files = items.filter((i) => i.type === "file");

  return (
    <div className="space-y-4">
      {/* mode switch + toolbar */}
      <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-lg bg-slate-800 p-1">
            <button onClick={() => setMode("products")}
              className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm ${mode === "products" ? "bg-emerald-500 font-bold text-slate-950" : "text-slate-300 hover:text-white"}`}>
              <Package size={15} /> Товары
            </button>
            <button onClick={() => { setMode("files"); load("catalog"); }}
              className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm ${mode === "files" ? "bg-emerald-500 font-bold text-slate-950" : "text-slate-300 hover:text-white"}`}>
              <Folder size={15} /> Файлы
            </button>
          </div>
          <div className="flex-1" />
          {mode === "files" && (
            <>
              <button onClick={createFolder} className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700"><FolderPlus size={16} /> Папка</button>
              <button onClick={() => fileInput.current?.click()} disabled={uploading}
                className="btn-shine inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 glow-emerald">
                <Upload size={16} /> {uploading ? "Загрузка..." : "Загрузить"}
              </button>
            </>
          )}
          <input ref={fileInput} type="file" multiple accept="image/*" className="hidden"
            onChange={(e) => { uploadFiles([...e.target.files]); e.target.value = ""; }} />
          <input ref={assignInput} type="file" accept="image/*" className="hidden"
            onChange={(e) => { uploadForProduct(e.target.files[0]); e.target.value = ""; }} />
        </div>

        {mode === "files" && (
          <div className="flex flex-wrap items-center gap-2">
            <button onClick={goUp} disabled={path === "catalog"} className="rounded-lg bg-slate-800 p-2 hover:bg-slate-700 disabled:opacity-40"><ArrowLeft size={16} /></button>
            <div className="flex min-w-0 flex-1 items-center gap-1 overflow-auto text-sm">
              {crumbs.map((c, i) => (
                <span key={i} className="flex items-center gap-1 whitespace-nowrap">
                  {i > 0 && <span className="text-slate-600">/</span>}
                  <button onClick={() => i > 0 && load(crumbs.slice(1, i + 1).join("/"))}
                    className={i === crumbs.length - 1 ? "font-bold text-emerald-400" : "text-slate-400 hover:text-slate-200"}>{c}</button>
                </span>
              ))}
            </div>
            <button onClick={() => load()} disabled={loading} className="rounded-lg bg-slate-800 p-2 hover:bg-slate-700 disabled:opacity-40"><RefreshCw size={16} className={loading ? "animate-spin" : ""} /></button>
          </div>
        )}

        {mode === "products" && (
          <form onSubmit={(e) => { e.preventDefault(); setProdPage(1); loadProducts(prodQuery, 1); }} className="flex gap-2">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input value={prodQuery} onChange={(e) => setProdQuery(e.target.value)} placeholder="Поиск товара по названию..."
                className="w-full rounded-lg border border-slate-700/50 bg-slate-900 py-2 pl-9 pr-3 text-sm outline-none focus:border-emerald-500" />
            </div>
            <button type="submit" className="rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700">Найти</button>
            <button type="button" onClick={() => loadProducts(prodQuery, prodPage)} disabled={prodLoading}
              className="rounded-lg bg-slate-800 p-2 hover:bg-slate-700 disabled:opacity-40"><RefreshCw size={16} className={prodLoading ? "animate-spin" : ""} /></button>
          </form>
        )}
      </div>

      {/* auto-suggest after upload */}
      {suggestions.length > 0 && (
        <div className="rounded-2xl border border-emerald-500/40 bg-emerald-500/5 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-bold text-emerald-400">Привязать загруженные фото к товарам?</div>
            <button onClick={() => setSuggestions([])} className="text-slate-500 hover:text-slate-300"><X size={16} /></button>
          </div>
          {suggestions.map((s) => (
            <div key={s.path} className="flex flex-wrap items-center gap-2 rounded-lg bg-slate-900/60 p-2">
              <img src={`https://stroiapp.ru/image/${s.path}`} alt="" className="h-10 w-10 rounded object-cover" />
              <span className="max-w-[180px] truncate text-xs text-slate-400" title={s.name}>{s.name}</span>
              <span className="text-slate-600">→</span>
              <div className="flex flex-wrap gap-1">
                {s.matches.map((m) => (
                  <button key={m.product_id || m.import_id} onClick={() => assignImage(m, s.path)}
                    className="inline-flex items-center gap-1 rounded-lg bg-slate-800 px-2 py-1 text-xs hover:bg-emerald-600 hover:text-slate-950" title={m.name}>
                    <Link2 size={11} /> {m.name.length > 40 ? m.name.slice(0, 40) + "…" : m.name}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PRODUCTS MODE */}
      {mode === "products" && (
        <div className="rounded-2xl border border-slate-700/30 glass p-4">
          {prodLoading ? (
            <div className="py-10 text-center text-sm text-slate-500">Загрузка товаров...</div>
          ) : products.length > 0 ? (
            <>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                {products.map((p) => (
                  <div key={p.product_id || `imp${p.import_id}`} className="group relative overflow-hidden rounded-xl border border-slate-700/40 bg-slate-900">
                    {p.image_url ? (
                      <img src={p.image_url} alt={p.name} loading="lazy" className="aspect-square w-full object-cover" />
                    ) : (
                      <div className="flex aspect-square flex-col items-center justify-center gap-2 text-slate-600">
                        <ImageIcon size={32} /><span className="text-[10px]">нет фото</span>
                      </div>
                    )}
                    <div className="absolute left-1 top-1 flex gap-1">
                      {p.pushed ? (
                        <span className="rounded bg-emerald-500/90 px-1.5 py-0.5 text-[9px] font-bold text-slate-950">на сайте</span>
                      ) : (
                        <span className="rounded bg-slate-700/90 px-1.5 py-0.5 text-[9px] text-slate-300">база</span>
                      )}
                    </div>
                    <div className="p-2">
                      <div className="line-clamp-2 min-h-[2rem] text-xs" title={p.name}>{p.name}</div>
                      <div className="mt-0.5 text-[10px] text-slate-500">{p.product_id ? `#${p.product_id}` : `imp ${p.import_id}`}{p.sku ? ` · ${p.sku}` : ""}</div>
                    </div>
                    <div className="absolute inset-x-0 bottom-0 flex translate-y-full justify-center gap-1 bg-slate-950/90 p-2 transition-transform group-hover:translate-y-0">
                      <button onClick={() => { setAssignFor(p); assignInput.current?.click(); }}
                        className="inline-flex items-center gap-1 rounded bg-emerald-500 px-2 py-1 text-xs font-bold text-slate-950 hover:bg-emerald-400">
                        <Upload size={12} /> Фото
                      </button>
                      {p.image_url && (
                        <button onClick={() => copyUrl(p.image_url)} className="rounded bg-slate-800 px-2 py-1 text-xs hover:bg-slate-700"><Copy size={12} /></button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center justify-center gap-2">
                <button disabled={prodPage <= 1} onClick={() => { setProdPage(prodPage - 1); loadProducts(prodQuery, prodPage - 1); }}
                  className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm hover:bg-slate-700 disabled:opacity-40">←</button>
                <span className="text-sm text-slate-400">стр. {prodPage} / {Math.max(1, Math.ceil(prodTotal / 60))} · {prodTotal} тов.</span>
                <button disabled={prodPage * 60 >= prodTotal} onClick={() => { setProdPage(prodPage + 1); loadProducts(prodQuery, prodPage + 1); }}
                  className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm hover:bg-slate-700 disabled:opacity-40">→</button>
              </div>
            </>
          ) : (
            <div className="py-10 text-center text-sm text-slate-500">Товары не найдены</div>
          )}
        </div>
      )}

      {/* FILES MODE */}
      {mode === "files" && (
        <div onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); uploadFiles([...e.dataTransfer.files]); }}
          className="rounded-2xl border border-slate-700/30 glass p-4">
          {dirs.length > 0 && (
            <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
              {dirs.map((d) => (
                <button key={d.name} onClick={() => load(`${path}/${d.name}`)}
                  className="flex items-center gap-2 rounded-lg bg-slate-800/60 px-3 py-2 text-left text-sm hover:bg-slate-700">
                  <Folder size={16} className="shrink-0 text-amber-400" /><span className="truncate">{d.name}</span>
                </button>
              ))}
            </div>
          )}
          {files.length > 0 ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
              {files.map((f) => (
                <div key={f.name} className="group relative overflow-hidden rounded-xl border border-slate-700/40 bg-slate-900">
                  {f.is_image ? (
                    <button onClick={() => setPreview(f)} className="block aspect-square w-full">
                      <img src={f.url} alt={f.name} loading="lazy" className="h-full w-full object-cover" />
                    </button>
                  ) : (
                    <div className="flex aspect-square items-center justify-center"><FileText size={32} className="text-slate-600" /></div>
                  )}
                  <div className="p-2">
                    <div className="truncate text-xs" title={f.name}>{f.name}</div>
                    <div className="text-[10px] text-slate-500">{fmtSize(f.size)}</div>
                  </div>
                  <div className="absolute right-1 top-1 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <button onClick={() => copyUrl(f.url)} className="rounded bg-slate-950/80 p-1.5 hover:bg-slate-800" title="Копировать URL"><Copy size={13} /></button>
                    <a href={f.url} target="_blank" rel="noreferrer" className="rounded bg-slate-950/80 p-1.5 hover:bg-slate-800" title="Открыть"><ExternalLink size={13} /></a>
                    <button onClick={() => removeFile(f)} className="rounded bg-red-950/80 p-1.5 text-red-400 hover:bg-red-900" title="Удалить"><Trash2 size={13} /></button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            !loading && dirs.length === 0 && <div className="py-10 text-center text-sm text-slate-500">Папка пуста — перетащи файлы сюда или нажми «Загрузить»</div>
          )}
          {loading && <div className="py-10 text-center text-sm text-slate-500">Загрузка...</div>}
        </div>
      )}

      {/* preview modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6" onClick={() => setPreview(null)}>
          <div className="relative max-h-full max-w-4xl" onClick={(e) => e.stopPropagation()}>
            <img src={preview.url} alt={preview.name} className="max-h-[80vh] rounded-xl object-contain" />
            <div className="mt-3 flex items-center justify-between gap-3">
              <div className="truncate text-sm text-slate-300">{preview.url}</div>
              <div className="flex gap-2">
                <button onClick={() => copyUrl(preview.url)} className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm hover:bg-slate-700"><Copy size={14} className="mr-1 inline" />URL</button>
                <button onClick={() => setPreview(null)} className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm hover:bg-slate-700"><X size={14} className="inline" /></button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
