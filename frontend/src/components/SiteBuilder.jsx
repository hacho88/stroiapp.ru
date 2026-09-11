import React, { useState, useEffect, useCallback, useRef } from "react";
import ImageManager from "./ImageManager";
import ForemanUploader from "./ForemanUploader";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  GripVertical,
  Trash2,
  Plus,
  Image as ImageIcon,
  Eye,
  EyeOff,
  Save,
  LayoutTemplate,
  Type,
  ShoppingCart,
  FolderOpen,
  Image,
  Video,
  SlidersHorizontal,
  MousePointerClick,
  Code,
  Wand2,
  Monitor,
  ArrowUpDown,
  Sparkles,
  Palette,
  Check,
  X,
  Copy,
  ExternalLink,
  Layers,
  FileSpreadsheet,
} from "lucide-react";

const API_URL = "http://127.0.0.1:8010/api";
const OPENCART_API_URL = "https://stroiapp.ru/index.php?route=api/ai_manager";
const OPENCART_TOKEN = "change_this_ai_manager_token";

const BLOCK_META = {
  hero:        { label: "Hero",        icon: LayoutTemplate,   color: "from-violet-500 to-purple-600", desc: "Большой баннер с заголовком" },
  text:        { label: "Текст",       icon: Type,             color: "from-sky-500 to-blue-600",    desc: "Текстовый блок с заголовком" },
  products:    { label: "Товары",      icon: ShoppingCart,     color: "from-emerald-500 to-teal-600", desc: "Сетка товаров из категории" },
  categories:  { label: "Категории",   icon: FolderOpen,       color: "from-amber-500 to-orange-600", desc: "Плитка категорий" },
  image:       { label: "Картинка",    icon: Image,            color: "from-pink-500 to-rose-600",   desc: "Изображение с подписью" },
  video:       { label: "Видео",       icon: Video,            color: "from-red-500 to-rose-600",    desc: "Видео-плеер" },
  carousel:    { label: "Карусель",    icon: SlidersHorizontal, color: "from-cyan-500 to-blue-600",   desc: "Горизонтальная карусель" },
  cta:         { label: "CTA",         icon: MousePointerClick, color: "from-orange-500 to-red-600",  desc: "Призыв к действию" },
  html:        { label: "HTML",        icon: Code,             color: "from-slate-500 to-gray-600",  desc: "Произвольный HTML код" },
};

const DEFAULT_CONTENT = {
  hero:        { title: "Заголовок баннера", subtitle: "Описание баннера", bg_image: "", button_text: "Подробнее", button_link: "" },
  text:        { title: "Заголовок", body: "Ваш текст здесь..." },
  products:    { title: "Наши товары", category_id: 0, limit: 4 },
  categories:  { title: "Категории", category_ids: [] },
  image:       { src: "", alt: "", caption: "" },
  video:       { src: "", title: "" },
  carousel:    { title: "Галерея", images: [] },
  cta:         { title: "Готовы начать?", button_text: "Связаться", button_link: "" },
  html:        { html: "<div>Свой HTML</div>" },
};

function apiGet(path) {
  return fetch(API_URL + path).then((r) => {
    if (!r.ok) throw new Error(r.statusText);
    return r.json();
  });
}
function apiPost(path, body) {
  return fetch(API_URL + path, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => { if (!r.ok) throw new Error(r.statusText); return r.json(); });
}
function apiPut(path, body) {
  return fetch(API_URL + path, {
    method: "PUT", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((r) => { if (!r.ok) throw new Error(r.statusText); return r.json(); });
}
function apiDelete(path) {
  return fetch(API_URL + path, { method: "DELETE" }).then((r) => { if (!r.ok) throw new Error(r.statusText); return r.json(); });
}

function BlockIcon({ type, size = 16 }) {
  const meta = BLOCK_META[type] || BLOCK_META.html;
  const Icon = meta.icon;
  return <Icon size={size} />;
}

/* ========================== SORTABLE BLOCK CARD ========================== */
function SortableBlockCard({ block, isSelected, onSelect, onToggle, onDelete, onDuplicate }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: block.id });
  const style = { transform: CSS.Transform.toString(transform), transition };
  const meta = BLOCK_META[block.type] || BLOCK_META.html;
  const Icon = meta.icon;

  return (
    <div
      ref={setNodeRef}
      style={style}
      onClick={() => onSelect(block.id)}
      className={`group relative mb-3 cursor-pointer select-none rounded-2xl border transition-all duration-300
        ${isDragging ? "z-50 scale-[1.02] shadow-2xl shadow-black/40 ring-2 ring-violet-500/60" : ""}
        ${isSelected ? "border-violet-500/60 bg-white/[0.07] shadow-lg shadow-violet-500/10" : "border-white/[0.06] bg-white/[0.03] hover:bg-white/[0.06] hover:border-white/[0.12]"}
        ${!block.is_active ? "opacity-40" : ""}
      `}
    >
      <div className="flex items-center gap-3 p-3.5">
        <button
          {...attributes}
          {...listeners}
          className="flex shrink-0 cursor-grab items-center justify-center rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-white/10 hover:text-slate-300 active:cursor-grabbing"
        >
          <GripVertical size={16} />
        </button>

        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${meta.color} text-white shadow-lg`}>
          <Icon size={18} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold text-slate-200 truncate">
            {block.content.title || meta.label}
          </div>
          <div className="mt-0.5 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wider text-slate-500">
            <span className="inline-flex items-center rounded bg-white/5 px-1.5 py-0.5">{meta.label}</span>
            <span>ID {block.id}</span>
          </div>
        </div>

        <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            onClick={(e) => { e.stopPropagation(); onToggle(block); }}
            className={`rounded-lg p-1.5 transition-colors ${block.is_active ? "text-emerald-400 hover:bg-emerald-500/10" : "text-slate-600 hover:bg-white/5 hover:text-slate-300"}`}
            title={block.is_active ? "Скрыть" : "Показать"}
          >
            {block.is_active ? <Eye size={14} /> : <EyeOff size={14} />}
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDuplicate(block); }}
            className="rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-white/5 hover:text-slate-300"
            title="Дублировать"
          >
            <Copy size={14} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(block.id); }}
            className="rounded-lg p-1.5 text-slate-500 transition-colors hover:bg-red-500/10 hover:text-red-400"
            title="Удалить"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ========================== DRAG OVERLAY ITEM ========================== */
function DragOverlayItem({ block }) {
  const meta = BLOCK_META[block.type] || BLOCK_META.html;
  const Icon = meta.icon;
  return (
    <div className="w-[380px] rounded-2xl border border-violet-500/50 bg-slate-900/95 p-4 shadow-2xl shadow-violet-500/20 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br ${meta.color} text-white`}><Icon size={18} /></div>
        <div className="text-sm font-semibold text-slate-200">{block.content.title || meta.label}</div>
      </div>
    </div>
  );
}

/* ========================== PROPERTY EDITOR ========================== */
function PropertyEditor({ block, content, onChange, onSave, onCancel }) {
  const update = (k, v) => onChange({ ...content, [k]: v });
  const meta = BLOCK_META[block.type] || BLOCK_META.html;

  return (
    <div className="animate-in slide-in-from-right-4 fade-in duration-300 border-t border-white/[0.06] bg-white/[0.02] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br ${meta.color} text-white`}><meta.icon size={14} /></div>
          <span className="text-sm font-semibold text-slate-200">Редактор: {meta.label}</span>
        </div>
        <div className="flex gap-2">
          <button onClick={onCancel} className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-400 transition-colors hover:bg-white/5 hover:text-slate-200"><X size={13} className="inline mr-1" />Отмена</button>
          <button onClick={onSave} className="rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-1.5 text-xs font-bold text-white shadow-lg shadow-emerald-500/20 transition-all hover:shadow-emerald-500/40 hover:scale-105"><Check size={13} className="inline mr-1" />Сохранить</button>
        </div>
      </div>

      <div className="space-y-4">
        {block.type === "hero" && (
          <>
            <Field label="Заголовок"><input value={content.title || ""} onChange={(e) => update("title", e.target.value)} className="input-field" placeholder="Главный заголовок" /></Field>
            <Field label="Подзаголовок"><input value={content.subtitle || ""} onChange={(e) => update("subtitle", e.target.value)} className="input-field" placeholder="Описание" /></Field>
            <Field label="Фоновая картинка (URL)"><input value={content.bg_image || ""} onChange={(e) => update("bg_image", e.target.value)} className="input-field" placeholder="https://..." /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Текст кнопки"><input value={content.button_text || ""} onChange={(e) => update("button_text", e.target.value)} className="input-field" placeholder="Купить" /></Field>
              <Field label="Ссылка кнопки"><input value={content.button_link || ""} onChange={(e) => update("button_link", e.target.value)} className="input-field" placeholder="/product/..." /></Field>
            </div>
          </>
        )}
        {block.type === "text" && (
          <>
            <Field label="Заголовок"><input value={content.title || ""} onChange={(e) => update("title", e.target.value)} className="input-field" /></Field>
            <Field label="Текст"><textarea value={content.body || ""} onChange={(e) => update("body", e.target.value)} rows={6} className="input-field" /></Field>
          </>
        )}
        {block.type === "image" && (
          <>
            <Field label="URL картинки"><input value={content.src || ""} onChange={(e) => update("src", e.target.value)} className="input-field" placeholder="https://..." /></Field>
            <Field label="Alt текст"><input value={content.alt || ""} onChange={(e) => update("alt", e.target.value)} className="input-field" /></Field>
            <Field label="Подпись"><input value={content.caption || ""} onChange={(e) => update("caption", e.target.value)} className="input-field" /></Field>
            {content.src && <img src={content.src} alt={content.alt} className="mt-2 max-h-40 rounded-xl border border-white/10 object-cover" />}
          </>
        )}
        {block.type === "cta" && (
          <>
            <Field label="Заголовок"><input value={content.title || ""} onChange={(e) => update("title", e.target.value)} className="input-field" /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Текст кнопки"><input value={content.button_text || ""} onChange={(e) => update("button_text", e.target.value)} className="input-field" /></Field>
              <Field label="Ссылка"><input value={content.button_link || ""} onChange={(e) => update("button_link", e.target.value)} className="input-field" /></Field>
            </div>
          </>
        )}
        {block.type === "products" && (
          <>
            <Field label="Заголовок"><input value={content.title || ""} onChange={(e) => update("title", e.target.value)} className="input-field" /></Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="ID категории"><input type="number" value={content.category_id || 0} onChange={(e) => update("category_id", Number(e.target.value))} className="input-field" /></Field>
              <Field label="Кол-во"><input type="number" value={content.limit || 4} onChange={(e) => update("limit", Number(e.target.value))} className="input-field" /></Field>
            </div>
          </>
        )}
        {block.type === "carousel" && (
          <>
            <Field label="Заголовок"><input value={content.title || ""} onChange={(e) => update("title", e.target.value)} className="input-field" /></Field>
            <Field label="Изображения (URL через запятую)">
              <textarea
                value={(content.images || []).join(", ")}
                onChange={(e) => update("images", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))}
                rows={3}
                className="input-field"
                placeholder="https://a.jpg, https://b.jpg"
              />
            </Field>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {(content.images || []).map((src, i) => <img key={i} src={src} alt="" className="h-20 rounded-lg border border-white/10 object-cover" />)}
            </div>
          </>
        )}
        {block.type === "video" && (
          <>
            <Field label="Заголовок"><input value={content.title || ""} onChange={(e) => update("title", e.target.value)} className="input-field" /></Field>
            <Field label="URL видео"><input value={content.src || ""} onChange={(e) => update("src", e.target.value)} className="input-field" placeholder="https://...mp4" /></Field>
            {content.src && <video src={content.src} controls className="mt-2 max-h-48 w-full rounded-xl" />}
          </>
        )}
        {block.type === "categories" && (
          <>
            <Field label="Заголовок"><input value={content.title || ""} onChange={(e) => update("title", e.target.value)} className="input-field" /></Field>
            <Field label="ID категорий (через запятую)">
              <input
                value={(content.category_ids || []).join(", ")}
                onChange={(e) => update("category_ids", e.target.value.split(",").map((s) => Number(s.trim())).filter(Boolean))}
                className="input-field"
              />
            </Field>
          </>
        )}
        {block.type === "html" && (
          <Field label="HTML код"><textarea value={content.html || ""} onChange={(e) => update("html", e.target.value)} rows={10} className="input-field font-mono text-xs" /></Field>
        )}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div className="mb-1.5 text-[11px] font-semibold uppercase tracking-widest text-slate-500">{label}</div>
      {children}
    </div>
  );
}

/* ========================== PREVIEW CANVAS ========================== */
function PreviewCanvas({ blocks, page }) {
  const activeBlocks = blocks.filter((b) => b.is_active);
  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Monitor size={14} />
          <span>Предпросмотр страницы: <b className="text-slate-200">{page}</b></span>
        </div>
        <a href={`http://stroiapp.ru/index.php?route=common/home`} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 text-xs font-medium text-sky-400 hover:text-sky-300 transition-colors">
          <ExternalLink size={12} /> Открыть stroiapp.ru
        </a>
      </div>
      <div className="space-y-6 rounded-3xl border border-white/[0.06] bg-white/[0.02] p-8 shadow-2xl">
        {activeBlocks.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Layers size={48} className="mb-4 opacity-20" />
            <p className="text-lg font-medium">Нет активных блоков</p>
            <p className="text-sm mt-1">Добавьте блоки в редакторе, чтобы увидеть предпросмотр</p>
          </div>
        )}
        {activeBlocks.map((block) => (
          <PreviewBlock key={block.id} block={block} />
        ))}
      </div>
    </div>
  );
}

function PreviewBlock({ block }) {
  switch (block.type) {
    case "hero":
      return (
        <div className="relative flex min-h-[360px] items-center justify-center overflow-hidden rounded-2xl" style={{ background: "linear-gradient(135deg,#1a1a2e 0%,#16213e 100%)" }}>
          {block.content.bg_image && <img src={block.content.bg_image} alt="" className="absolute inset-0 h-full w-full object-cover opacity-30" />}
          <div className="relative z-10 px-8 py-12 text-center">
            <h2 className="mb-3 text-4xl font-bold text-white">{block.content.title || "Заголовок"}</h2>
            <p className="mb-8 text-lg text-slate-300">{block.content.subtitle || "Подзаголовок"}</p>
            {block.content.button_text && <button className="rounded-xl bg-[#ff6b00] px-8 py-3 text-sm font-bold text-white shadow-lg shadow-orange-500/30 transition-transform hover:scale-105">{block.content.button_text}</button>}
          </div>
        </div>
      );
    case "text":
      return (
        <div className="rounded-2xl bg-white p-8 shadow-sm">
          {block.content.title && <h3 className="mb-4 text-2xl font-bold text-slate-900">{block.content.title}</h3>}
          <p className="whitespace-pre-wrap text-base leading-relaxed text-slate-600">{block.content.body || "Текст..."}</p>
        </div>
      );
    case "image":
      return (
        <div className="overflow-hidden rounded-2xl bg-white shadow-sm">
          {block.content.src ? <img src={block.content.src} alt={block.content.alt || ""} className="h-auto w-full" /> : <div className="flex h-64 items-center justify-center bg-slate-100 text-slate-400">Нет изображения</div>}
          {block.content.caption && <p className="px-6 py-4 text-sm text-slate-500">{block.content.caption}</p>}
        </div>
      );
    case "cta":
      return (
        <div className="rounded-2xl bg-gradient-to-r from-[#ff6b00] to-[#ff8c00] p-10 text-center shadow-lg shadow-orange-500/20">
          <h3 className="mb-6 text-2xl font-bold text-white">{block.content.title || "Призыв к действию"}</h3>
          {block.content.button_text && <a href={block.content.button_link || "#"} className="inline-block rounded-xl bg-white px-8 py-3 text-sm font-bold text-[#ff6b00] shadow-md transition-transform hover:scale-105">{block.content.button_text}</a>}
        </div>
      );
    case "products":
      return (
        <div className="rounded-2xl bg-white p-8 shadow-sm">
          {block.content.title && <h3 className="mb-6 text-2xl font-bold text-slate-900">{block.content.title}</h3>}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {Array.from({ length: block.content.limit || 4 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-slate-100 p-4 text-center transition-shadow hover:shadow-md">
                <div className="mb-3 aspect-square rounded-lg bg-slate-100" />
                <div className="text-sm font-medium text-slate-700">Товар {i + 1}</div>
                <div className="mt-1 text-xs text-slate-400">от {1000 + i * 500} ₽</div>
              </div>
            ))}
          </div>
        </div>
      );
    case "carousel":
      return (
        <div className="rounded-2xl bg-white p-8 shadow-sm">
          {block.content.title && <h3 className="mb-6 text-2xl font-bold text-slate-900">{block.content.title}</h3>}
          <div className="flex gap-4 overflow-x-auto pb-2">
            {(block.content.images || []).map((img, i) => <img key={i} src={img} alt="" className="h-48 shrink-0 rounded-xl object-cover" />)}
            {(block.content.images || []).length === 0 && <div className="flex h-48 w-full items-center justify-center rounded-xl bg-slate-50 text-slate-400">Нет изображений</div>}
          </div>
        </div>
      );
    case "video":
      return (
        <div className="rounded-2xl bg-white p-8 shadow-sm">
          {block.content.title && <h3 className="mb-4 text-2xl font-bold text-slate-900">{block.content.title}</h3>}
          {block.content.src ? <video src={block.content.src} controls className="w-full rounded-xl" /> : <div className="flex aspect-video items-center justify-center rounded-xl bg-slate-50 text-slate-400">Нет видео</div>}
        </div>
      );
    case "categories":
      return (
        <div className="rounded-2xl bg-white p-8 shadow-sm">
          {block.content.title && <h3 className="mb-6 text-2xl font-bold text-slate-900">{block.content.title}</h3>}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {(block.content.category_ids || []).map((id, i) => (
              <div key={i} className="rounded-xl bg-slate-50 p-6 text-center transition-colors hover:bg-slate-100">
                <div className="text-sm font-semibold text-slate-700">Категория {id}</div>
              </div>
            ))}
            {(block.content.category_ids || []).length === 0 && <div className="col-span-full py-8 text-center text-slate-400">Нет категорий</div>}
          </div>
        </div>
      );
    case "html":
      return <div className="rounded-2xl bg-white p-8 shadow-sm" dangerouslySetInnerHTML={{ __html: block.content.html || "" }} />;
    default:
      return <div className="rounded-2xl bg-slate-50 p-8 text-slate-400">Блок «{block.type}»</div>;
  }
}

/* ========================== MAIN COMPONENT ========================== */
export default function SiteBuilder({ addToast }) {
  const [page, setPage] = useState("home");
  const [blocks, setBlocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [editContent, setEditContent] = useState({});
  const [previewMode, setPreviewMode] = useState(false);
  const [savingOrder, setSavingOrder] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [activeDragId, setActiveDragId] = useState(null);
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiGenerating, setAiGenerating] = useState(false);

  /* OpenCart Theme Mode */
  const [mode, setMode] = useState("builder"); // 'builder' | 'theme' | 'media' | 'foreman'
  const [themeSections, setThemeSections] = useState([
    { key: "hero", label: "Hero + AI Калькулятор", icon: "🎨", enabled: true, color: "from-violet-500 to-purple-600" },
    { key: "features", label: "Преимущества", icon: "🏆", enabled: true, color: "from-sky-500 to-blue-600" },
    { key: "categories", label: "Категории", icon: "📁", enabled: true, color: "from-amber-500 to-orange-600" },
    { key: "products", label: "Хиты продаж", icon: "📦", enabled: true, color: "from-emerald-500 to-teal-600" },
    { key: "promotions", label: "Акции", icon: "💰", enabled: false, color: "from-pink-500 to-rose-600" },
    { key: "blog", label: "Блог", icon: "📖", enabled: false, color: "from-cyan-500 to-blue-600" },
    { key: "manufacturers", label: "Бренды", icon: "🏭", enabled: false, color: "from-slate-500 to-gray-600" },
  ]);
  const [themePrompt, setThemePrompt] = useState("");
  const [themeGenerating, setThemeGenerating] = useState(false);
  const [generatedTwig, setGeneratedTwig] = useState("");
  const [generatedCss, setGeneratedCss] = useState("");
  const [exporting, setExporting] = useState(false);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  const loadBlocks = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiGet(`/site-builder/blocks?page=${page}`);
      setBlocks(data.blocks || []);
    } catch (err) {
      addToast("Ошибка загрузки: " + err.message, "error");
    } finally {
      setLoading(false);
    }
  }, [page, addToast]);

  useEffect(() => { loadBlocks(); }, [loadBlocks]);

  useEffect(() => {
    const sel = blocks.find((b) => b.id === selectedId);
    if (sel) setEditContent({ ...sel.content });
  }, [selectedId, blocks]);

  function handleDragStart(event) {
    setActiveDragId(event.active.id);
  }

  async function handleDragEnd(event) {
    setActiveDragId(null);
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = blocks.findIndex((b) => b.id === active.id);
    const newIndex = blocks.findIndex((b) => b.id === over.id);
    const newBlocks = arrayMove(blocks, oldIndex, newIndex);
    setBlocks(newBlocks);
    setSavingOrder(true);
    try {
      await apiPost("/site-builder/reorder", { page, ordered_ids: newBlocks.map((b) => b.id) });
      addToast("Порядок сохранён", "success");
    } catch (err) {
      addToast("Ошибка сохранения порядка", "error");
    } finally {
      setSavingOrder(false);
    }
  }

  async function addBlock(type) {
    try {
      const content = DEFAULT_CONTENT[type] || {};
      await apiPost("/site-builder/blocks", { page, type, content, sort_order: blocks.length });
      addToast("Блок добавлен", "success");
      await loadBlocks();
    } catch (err) {
      addToast("Ошибка добавления", "error");
    }
  }

  async function deleteBlock(id) {
    if (!confirm("Удалить блок?")) return;
    try {
      await apiDelete(`/site-builder/blocks/${id}`);
      if (selectedId === id) setSelectedId(null);
      addToast("Блок удалён", "success");
      await loadBlocks();
    } catch (err) {
      addToast("Ошибка удаления", "error");
    }
  }

  async function duplicateBlock(block) {
    try {
      await apiPost("/site-builder/blocks", {
        page, type: block.type, content: { ...block.content },
        sort_order: blocks.findIndex((b) => b.id === block.id) + 1,
      });
      addToast("Блок дублирован", "success");
      await loadBlocks();
    } catch (err) {
      addToast("Ошибка дублирования", "error");
    }
  }

  async function toggleBlock(block) {
    try {
      await apiPut(`/site-builder/blocks/${block.id}`, { is_active: !block.is_active });
      addToast(block.is_active ? "Блок скрыт" : "Блок показан", "success");
      await loadBlocks();
    } catch (err) {
      addToast("Ошибка", "error");
    }
  }

  async function saveEdit(block) {
    try {
      await apiPut(`/site-builder/blocks/${block.id}`, { content: editContent });
      addToast("Блок обновлён", "success");
      await loadBlocks();
    } catch (err) {
      addToast("Ошибка сохранения", "error");
    }
  }

  async function generateFromPrompt() {
    if (!aiPrompt.trim()) return;
    setAiGenerating(true);
    const p = aiPrompt.toLowerCase();
    const toCreate = [];
    if (p.includes("hero") || p.includes("баннер") || p.includes("главн") || p.includes("слайдер") || p.includes("калькулятор")) {
      toCreate.push({ type: "hero", content: { title: "Качественные стройматериалы", subtitle: "Доставка по Москве и МО", button_text: "Каталог", button_link: "/" } });
    }
    if (p.includes("преимуществ") || p.includes("features") || p.includes("плюсы") || p.includes("доставк") || p.includes("гарант")) {
      toCreate.push({ type: "text", content: { title: "Почему выбирают нас", body: "Быстрая доставка по всей России. Гарантия качества на все товары. Выгодные цены и акции." } });
    }
    if (p.includes("товар") || p.includes("продукт") || p.includes("хит") || p.includes("bestseller")) {
      toCreate.push({ type: "products", content: { title: "Популярные товары", category_id: 0, limit: 4 } });
    }
    if (p.includes("категор") || p.includes("categories")) {
      toCreate.push({ type: "categories", content: { title: "Категории товаров", category_ids: [] } });
    }
    if (p.includes("cta") || p.includes("заказ") || p.includes("связ") || p.includes("консульт")) {
      toCreate.push({ type: "cta", content: { title: "Нужна консультация?", button_text: "Связаться", button_link: "/contact" } });
    }
    if (p.includes("карусел") || p.includes("carousel")) {
      toCreate.push({ type: "carousel", content: { title: "Галерея", images: [] } });
    }
    if (p.includes("видео") || p.includes("video")) {
      toCreate.push({ type: "video", content: { src: "", title: "Видео-обзор" } });
    }
    if (p.includes("картинк") || p.includes("image") || p.includes("фото")) {
      toCreate.push({ type: "image", content: { src: "", alt: "", caption: "" } });
    }
    if (toCreate.length === 0) {
      toCreate.push({ type: "hero", content: DEFAULT_CONTENT.hero });
      toCreate.push({ type: "products", content: DEFAULT_CONTENT.products });
    }
    try {
      for (const b of toCreate) {
        await apiPost("/site-builder/blocks", { page, type: b.type, content: b.content, sort_order: blocks.length });
      }
      addToast(`Создано ${toCreate.length} блоков!`, "success");
      setAiPrompt("");
      await loadBlocks();
    } catch (err) {
      addToast("Ошибка генерации: " + err.message, "error");
    }
    setAiGenerating(false);
  }

  async function aiGenerate(block) {
    setAiLoading(true);
    try {
      const res = await apiPost("/ai/deepseek/generate-article", {
        topic: `Напиши короткий текст для блока типа "${block.type}" на строительную тематику. Не более 200 слов.`,
      });
      const text = res.article || res.text || "";
      if (block.type === "text") {
        setEditContent((prev) => ({ ...prev, body: text }));
      } else if (block.type === "hero") {
        setEditContent((prev) => ({ ...prev, title: text.split("\n")[0] || text, subtitle: text.split("\n").slice(1).join(" ") }));
      } else {
        setEditContent((prev) => ({ ...prev, title: text.split("\n")[0] || text }));
      }
      addToast("AI сгенерировал контент", "success");
    } catch (err) {
      addToast("Ошибка AI: " + err.message, "error");
    } finally {
      setAiLoading(false);
    }
  }

  /* ========================== OPENCART THEME GENERATOR ========================== */
  function opencartApiPost(action, body) {
    return fetch(`${OPENCART_API_URL}&action=${action}&token=${OPENCART_TOKEN}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }).then((r) => r.json());
  }

  function generateThemeTwig(sections) {
    let twig = `{{ header }}\n<link rel="stylesheet" href="catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css">\n<div id="content" class="home-page">\n`;
    sections.forEach((s) => {
      switch (s.key) {
        case "hero":
          twig += `<div class="sa-hero-wrap">\n  <div class="container">\n    <div class="row">\n      <div class="col-lg-4 col-md-5 col-sm-12">\n        <div class="sa-calc-card">\n          <div class="sa-calc-header">\n            <h3><span>&#x2728;</span> AI Калькулятор</h3>\n            <span class="sa-badge">AI</span>\n          </div>\n          <p class="sa-calc-desc">Рассчитайте количество материалов для вашего проекта</p>\n          <div class="sa-calc-fields">\n            <div class="sa-field"><div class="sa-field-icon">&#x1F527;</div><div class="sa-field-body"><label>Тип работ</label><select><option>Стены</option><option>Пол</option><option>Потолок</option></select></div></div>\n            <div class="sa-field"><div class="sa-field-icon">&#x1F4CB;</div><div class="sa-field-body"><label>Материал</label><select><option>Гипсокартон KNAUF</option><option>Штукатурка</option><option>Шпаклёвка</option></select></div></div>\n            <div class="sa-field"><div class="sa-field-icon">&#x1F4D0;</div><div class="sa-field-body"><label>Площадь поверхности, м&#xB2;</label><input type="number" value="50"></div></div>\n            <div class="sa-field"><div class="sa-field-icon">&#x1F4CF;</div><div class="sa-field-body"><label>Высота стен, м</label><input type="number" value="2.7"></div></div>\n            <div class="sa-field"><div class="sa-field-icon">&#x1F3E0;</div><div class="sa-field-body"><label>Тип помещения</label><select><option>Жилое помещение</option><option>Ванная</option><option>Кухня</option></select></div></div>\n          </div>\n          <button type="button" class="sa-btn-calc">Рассчитать материалы <span>&#x2728;</span></button>\n          <p class="sa-calc-footer">&#x2705; Точность расчёта на основе AI</p>\n        </div>\n      </div>\n      <div class="col-lg-8 col-md-7 col-sm-12">\n        <div class="sa-slider-card">\n          <div class="sa-slider-img"><img src="https://stroiapp.ru/image/cache/catalog/1-1-1-6_1_64c0f53d3d421_thumb_2264c0f53d3e1a7-800x400.jpg" alt="KNAUF"></div>\n          <div class="sa-slider-overlay"></div>\n          <div class="sa-slider-content">\n            <div class="sa-slider-logo">KNAUF</div>\n            <h3>Немецкое качество<br>для вашего строительства</h3>\n            <div class="sa-slider-props">\n              <span><i>&#x2699;&#xFE0F;</i> Проверенные<br>технологии</span>\n              <span><i>&#x1F33F;</i> Экологичные<br>материалы</span>\n              <span><i>&#x1F6E1;&#xFE0F;</i> Надёжность<br>на годы</span>\n            </div>\n            <a href="index.php?route=product/category&amp;path=59" class="sa-btn-slider">Смотреть продукцию KNAUF</a>\n          </div>\n          <div class="sa-slider-nav">\n            <div class="sa-slider-dots"><span class="active"></span><span></span><span></span></div>\n            <div class="sa-slider-arrows"><button>&lsaquo;</button><button>&rsaquo;</button></div>\n          </div>\n        </div>\n      </div>\n    </div>\n  </div>\n</div>\n`;
          break;
        case "features":
          twig += `<div class="sa-features-bar">\n  <div class="container">\n    <div class="sa-features-inner">\n      <div class="sa-feat"><div class="sa-feat-icon" style="background:#FFF0E6;">&#x1F69A;</div><div class="sa-feat-text"><h4>Быстрая доставка</h4><p>по всей России</p></div></div>\n      <div class="sa-feat"><div class="sa-feat-icon" style="background:#FFF8E6;">&#x1F3C5;</div><div class="sa-feat-text"><h4>Гарантия качества</h4><p>на все товары</p></div></div>\n      <div class="sa-feat"><div class="sa-feat-icon" style="background:#E6F7FF;">&#x1F3F7;&#xFE0F;</div><div class="sa-feat-text"><h4>Выгодные цены</h4><p>и акции</p></div></div>\n      <div class="sa-feat"><div class="sa-feat-icon" style="background:#E6FFF0;">&#x1F504;</div><div class="sa-feat-text"><h4>Возврат товара</h4><p>в течение 14 дней</p></div></div>\n      <div class="sa-feat"><div class="sa-feat-icon" style="background:#F0E6FF;">&#x1F3A7;</div><div class="sa-feat-text"><h4>Поддержка 24/7</h4><p>мы всегда на связи</p></div></div>\n    </div>\n  </div>\n</div>\n`;
          break;
        case "categories":
          twig += `<div class="sa-categories">\n  <div class="container">\n    <div class="sa-cat-header">\n      <h2>Популярные категории</h2>\n      <a href="index.php?route=product/category">Смотреть все категории &#x2192;</a>\n    </div>\n    <div class="sa-cat-grid">\n      {% for category in home_categories %}\n      <a href="{{ category.href }}" class="sa-cat-card">\n        <div class="sa-cat-info">\n          <h3>{{ category.name }}</h3>\n          <span>Перейти в категорию</span>\n        </div>\n        <div class="sa-cat-img">\n          <img src="{{ category.image }}" alt="{{ category.name }}">\n        </div>\n      </a>\n      {% endfor %}\n    </div>\n  </div>\n</div>\n`;
          break;
        case "products":
          twig += `<div class="sa-section">\n  <div class="container">\n    <h2 class="sa-section-title">Хиты продаж</h2>\n    <p>Сетка товаров</p>\n  </div>\n</div>\n`;
          break;
        case "promotions":
          twig += `<div class="sa-section">\n  <div class="container">\n    <h2 class="sa-section-title">Акции</h2>\n    <p>Специальные предложения</p>\n  </div>\n</div>\n`;
          break;
        case "blog":
          twig += `<div class="sa-section">\n  <div class="container">\n    <h2 class="sa-section-title">Блог</h2>\n    <p>Последние статьи</p>\n  </div>\n</div>\n`;
          break;
        case "manufacturers":
          twig += `<div class="sa-section">\n  <div class="container">\n    <h2 class="sa-section-title">Бренды</h2>\n    <p>Логотипы производителей</p>\n  </div>\n</div>\n`;
          break;
      }
    });
    twig += `</div>\n{{ footer }}`;
    return twig;
  }

  function generateThemeCss(sections) {
    let css = `.home-page { --sa-orange: #FF4F00; --sa-dark: #1A1A2E; --sa-gray: #F3F4F6; }\n`;
    css += `.sa-hero-wrap { background: var(--sa-gray); padding: 20px 0; width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%); }\n`;
    css += `.sa-calc-card { background: #fff; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }\n`;
    css += `.sa-calc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }\n`;
    css += `.sa-calc-header h3 { font-size: 16px; font-weight: 700; color: #1A1A2E; margin: 0; }\n`;
    css += `.sa-calc-header h3 span { margin-right: 6px; }\n`;
    css += `.sa-badge { background: var(--sa-orange); color: #fff; font-size: 10px; font-weight: 700; padding: 3px 8px; border-radius: 8px; }\n`;
    css += `.sa-calc-desc { font-size: 13px; color: #666; margin-bottom: 16px; }\n`;
    css += `.sa-calc-fields { display: flex; flex-direction: column; gap: 10px; }\n`;
    css += `.sa-field { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: 12px; background: #F9FAFB; border: 1px solid #eee; }\n`;
    css += `.sa-field-icon { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 16px; }\n`;
    css += `.sa-field-body { flex: 1; }\n`;
    css += `.sa-field-body label { display: block; font-size: 11px; color: #999; margin-bottom: 2px; }\n`;
    css += `.sa-field-body select, .sa-field-body input { width: 100%; border: none; background: transparent; font-size: 14px; color: #1A1A2E; outline: none; }\n`;
    css += `.sa-btn-calc { width: 100%; background: var(--sa-orange); color: #fff; border: none; border-radius: 12px; padding: 14px; font-size: 14px; font-weight: 700; margin-top: 12px; cursor: pointer; }\n`;
    css += `.sa-calc-footer { font-size: 11px; color: #4CAF50; text-align: center; margin-top: 8px; }\n`;
    css += `.sa-slider-card { position: relative; border-radius: 16px; overflow: hidden; min-height: 460px; background: #ddd; }\n`;
    css += `.sa-slider-img { position: absolute; inset: 0; }\n`;
    css += `.sa-slider-img img { width: 100%; height: 100%; object-fit: cover; }\n`;
    css += `.sa-slider-overlay { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.2) 50%, rgba(0,0,0,0) 100%); }\n`;
    css += `.sa-slider-content { position: absolute; left: 40px; top: 50%; transform: translateY(-50%); color: #fff; max-width: 400px; }\n`;
    css += `.sa-slider-logo { font-size: 48px; font-weight: 900; font-style: italic; color: #00A0E3; margin-bottom: 12px; text-shadow: 2px 2px 8px rgba(0,0,0,0.3); }\n`;
    css += `.sa-slider-content h3 { font-size: 26px; font-weight: 700; line-height: 1.3; margin-bottom: 20px; }\n`;
    css += `.sa-slider-props { display: flex; gap: 16px; margin-bottom: 24px; }\n`;
    css += `.sa-slider-props span { display: flex; align-items: center; gap: 6px; font-size: 12px; }\n`;
    css += `.sa-slider-props span i { font-style: normal; }\n`;
    css += `.sa-btn-slider { display: inline-block; background: var(--sa-orange); color: #fff; padding: 12px 24px; border-radius: 10px; font-size: 14px; font-weight: 600; text-decoration: none; }\n`;
    css += `.sa-slider-nav { position: absolute; bottom: 24px; right: 24px; display: flex; align-items: center; gap: 12px; }\n`;
    css += `.sa-slider-dots { display: flex; gap: 6px; }\n`;
    css += `.sa-slider-dots span { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.4); }\n`;
    css += `.sa-slider-dots span.active { background: var(--sa-orange); }\n`;
    css += `.sa-slider-arrows { display: flex; gap: 6px; }\n`;
    css += `.sa-slider-arrows button { width: 32px; height: 32px; border-radius: 50%; background: rgba(255,255,255,0.2); border: none; color: #fff; cursor: pointer; font-size: 16px; }\n`;
    css += `.sa-features-bar { background: #fff; padding: 20px 0; border-top: 1px solid #e5e5e5; border-bottom: 1px solid #e5e5e5; width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%); }\n`;
    css += `.sa-features-inner { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }\n`;
    css += `.sa-feat { display: flex; align-items: center; gap: 12px; }\n`;
    css += `.sa-feat-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }\n`;
    css += `.sa-feat-text h4 { font-size: 13px; font-weight: 700; color: #1A1A2E; margin: 0; }\n`;
    css += `.sa-feat-text p { font-size: 11px; color: #888; margin: 0; }\n`;
    css += `.sa-categories { background: var(--sa-gray); padding: 50px 0; width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%); }\n`;
    css += `.sa-cat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }\n`;
    css += `.sa-cat-header h2 { font-size: 22px; font-weight: 700; color: #1A1A2E; margin: 0; }\n`;
    css += `.sa-cat-header a { font-size: 13px; color: var(--sa-orange); text-decoration: none; }\n`;
    css += `.sa-cat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }\n`;
    css += `.sa-cat-card { display: flex; justify-content: space-between; align-items: center; background: #fff; border-radius: 16px; padding: 20px; text-decoration: none; box-shadow: 0 2px 12px rgba(0,0,0,0.04); transition: transform 0.2s, box-shadow 0.2s; }\n`;
    css += `.sa-cat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }\n`;
    css += `.sa-cat-info h3 { font-size: 14px; font-weight: 700; color: #1A1A2E; margin: 0 0 4px; }\n`;
    css += `.sa-cat-info span { font-size: 11px; color: #888; }\n`;
    css += `.sa-cat-img { width: 60px; height: 60px; }\n`;
    css += `.sa-cat-img img { width: 100%; height: 100%; object-fit: contain; }\n`;
    css += `.sa-section { padding: 50px 0; width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%); }\n`;
    css += `.sa-section-title { font-size: 24px; font-weight: 700; margin-bottom: 24px; color: #1A1A2E; }\n`;
    return css;
  }

  async function generateThemeFromPrompt() {
    if (!themePrompt.trim()) return;
    setThemeGenerating(true);
    const p = themePrompt.toLowerCase();
    const updated = themeSections.map((s) => ({ ...s, enabled: false }));
    if (p.includes("hero") || p.includes("баннер") || p.includes("главн") || p.includes("слайдер") || p.includes("калькулятор")) {
      const idx = updated.findIndex((x) => x.key === "hero"); if (idx >= 0) updated[idx].enabled = true;
    }
    if (p.includes("преимуществ") || p.includes("features") || p.includes("плюсы") || p.includes("доставк") || p.includes("гарант")) {
      const idx = updated.findIndex((x) => x.key === "features"); if (idx >= 0) updated[idx].enabled = true;
    }
    if (p.includes("категор") || p.includes("categories")) {
      const idx = updated.findIndex((x) => x.key === "categories"); if (idx >= 0) updated[idx].enabled = true;
    }
    if (p.includes("товар") || p.includes("продукт") || p.includes("хит") || p.includes("bestseller")) {
      const idx = updated.findIndex((x) => x.key === "products"); if (idx >= 0) updated[idx].enabled = true;
    }
    if (p.includes("акци") || p.includes("скидк") || p.includes("promotions")) {
      const idx = updated.findIndex((x) => x.key === "promotions"); if (idx >= 0) updated[idx].enabled = true;
    }
    if (p.includes("блог") || p.includes("стат") || p.includes("blog") || p.includes("новост")) {
      const idx = updated.findIndex((x) => x.key === "blog"); if (idx >= 0) updated[idx].enabled = true;
    }
    if (p.includes("производител") || p.includes("бренд") || p.includes("manufacturer")) {
      const idx = updated.findIndex((x) => x.key === "manufacturers"); if (idx >= 0) updated[idx].enabled = true;
    }
    // Если ничего не распознано — включаем hero + categories
    if (!updated.some((s) => s.enabled)) {
      updated[0].enabled = true;
      updated[2].enabled = true;
    }
    setThemeSections(updated);
    const active = updated.filter((s) => s.enabled);
    setGeneratedTwig(generateThemeTwig(active));
    setGeneratedCss(generateThemeCss(active));
    setThemeGenerating(false);
    addToast(`Сгенерировано ${active.length} секций`, "success");
  }

  async function exportToStroiapp() {
    if (!generatedTwig || !generatedCss) return;
    setExporting(true);
    try {
      await apiPost("/opencart/files/write", { path: "catalog/view/theme/unishop2/template/common/home.twig", content: generatedTwig });
      await apiPost("/opencart/files/write", { path: "catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css", content: generatedCss });
      await apiPost("/opencart/site/clearCache", {});
      addToast("Экспортировано на stroiapp.ru! Обновите сайт.", "success");
    } catch (err) {
      addToast("Ошибка экспорта: " + err.message, "error");
    }
    setExporting(false);
  }

  const selectedBlock = blocks.find((b) => b.id === selectedId);

  return (
    <div className="flex h-[calc(100vh-80px)] flex-col overflow-hidden">
      {/* Header */}
      <div className="flex shrink-0 items-center justify-between border-b border-white/[0.06] bg-slate-950/80 px-6 py-3 backdrop-blur-xl">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-600 text-white shadow-lg shadow-violet-500/20">
              <Layers size={16} />
            </div>
            <span className="text-base font-bold text-slate-100">Конструктор</span>
          </div>
          <div className="flex rounded-xl bg-white/[0.03] p-1 border border-white/[0.06]">
            <button
              onClick={() => setMode("builder")}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${mode === "builder" ? "bg-gradient-to-r from-violet-500 to-fuchsia-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              Блоки
            </button>
            <button
              onClick={() => setMode("theme")}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${mode === "theme" ? "bg-gradient-to-r from-violet-500 to-fuchsia-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              OpenCart Тема
            </button>
            <button
              onClick={() => setMode("media")}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${mode === "media" ? "bg-gradient-to-r from-violet-500 to-fuchsia-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              <ImageIcon size={13} /> Медиа
            </button>
            <button
              onClick={() => setMode("foreman")}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${mode === "foreman" ? "bg-gradient-to-r from-violet-500 to-fuchsia-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              <FileSpreadsheet size={13} /> Прораб
            </button>
          </div>
          <div className="h-5 w-px bg-white/10" />
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium uppercase tracking-widest text-slate-500">Страница</span>
            <input
              value={page}
              onChange={(e) => setPage(e.target.value)}
              className="w-32 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-sm font-medium text-slate-200 outline-none transition-all focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20"
            />
          </div>
        </div>

        <div className="flex items-center gap-2">
          {savingOrder && (
            <span className="flex items-center gap-1.5 rounded-full bg-white/5 px-3 py-1 text-[11px] font-medium text-slate-400">
              <ArrowUpDown size={11} className="animate-spin" /> Сохранение порядка...
            </span>
          )}
          <div className="flex rounded-xl bg-white/[0.03] p-1 border border-white/[0.06]">
            <button
              onClick={() => setPreviewMode(false)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${!previewMode ? "bg-gradient-to-r from-violet-500 to-fuchsia-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              <Palette size={13} /> Редактор
            </button>
            <button
              onClick={() => setPreviewMode(true)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all ${previewMode ? "bg-gradient-to-r from-violet-500 to-fuchsia-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"}`}
            >
              <Monitor size={13} /> Предпросмотр
            </button>
          </div>
        </div>
      </div>

      {mode === 'builder' && <>
      {!previewMode && (
        <div className="flex shrink-0 items-center gap-3 border-b border-white/[0.06] bg-slate-900/60 px-6 py-2.5 backdrop-blur-md">
          <Sparkles size={16} className="shrink-0 text-amber-400" />
          <input
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && generateFromPrompt()}
            placeholder="Опишите страницу: 'сделай hero, преимущества, категории и товары'..."
            className="flex-1 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600 focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20"
          />
          <button
            onClick={generateFromPrompt}
            disabled={aiGenerating || !aiPrompt.trim()}
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-amber-500 to-orange-600 px-4 py-1.5 text-xs font-bold text-white shadow-lg shadow-orange-500/20 transition-all hover:shadow-orange-500/40 disabled:opacity-40"
          >
            <Wand2 size={13} />
            {aiGenerating ? "Генерация..." : "Сгенерировать"}
          </button>
        </div>
      )}

      {/* Main workspace */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar — Block Palette */}
        {!previewMode && (
          <div className="w-64 shrink-0 overflow-y-auto border-r border-white/[0.06] bg-slate-950/50 p-4">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-600">Добавить блок</div>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(BLOCK_META).map(([type, meta]) => {
                const Icon = meta.icon;
                return (
                  <button
                    key={type}
                    onClick={() => addBlock(type)}
                    className="group flex flex-col items-center gap-2 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 transition-all hover:border-white/[0.15] hover:bg-white/[0.06] hover:shadow-lg"
                  >
                    <div className={`flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br ${meta.color} text-white shadow-md transition-transform group-hover:scale-110`}>
                      <Icon size={16} />
                    </div>
                    <div className="text-center">
                      <div className="text-[11px] font-semibold text-slate-300">{meta.label}</div>
                      <div className="mt-0.5 text-[9px] leading-tight text-slate-600">{meta.desc}</div>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-6 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
              <div className="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-400">
                <Sparkles size={12} className="text-amber-400" /> Совет
              </div>
              <p className="text-[11px] leading-relaxed text-slate-500">
                Перетаскивайте блоки за иконку ⋮⋮ чтобы менять порядок. Кликните блок, чтобы отредактировать.
              </p>
            </div>
          </div>
        )}

        {/* Center — Editor / Preview */}
        <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-950 via-slate-900/95 to-slate-950">
          {previewMode ? (
            <div className="p-8">
              <PreviewCanvas blocks={blocks} page={page} />
            </div>
          ) : (
            <div className="mx-auto max-w-2xl p-6">
              {/* Instruction banner */}
              <div className="mb-6 rounded-2xl border border-sky-500/15 bg-gradient-to-r from-sky-500/5 to-transparent p-5">
                <h3 className="mb-1 text-sm font-bold text-sky-400">Как работать с конструктором</h3>
                <ol className="ml-4 list-decimal space-y-1 text-xs leading-relaxed text-slate-400 marker:text-sky-500/60">
                  <li><b className="text-slate-300">Выберите страницу</b> — введите имя (home, about, contacts) в верхней панели.</li>
                  <li><b className="text-slate-300">Добавьте блок</b> — нажмите на иконку в левой панели.</li>
                  <li><b className="text-slate-300">Перетащите</b> — зажмите ⋮⋮ и перенесите блок в нужное место.</li>
                  <li><b className="text-slate-300">Редактируйте</b> — кликните по блоку, измените поля, нажмите Сохранить.</li>
                  <li><b className="text-slate-300">Публикуйте</b> — блоки автоматически доступны на stroiapp.ru через API.</li>
                </ol>
              </div>

              {loading && (
                <div className="flex flex-col items-center justify-center py-20">
                  <div className="mb-3 h-8 w-8 animate-spin rounded-full border-2 border-violet-500/30 border-t-violet-500" />
                  <p className="text-sm text-slate-500">Загрузка блоков...</p>
                </div>
              )}

              {!loading && blocks.length === 0 && (
                <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-white/[0.08] py-20">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/[0.03]">
                    <Plus size={28} className="text-slate-600" />
                  </div>
                  <p className="text-base font-semibold text-slate-400">Нет блоков на странице {page}</p>
                  <p className="mt-1 text-sm text-slate-600">Выберите тип в левой панели, чтобы добавить первый блок</p>
                </div>
              )}

              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
              >
                <SortableContext items={blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
                  {blocks.map((block) => (
                    <div key={block.id}>
                      <SortableBlockCard
                        block={block}
                        isSelected={selectedId === block.id}
                        onSelect={setSelectedId}
                        onToggle={toggleBlock}
                        onDelete={deleteBlock}
                        onDuplicate={duplicateBlock}
                      />
                      {selectedId === block.id && (
                        <div className="mb-4 overflow-hidden rounded-b-2xl rounded-t-none border border-t-0 border-white/[0.06] bg-white/[0.02] -mt-3">
                          <PropertyEditor
                            block={block}
                            content={editContent}
                            onChange={setEditContent}
                            onSave={() => saveEdit(block)}
                            onCancel={() => setSelectedId(null)}
                          />
                          <div className="flex items-center justify-end gap-2 border-t border-white/[0.06] px-5 py-3">
                            <button
                              onClick={() => aiGenerate(block)}
                              disabled={aiLoading}
                              className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-500 to-fuchsia-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-violet-500/20 transition-all hover:shadow-violet-500/40 disabled:opacity-50"
                            >
                              <Wand2 size={13} /> {aiLoading ? "Генерация..." : "AI: Сгенерировать текст"}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </SortableContext>
                <DragOverlay dropAnimation={{ duration: 200, easing: "cubic-bezier(0.18, 0.67, 0.6, 1.22)" }}>
                  {activeDragId ? <DragOverlayItem block={blocks.find((b) => b.id === activeDragId)} /> : null}
                </DragOverlay>
              </DndContext>
            </div>
          )}
        </div>
      </div>
      </>}

      {mode === 'media' && (
        <div className="flex flex-1 overflow-hidden">
          <ImageManager addToast={addToast} />
        </div>
      )}

      {mode === 'foreman' && (
        <div className="flex flex-1 overflow-hidden">
          <ForemanUploader addToast={addToast} />
        </div>
      )}

      {mode === 'theme' && (
        <div className="flex flex-1 overflow-hidden">
          {/* Left — Section Palette */}
          <div className="w-64 shrink-0 overflow-y-auto border-r border-white/[0.06] bg-slate-950/50 p-4">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-600">Секции темы</div>
            <div className="space-y-2">
              {themeSections.map((s) => (
                <button
                  key={s.key}
                  onClick={() => {
                    const updated = themeSections.map((x) => x.key === s.key ? { ...x, enabled: !x.enabled } : x);
                    setThemeSections(updated);
                    const active = updated.filter((x) => x.enabled);
                    setGeneratedTwig(generateThemeTwig(active));
                    setGeneratedCss(generateThemeCss(active));
                  }}
                  className={`w-full flex items-center gap-3 rounded-xl border p-3 text-left transition-all ${s.enabled ? 'border-white/[0.15] bg-white/[0.08]' : 'border-white/[0.06] bg-white/[0.02] opacity-60'}`}
                >
                  <span className="text-xl">{s.icon}</span>
                  <div>
                    <div className="text-[12px] font-semibold text-slate-200">{s.label}</div>
                    <div className="text-[10px] text-slate-500">{s.enabled ? 'Включено' : 'Отключено'}</div>
                  </div>
                </button>
              ))}
            </div>
            <div className="mt-6 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
              <div className="mb-2 flex items-center gap-1.5 text-xs font-bold text-slate-400">
                <Sparkles size={12} className="text-amber-400" /> AI Генератор
              </div>
              <p className="text-[11px] leading-relaxed text-slate-500">
                Введите описание в поле сверху и нажмите «Сгенерировать». Система автоматически выберет секции и создаст Twig + CSS.
              </p>
            </div>
          </div>

          {/* Center — Visual Canvas */}
          <div className="flex-1 overflow-y-auto bg-gradient-to-br from-slate-950 via-slate-900/95 to-slate-950 p-6">
            {/* Theme Prompt bar */}
            <div className="flex items-center gap-3 mb-6">
              <Sparkles size={16} className="shrink-0 text-amber-400" />
              <input
                value={themePrompt}
                onChange={(e) => setThemePrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && generateThemeFromPrompt()}
                placeholder="Опишите интерфейс: 'оранжевый hero с калькулятором, категории, товары и акции'..."
                className="flex-1 rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-slate-200 outline-none transition-all placeholder:text-slate-600 focus:border-violet-500/50 focus:ring-2 focus:ring-violet-500/20"
              />
              <button
                onClick={generateThemeFromPrompt}
                disabled={themeGenerating || !themePrompt.trim()}
                className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-amber-500 to-orange-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-orange-500/20 transition-all hover:shadow-orange-500/40 disabled:opacity-40"
              >
                <Wand2 size={13} />
                {themeGenerating ? "Генерация..." : "Сгенерировать"}
              </button>
            </div>

            {/* Visual preview of sections */}
            <div className="mx-auto max-w-4xl space-y-4">
              {themeSections.filter((s) => s.enabled).map((s) => (
                <div key={s.key} className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-2xl">{s.icon}</span>
                    <span className="text-sm font-bold text-slate-200">{s.label}</span>
                    <span className="ml-auto text-[10px] font-medium uppercase tracking-widest text-slate-600">{s.key}</span>
                  </div>
                  <div className="rounded-xl bg-gradient-to-br p-8 text-center text-slate-400" style={{ minHeight: s.key === 'hero' ? '200px' : '100px', background: 'linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)' }}>
                    {s.key === 'hero' && <div><div className="text-2xl font-bold text-white mb-2">Hero Banner</div><div className="text-sm">AI Калькулятор + Slider</div></div>}
                    {s.key === 'features' && <div className="grid grid-cols-4 gap-4"><div>🚚 Доставка</div><div>🛡️ Гарантия</div><div>💰 Цены</div><div>🔄 Возврат</div></div>}
                    {s.key === 'categories' && <div className="grid grid-cols-4 gap-4"><div>📁 Кат</div><div>📁 Кат</div><div>📁 Кат</div><div>📁 Кат</div></div>}
                    {s.key === 'products' && <div className="grid grid-cols-4 gap-4"><div>📦 Товар</div><div>📦 Товар</div><div>📦 Товар</div><div>📦 Товар</div></div>}
                    {s.key === 'promotions' && <div>💰 Акции и спецпредложения</div>}
                    {s.key === 'blog' && <div>📖 Блог — последние статьи</div>}
                    {s.key === 'manufacturers' && <div>🏭 Бренды — логотипы производителей</div>}
                  </div>
                </div>
              ))}
              {themeSections.filter((s) => s.enabled).length === 0 && (
                <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-white/[0.08] py-20">
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/[0.03]">
                    <Plus size={28} className="text-slate-600" />
                  </div>
                  <p className="text-base font-semibold text-slate-400">Нет активных секций</p>
                  <p className="mt-1 text-sm text-slate-600">Введите промпт или включите секции вручную слева</p>
                </div>
              )}
            </div>
          </div>

          {/* Right — Code & Export */}
          <div className="w-80 shrink-0 overflow-y-auto border-l border-white/[0.06] bg-slate-950/50 p-4">
            <div className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-600">Код</div>
            <div className="mb-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
              <div className="mb-2 text-[10px] font-bold text-slate-500">Twig</div>
              <textarea
                value={generatedTwig}
                onChange={(e) => setGeneratedTwig(e.target.value)}
                className="h-32 w-full rounded-lg border border-white/[0.08] bg-white/[0.03] p-2 text-[10px] text-slate-300 font-mono outline-none resize-none"
              />
            </div>
            <div className="mb-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
              <div className="mb-2 text-[10px] font-bold text-slate-500">CSS</div>
              <textarea
                value={generatedCss}
                onChange={(e) => setGeneratedCss(e.target.value)}
                className="h-32 w-full rounded-lg border border-white/[0.08] bg-white/[0.03] p-2 text-[10px] text-slate-300 font-mono outline-none resize-none"
              />
            </div>
            <button
              onClick={exportToStroiapp}
              disabled={exporting || !generatedTwig}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 py-2.5 text-xs font-bold text-white shadow-lg shadow-emerald-500/20 transition-all hover:shadow-emerald-500/40 disabled:opacity-40"
            >
              <ExternalLink size={14} />
              {exporting ? "Экспорт..." : "Экспорт на stroiapp.ru"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
