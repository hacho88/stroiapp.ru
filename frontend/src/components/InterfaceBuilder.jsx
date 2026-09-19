import React, { useMemo, useRef, useState, useEffect, useCallback } from "react";
import {
  Sparkles, Layers, Code2, Eye, Copy, Check, Trash2, Wand2,
  Loader2, AlertCircle, MousePointer2, Plus,
} from "lucide-react";
import { apiPost } from "../lib/api";
import { BUILDER_PRESETS } from "../lib/builder-presets";
import { compileToNextJS, renderToHtml } from "../lib/ui-compiler";

/** @typedef {import('../types/ui-builder').UIElement} UIElement */

function mapTree(list, id, fn) {
  return list.map((el) => {
    if (el.id === id) return fn(el);
    if (el.children) return { ...el, children: mapTree(el.children, id, fn) };
    return el;
  });
}
function findEl(list, id) {
  for (const el of list) {
    if (el.id === id) return el;
    if (el.children) { const f = findEl(el.children, id); if (f) return f; }
  }
  return null;
}
function removeEl(list, id) {
  return list.filter((el) => el.id !== id)
    .map((el) => (el.children ? { ...el, children: removeEl(el.children, id) } : el));
}
let _uid = 1000;
const newId = () => `el-${Date.now().toString(36)}-${_uid++}`;

function buildPreviewDoc(elements) {
  const html = renderToHtml(elements);
  return `<!doctype html><html><head><meta charset="utf-8"/>
<script src="https://cdn.tailwindcss.com"><\/script>
<style>
  html,body{margin:0;padding:16px;background:transparent;font-family:Inter,system-ui,sans-serif}
  [data-id]{cursor:pointer}
  [data-id]:hover{outline:1px dashed rgba(52,211,153,.55);outline-offset:2px}
  .sel{outline:2px solid #34d399 !important;outline-offset:2px}
</style></head><body>${html}
<script>
  document.addEventListener('click',function(e){
    e.preventDefault();e.stopPropagation();
    var t=e.target.closest('[data-id]');
    if(t)parent.postMessage({type:'ui-select',id:t.getAttribute('data-id')},'*');
  },true);
  window.addEventListener('message',function(e){
    if(e.data&&e.data.type==='ui-highlight'){
      document.querySelectorAll('.sel').forEach(function(x){x.classList.remove('sel')});
      var t=document.querySelector('[data-id="'+e.data.id+'"]');
      if(t){t.classList.add('sel');t.scrollIntoView({block:'nearest'})}
    }
  });
<\/script></body></html>`;
}

function TreeNode({ el, depth, selectedId, onSelect, onDelete }) {
  const [open, setOpen] = useState(true);
  const hasKids = el.children && el.children.length > 0;
  const sel = el.id === selectedId;
  return (
    <div>
      <div onClick={() => onSelect(el.id)}
        className={`group flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs cursor-pointer select-none transition-colors ${sel ? "bg-emerald-500/15 text-emerald-300" : "text-neutral-400 hover:bg-neutral-800/60 hover:text-neutral-200"}`}
        style={{ paddingLeft: `${8 + depth * 14}px` }}>
        <button onClick={(e) => { e.stopPropagation(); if (hasKids) setOpen(!open); }}
          className={`w-3 text-neutral-600 ${hasKids ? "" : "invisible"}`}>{open ? "▾" : "▸"}</button>
        <span className="text-neutral-600 font-mono text-[10px] uppercase w-14 shrink-0">{el.type}</span>
        <span className="truncate flex-1">{el.name}</span>
        <button onClick={(e) => { e.stopPropagation(); onDelete(el.id); }}
          className="opacity-0 group-hover:opacity-100 text-neutral-600 hover:text-red-400 transition"><Trash2 size={12} /></button>
      </div>
      {hasKids && open && el.children.map((c) => (
        <TreeNode key={c.id} el={c} depth={depth + 1} selectedId={selectedId} onSelect={onSelect} onDelete={onDelete} />
      ))}
    </div>
  );
}

export default function InterfaceBuilder({ addToast }) {
  const [elements, setElements] = useState(() => BUILDER_PRESETS[0].build());
  const [selectedId, setSelectedId] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [view, setView] = useState("canvas");
  const [copied, setCopied] = useState(false);
  const iframeRef = useRef(null);

  const selected = useMemo(() => (selectedId ? findEl(elements, selectedId) : null), [elements, selectedId]);
  const code = useMemo(() => compileToNextJS(elements), [elements]);
  const previewDoc = useMemo(() => buildPreviewDoc(elements), [elements]);
  const toast = useCallback((m, t) => { if (addToast) addToast(m, t); }, [addToast]);

  useEffect(() => {
    const onMsg = (e) => { if (e.data && e.data.type === "ui-select") setSelectedId(e.data.id); };
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, []);

  useEffect(() => {
    const w = iframeRef.current && iframeRef.current.contentWindow;
    if (w && selectedId) w.postMessage({ type: "ui-highlight", id: selectedId }, "*");
  }, [selectedId, previewDoc]);

  const applyPreset = (p) => { setElements(p.build()); setSelectedId(null); setError(""); toast(`Пресет «${p.title}» загружен`, "success"); };

  const generate = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true); setError("");
    try {
      const res = await apiPost("/interfaces/generate", { prompt: prompt.trim(), currentElements: elements });
      if (res && res.elements && res.elements.length) {
        setElements(res.elements); setSelectedId(null); toast("Интерфейс сгенерирован", "success");
      } else setError("DeepSeek вернул пустой результат. Попробуй переформулировать.");
    } catch (e) {
      const msg = (e && e.message) || "Ошибка генерации";
      setError(/402|balance|баланс|insufficient/i.test(msg) ? "Закончился баланс на ключе DeepSeek. Пополни счёт и повтори." : msg);
      toast("Ошибка генерации", "error");
    } finally { setLoading(false); }
  };

  const updateProp = (id, key, value) => setElements((els) => mapTree(els, id, (el) => ({ ...el, props: { ...el.props, [key]: value } })));
  const updateName = (id, value) => setElements((els) => mapTree(els, id, (el) => ({ ...el, name: value })));
  const deleteEl = (id) => { setElements((els) => removeEl(els, id)); if (selectedId === id) setSelectedId(null); };
  const addElement = (type) => {
    const base = {
      container: { className: "p-4 rounded-xl bg-neutral-100 flex flex-col gap-2" },
      text: { className: "text-sm text-neutral-800", text: "Новый текст" },
      button: { className: "px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold", text: "Кнопка" },
      image: { className: "w-full h-40 object-cover rounded-lg", src: "https://placehold.co/600x400" },
      input: { className: "rounded-lg border border-neutral-300 px-3 py-2 text-sm", placeholder: "Введите..." },
    }[type];
    const el = { id: newId(), type, name: type[0].toUpperCase() + type.slice(1), props: { ...base } };
    if (type === "container") el.children = [];
    setElements((els) => [...els, el]); setSelectedId(el.id);
  };

  const copyCode = async () => {
    try { await navigator.clipboard.writeText(code); setCopied(true); toast("Код скопирован", "success"); setTimeout(() => setCopied(false), 1600); }
    catch { toast("Не удалось скопировать", "error"); }
  };

  return (
    <div className="flex h-[calc(100vh-120px)] gap-3 text-neutral-200">
      {/* LEFT: presets + AI + layers */}
      <div className="w-72 shrink-0 flex flex-col gap-3 overflow-hidden">
        <div className="rounded-xl border border-neutral-800 bg-[#0c0c0e] p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            <Wand2 size={13} /> Пресеты
          </div>
          <div className="flex flex-col gap-1.5">
            {BUILDER_PRESETS.map((p) => (
              <button key={p.id} onClick={() => applyPreset(p)}
                className="rounded-lg border border-neutral-800 bg-neutral-900/60 px-3 py-2 text-left transition hover:border-emerald-500/40 hover:bg-neutral-800">
                <div className="text-xs font-semibold text-neutral-200">{p.title}</div>
                <div className="text-[10px] text-neutral-500">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-neutral-800 bg-[#0c0c0e] p-3">
          <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            <Sparkles size={13} /> AI-генерация
          </div>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={3}
            placeholder="Опиши интерфейс: карточка цемента с ценой, калькулятор, баннер..."
            className="input-field w-full resize-none text-xs" />
          <button onClick={generate} disabled={loading || !prompt.trim()}
            className="btn-shine mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {loading ? "DeepSeek думает..." : "Сгенерировать"}
          </button>
          {error && (
            <div className="mt-2 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-2 text-[11px] text-red-300">
              <AlertCircle size={13} className="mt-0.5 shrink-0" /> {error}
            </div>
          )}
          <div className="mt-3 flex flex-wrap gap-1">
            {["container", "text", "button", "image", "input"].map((t) => (
              <button key={t} onClick={() => addElement(t)}
                className="flex items-center gap-1 rounded-md border border-neutral-800 bg-neutral-900 px-2 py-1 text-[10px] text-neutral-400 transition hover:border-emerald-500/40 hover:text-emerald-300">
                <Plus size={10} /> {t}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto rounded-xl border border-neutral-800 bg-[#0c0c0e] p-2">
          <div className="mb-1 flex items-center gap-2 px-1 text-xs font-semibold uppercase tracking-wider text-neutral-500">
            <Layers size={13} /> Слои
          </div>
          {elements.length === 0 ? (
            <div className="p-3 text-center text-[11px] text-neutral-600">Холст пуст — добавь элемент или пресет</div>
          ) : (
            elements.map((el) => (
              <TreeNode key={el.id} el={el} depth={0} selectedId={selectedId} onSelect={setSelectedId} onDelete={deleteEl} />
            ))
          )}
        </div>
      </div>
      {/* CENTER: canvas / code */}
      <div className="flex min-w-0 flex-1 flex-col rounded-xl border border-neutral-800 bg-[#0c0c0e]">
        <div className="flex items-center justify-between border-b border-neutral-800 px-3 py-2">
          <div className="flex gap-1 rounded-lg bg-neutral-900 p-1">
            <button onClick={() => setView("canvas")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${view === "canvas" ? "bg-emerald-600 text-white" : "text-neutral-400 hover:text-neutral-200"}`}>
              <Eye size={13} /> Визуальный холст
            </button>
            <button onClick={() => setView("code")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${view === "code" ? "bg-emerald-600 text-white" : "text-neutral-400 hover:text-neutral-200"}`}>
              <Code2 size={13} /> Next.js Код
            </button>
          </div>
          {view === "code" && (
            <button onClick={copyCode}
              className="flex items-center gap-1.5 rounded-lg border border-neutral-700 bg-neutral-900 px-3 py-1.5 text-xs font-medium text-neutral-300 transition hover:border-emerald-500/50 hover:text-emerald-300">
              {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />} {copied ? "Скопировано" : "Скопировать"}
            </button>
          )}
        </div>
        <div className="relative flex-1 overflow-hidden">
          {view === "canvas" ? (
            <div className="bg-grid absolute inset-0 overflow-auto">
              {elements.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-neutral-600">
                  <MousePointer2 size={28} />
                  <div className="text-sm">Пустой холст</div>
                  <div className="text-xs">Выбери пресет или опиши интерфейс для DeepSeek</div>
                </div>
              ) : (
                <iframe ref={iframeRef} title="ui-preview" sandbox="allow-scripts"
                  srcDoc={previewDoc} className="h-full w-full border-0 bg-white" />
              )}
            </div>
          ) : (
            <pre className="h-full overflow-auto p-4 font-mono text-[11px] leading-relaxed text-emerald-100/90">
              <code>{code}</code>
            </pre>
          )}
        </div>
      </div>
      {/* RIGHT: inspector */}
      <div className="w-72 shrink-0 overflow-y-auto rounded-xl border border-neutral-800 bg-[#0c0c0e] p-3">
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-500">
          <MousePointer2 size={13} /> Инспектор
        </div>
        {!selected ? (
          <div className="rounded-lg border border-dashed border-neutral-800 p-4 text-center text-[11px] text-neutral-600">
            Кликни по элементу на холсте или в дереве слоёв
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Имя слоя</label>
              <input value={selected.name} onChange={(e) => updateName(selected.id, e.target.value)} className="input-field w-full text-xs" />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Тип</label>
              <div className="rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 font-mono text-xs text-emerald-300">{selected.type}</div>
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Tailwind классы</label>
              <textarea value={selected.props.className || ""} rows={4}
                onChange={(e) => updateProp(selected.id, "className", e.target.value)}
                className="input-field w-full resize-y font-mono text-[11px] leading-relaxed" />
            </div>
            {(selected.type === "text" || selected.type === "button") && (
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Текст</label>
                <textarea value={selected.props.text || ""} rows={2}
                  onChange={(e) => updateProp(selected.id, "text", e.target.value)} className="input-field w-full resize-y text-xs" />
              </div>
            )}
            {selected.type === "image" && (
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-neutral-500">URL изображения</label>
                <input value={selected.props.src || ""} onChange={(e) => updateProp(selected.id, "src", e.target.value)} className="input-field w-full font-mono text-[11px]" />
              </div>
            )}
            {selected.type === "input" && (
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-neutral-500">Placeholder</label>
                <input value={selected.props.placeholder || ""} onChange={(e) => updateProp(selected.id, "placeholder", e.target.value)} className="input-field w-full text-xs" />
              </div>
            )}
            <button onClick={() => deleteEl(selected.id)}
              className="mt-1 flex items-center justify-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs font-medium text-red-300 transition hover:bg-red-500/20">
              <Trash2 size={13} /> Удалить элемент
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
