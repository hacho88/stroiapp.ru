import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, ChevronDown, ChevronUp, Eye, EyeOff, Folder, Image as ImageIcon, Maximize2, Minimize2, Monitor, Plus, RefreshCw, Save, Smartphone, Trash2, Upload, X } from "lucide-react";
import { apiDelete, apiGet, apiPost, apiPut, apiUpload } from "../lib/api";

const TYPE_LABELS = {
  header: "Шапка сайта", sections: "Секции главной", logo: "Логотип", hero: "Hero-слайдер", banner: "Баннер",
  text: "Текст", products: "Товары", categories: "Категории", image: "Картинка", video: "Видео",
  carousel: "Карусель", cta: "Кнопка/CTA", html: "HTML", theme: "Тема оформления",
  sec_hero: "Секция: Hero-баннер", sec_categories: "Секция: Категории", sec_solutions: "Секция: Калькуляторы",
  sec_convenient: "Секция: С нами удобно", sec_delivery: "Секция: Доставка", sec_payment: "Секция: Оплата и бонусы",
  sec_brands: "Секция: Бренды", sec_journal: "Секция: Журнал",
};

const FIELD_LABELS = {
  logo_src: "Логотип (картинка)", logo_alt: "Название", logo_link: "Ссылка логотипа", tagline: "Подпись под логотипом",
  phone: "Телефон", phone_link: "Ссылка телефона (tel:)",
  promo_text: "Кнопка «Акции» (текст)", promo_link: "Кнопка «Акции» (ссылка)", promo_color: "Кнопка «Акции» (цвет)",
  primary_color: "Основной цвет (кнопки, цены)", accent_color: "Акцентный цвет", secondary_color: "Фон блоков",
  muted_color: "Приглушённый фон", border_color: "Цвет рамок", font_family: "Шрифт сайта",
  font_scale: "Масштаб интерфейса (%)", radius: "Скругление углов (px)",
  page_width: "Ширина страницы (px, 0 = стандарт, 9999 = на весь экран)",
  src: "URL картинки/видео", alt: "Название (alt)", link: "Ссылка", title: "Заголовок", subtitle: "Подзаголовок",
  bg_image: "Фон (картинка)", bg_color: "Цвет фона", text_color: "Цвет текста", button_color: "Цвет кнопки",
  button_text: "Текст кнопки", button_link: "Ссылка кнопки", body: "Текст", image: "Картинка", caption: "Подпись",
  html: "HTML-код", category_id: "ID категории", limit: "Кол-во", category_ids: "ID категорий (через запятую)",
  images: "URL картинок", slides: "Слайды", autoplay: "Автопрокрутка (сек, 0 = выкл)", height: "Высота",
  video: "Видео (mp4/webm)", poster: "Постер видео", overlay: "Затемнение (0-90)", align: "Выравнивание текста",
  eyebrow: "Бейдж (над заголовком)", h1: "Заголовок H1", intro: "Текст под заголовком",
  foot1: "Преимущество 1", foot2: "Преимущество 2",
  side_eyebrow: "Бейдж правого блока", side_title: "Заголовок правого блока",
  side_button_text: "Кнопка правого блока", side_button_link: "Ссылка кнопки",
  anim: "Анимация появления", anim_speed: "Скорость анимации (1 = норма)",
  anim_pulse: "Пульс кнопки", anim_float: "Парение карточки товара",
  bg_overlay: "Затемнение фона (0-90)", side_image: "Фото правого блока",
  side_bg_color: "Фон правого блока (цвет)", side_text_color: "Цвет текста правого блока",
  product_id: "ID товара в карточке (0 = авто)", product_anim: "Анимация карточки товара",
  palette: "Цветовая гамма сайта",
  link_text: "Текст ссылки", link_href: "URL ссылки",
  cards: "Карточки", features: "Большие карточки", services: "Сервисы", payments: "Способы оплаты",
  articles: "Статьи", brands: "Бренды",
  consult_eyebrow: "Бейдж консультации", consult_title: "Заголовок консультации", consult_text: "Текст консультации",
  action_text: "Текст кнопки «все»", action_link: "Ссылка кнопки «все»",
  bonus_eyebrow: "Бейдж бонусов", bonus_title: "Заголовок бонусов", bonus_text: "Текст бонусов",
  bonus_button: "Кнопка бонусов", bonus_link: "Ссылка кнопки",
};

const SECTION_LABELS = {
  hero: "Hero-баннер", categories: "Категории", solutions: "Калькуляторы и решения", sale: "Скидки для всех",
  convenient: "Удобство покупок", recommend: "Мы рекомендуем", delivery: "Доставка", payment: "Оплата и бонусы",
  brands: "Бренды", journal: "Журнал",
};

const TEXTAREA_FIELDS = new Set(["body", "html", "intro", "consult_text", "bonus_text"]);
const LIST_FIELDS = new Set(["images", "category_ids"]);
const MEDIA_FIELDS = new Set(["src", "image", "bg_image", "logo_src", "poster", "video", "side_image"]);
const NUMBER_FIELDS = new Set(["limit", "category_id", "autoplay", "overlay", "bg_overlay", "font_scale", "radius", "page_width", "anim_speed", "product_id"]);
const SELECT_FIELDS = {
  height: [["small", "Низкий"], ["medium", "Средний"], ["large", "Высокий"]],
  align: [["left", "Слева"], ["center", "По центру"], ["right", "Справа"]],
  anim: [["1", "Вкл"], ["0", "Выкл"]],
  anim_pulse: [["1", "Вкл"], ["0", "Выкл"]],
  palette: [["", "По умолчанию (красная)"], ["red", "Красная"], ["blue", "Синяя"], ["green", "Зелёная"],
    ["orange", "Оранжевая"], ["violet", "Фиолетовая"], ["graphite", "Графит + золото"],
    ["apple-platinum", "Apple: Платина"], ["apple-glacier", "Apple: Ледник"], ["apple-linen", "Apple: Лён"],
    ["apple-cyber", "Apple: Кибер-Бургунди (тёмная)"], ["apple-glass", "Apple: Стекло"], ["apple-desert", "Apple: Пустынный титан"],
    ["apple-elegance", "Apple: Титановая Элегантность"]],
  product_anim: [["carousel", "3D-карусель"], ["float", "Парение"], ["rotate", "Вращение фото"], ["cycle", "Смена товаров"], ["none", "Выкл"]],
  anim_float: [["1", "Вкл"], ["0", "Выкл"]],
  font_family: [["", "Inter (по умолчанию)"], ["Geologica", "Geologica"], ["Roboto", "Roboto"], ["Open Sans", "Open Sans"], ["Montserrat", "Montserrat"],
    ["Manrope", "Manrope"], ["PT Sans", "PT Sans"], ["Rubik", "Rubik"], ["Nunito", "Nunito"],
    ["Oswald", "Oswald"], ["Playfair Display", "Playfair Display"]],
};
const isColorField = (k) => /_color$/.test(k);

function imgUrl(v) {
  if (!v) return "";
  const s = String(v);
  return s.startsWith("http") ? s : `https://stroiapp.ru/image/${s}`;
}

/* ================= Медиа-пикер ================= */

function MediaPicker({ onPick, onClose, notify }) {
  const [path, setPath] = useState("catalog");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);

  const load = useCallback(async (p) => {
    setLoading(true);
    try {
      const d = await apiGet(`/opencart/media/list?path=${encodeURIComponent(p || path)}`);
      setItems(d.items || []);
      if (d.path) setPath(d.path);
    } catch (e) { notify("Ошибка медиа: " + e.message, "error"); }
    finally { setLoading(false); }
  }, [path, notify]);

  useEffect(() => { load("catalog"); /* eslint-disable-next-line */ }, []);

  const upload = async (files) => {
    if (!files?.length) return;
    setUploading(true);
    let ok = 0;
    for (const f of files) {
      try {
        const r = await apiUpload(`/opencart/media/upload?dir=${encodeURIComponent(path)}`, f);
        if (r.status === "uploaded") ok++;
        else notify(`${f.name}: ${r.error || r.detail || "?"}`, "error");
      } catch (e) { notify(`${f.name}: ${e.message}`, "error"); }
    }
    setUploading(false);
    if (ok) { notify(`Загружено: ${ok}`, "success"); load(); }
  };

  const crumbs = path.split("/").filter(Boolean);
  const dirs = items.filter((i) => i.type === "directory");
  const files = items.filter((i) => i.type === "file" && i.is_image);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6" onClick={onClose}>
      <div className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-2xl border border-slate-700 bg-slate-900 p-4" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-center gap-2">
          <span className="text-sm font-bold text-white">Медиабиблиотека</span>
          <div className="flex min-w-0 flex-1 items-center gap-1 overflow-auto text-xs">
            {crumbs.map((c, i) => (
              <span key={i} className="flex items-center gap-1 whitespace-nowrap">
                {i > 0 && <span className="text-slate-600">/</span>}
                <button onClick={() => load(crumbs.slice(0, i + 1).join("/"))}
                  className={i === crumbs.length - 1 ? "font-bold text-emerald-400" : "text-slate-400 hover:text-slate-200"}>{c}</button>
              </span>
            ))}
          </div>
          <button onClick={() => fileRef.current?.click()} disabled={uploading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">
            <Upload size={13} /> {uploading ? "Загрузка..." : "Загрузить"}
          </button>
          <button onClick={onClose} className="rounded-lg bg-slate-800 p-1.5 hover:bg-slate-700"><X size={15} /></button>
          <input ref={fileRef} type="file" multiple accept="image/*,video/*" className="hidden"
            onChange={(e) => { upload([...e.target.files]); e.target.value = ""; }} />
        </div>
        <div className="min-h-0 flex-1 overflow-auto">
          {dirs.length > 0 && (
            <div className="mb-3 grid grid-cols-3 gap-2 sm:grid-cols-4">
              {dirs.map((d) => (
                <button key={d.name} onClick={() => load(`${path}/${d.name}`)}
                  className="flex items-center gap-2 rounded-lg bg-slate-800/60 px-2.5 py-2 text-left text-xs hover:bg-slate-700">
                  <Folder size={14} className="shrink-0 text-amber-400" /><span className="truncate">{d.name}</span>
                </button>
              ))}
            </div>
          )}
          {loading ? (
            <div className="py-10 text-center text-sm text-slate-500">Загрузка...</div>
          ) : files.length ? (
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
              {files.map((f) => (
                <button key={f.name} onClick={() => onPick(`${path}/${f.name}`)}
                  className="group relative overflow-hidden rounded-xl border border-slate-700/40 bg-slate-950 hover:border-emerald-500">
                  <img src={f.url} alt={f.name} loading="lazy" className="aspect-square w-full object-cover" />
                  <span className="absolute inset-x-0 bottom-0 truncate bg-slate-950/80 px-1.5 py-1 text-[10px] text-slate-300">{f.name}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="py-10 text-center text-sm text-slate-500">Нет картинок — загрузи или выбери папку</div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ================= Универсальный редактор массивов ================= */

const ICON_OPTIONS = ["store", "hammer", "shield", "clipboard", "card", "file", "phone", "gift", "truck", "percent", "check", "ruler"];
const ICON_LABELS = { store: "Магазин", hammer: "Молоток", shield: "Щит", clipboard: "Смета", card: "Карта", file: "Документ", phone: "Телефон", gift: "Подарок", truck: "Доставка", percent: "Процент", check: "Галочка", ruler: "Линейка" };
const KIND_LABELS = { image: "Фото", video: "Видео", animation: "Анимация", products: "Товары", brands: "Бренды", text: "Только текст" };

// 4-й элемент поля (массив) = типы слайда, для которых поле показывается
const ARRAY_SPECS = {
  slides: {
    item: "Слайд",
    fields: [
      ["kind", "Тип слайда", "kind"],
      ["image", "Фото", "media", ["image"]],
      ["effect", "Эффект", "select:none|kenburns", ["image"]],
      ["video", "Видео (mp4/embed)", "media", ["video"]],
      ["animation", "Анимация", "select:gradient|aurora|shapes", ["animation"]],
      ["products_category", "ID категории (0=все)", "number", ["products"]],
      ["products_limit", "Кол-во товаров", "number", ["products"]],
      ["brands", "Бренды (через запятую)", "text", ["brands"]],
      ["title", "Заголовок", "text"],
      ["subtitle", "Подзаголовок", "text"],
      ["button_text", "Кнопка", "text"],
      ["button_link", "Ссылка кнопки", "text"],
      ["align", "Текст", "select:left|center|right"],
      ["overlay", "Затемнение 0-90", "number", ["image", "video", "animation"]],
      ["text_color", "Цвет текста", "color"],
      ["bg_color", "Цвет фона", "color"],
    ],
  },
  features: {
    item: "Карточка",
    fields: [["eyebrow", "Бейдж", "text"], ["title", "Заголовок", "text"], ["caption", "Подпись", "text"],
      ["tone", "Стиль", "select:b2b|audit|contractor"], ["link", "Ссылка", "text"]],
  },
  services: {
    item: "Сервис",
    fields: [["icon", "Иконка", "icon"], ["title", "Заголовок", "text"], ["text", "Текст", "text"], ["link", "Ссылка", "text"]],
  },
  payments: {
    item: "Способ",
    fields: [["icon", "Иконка", "icon"], ["title", "Заголовок", "text"], ["text", "Текст", "text"]],
  },
  cards: {
    item: "Карточка",
    fields: [["title", "Заголовок", "text"], ["subtitle", "Подзаголовок", "text"], ["text", "Текст", "text"],
      ["tone", "Стиль", "select:solution-large|solution-side|solution-small|promo-mint|promo-roof|promo-green"],
      ["bg", "Фон (css)", "text"], ["link", "Ссылка", "text"]],
  },
  articles: {
    item: "Статья",
    fields: [["category", "Рубрика", "text"], ["title", "Заголовок", "text"],
      ["tone", "Стиль", "select:article-dark|article-blue|article-grey|article-warm|article-red"], ["link", "Ссылка", "text"]],
  },
  brands: {
    item: "Бренд",
    fields: [["name", "Название", "text"], ["link", "Ссылка", "text"]],
  },
};

const TONE_LABELS = {
  b2b: "Тёмная", audit: "Мятная", contractor: "Синяя",
  "solution-large": "Большая", "solution-side": "Боковая", "solution-small": "Малая",
  "promo-mint": "Мятная", "promo-roof": "Кровля", "promo-green": "Зелёная",
  "article-dark": "Тёмная", "article-blue": "Синяя", "article-grey": "Серая", "article-warm": "Тёплая", "article-red": "Красная",
  none: "Без эффекта", kenburns: "Ken Burns (зум)",
  gradient: "Градиент", aurora: "Аврора", shapes: "Фигуры",
  left: "Слева", center: "По центру", right: "Справа",
};

function ArrayEditor({ specKey, items, onChange, pickMedia }) {
  const spec = ARRAY_SPECS[specKey] || { item: "Элемент", fields: [["title", "Заголовок", "text"], ["text", "Текст", "text"], ["link", "Ссылка", "text"]] };
  const list = (Array.isArray(items) ? items : []).map((s) => (typeof s === "string" ? { name: s } : s));
  const set = (i, k, v) => onChange(list.map((s, j) => (j === i ? { ...s, [k]: v } : s)));
  const move = (i, d) => {
    const j = i + d;
    if (j < 0 || j >= list.length) return;
    const n = [...list];
    [n[i], n[j]] = [n[j], n[i]];
    onChange(n);
  };
  const empty = Object.fromEntries(spec.fields.filter((f) => f[1] !== "kind").map(([k]) => [k, ""]));
  return (
    <div className="space-y-2">
      {list.map((s, i) => (
        <div key={i} className="rounded-lg border border-slate-700/50 bg-slate-950/60 p-2.5">
          <div className="mb-2 flex items-center gap-1">
            <span className="flex-1 truncate text-[11px] font-bold text-slate-400">
              {spec.item} {i + 1}{s.kind ? ` · ${KIND_LABELS[s.kind] || s.kind}` : ""}{s.title || s.name ? ` · ${s.title || s.name}` : ""}
            </span>
            <button onClick={() => move(i, -1)} disabled={i === 0} className="rounded p-0.5 text-slate-400 hover:bg-slate-700 disabled:opacity-30"><ChevronUp size={12} /></button>
            <button onClick={() => move(i, 1)} disabled={i === list.length - 1} className="rounded p-0.5 text-slate-400 hover:bg-slate-700 disabled:opacity-30"><ChevronDown size={12} /></button>
            <button onClick={() => onChange(list.filter((_, j) => j !== i))} className="rounded p-0.5 text-red-400 hover:bg-red-900/40"><Trash2 size={12} /></button>
          </div>
          {s.image && <img src={imgUrl(s.image)} alt="" className="mb-2 h-16 w-full rounded-lg object-cover" />}
          <div className="grid grid-cols-2 gap-1.5">
            {spec.fields.filter((f) => !f[3] || f[3].includes(s.kind || "image")).map(([k, label, kind]) => (
              <div key={k} className={kind === "media" ? "col-span-2" : ""}>
                <label className="mb-0.5 block text-[10px] text-slate-500">{label}</label>
                {kind === "kind" ? (
                  <select value={s.kind || "image"} onChange={(e) => set(i, "kind", e.target.value)}
                    className="w-full rounded border border-emerald-700/60 bg-slate-950 px-2 py-1 text-[11px] font-bold text-emerald-400 outline-none focus:border-emerald-500">
                    {Object.entries(KIND_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                ) : kind === "number" ? (
                  <input type="number" value={s[k] ?? ""} onChange={(e) => set(i, k, Number(e.target.value) || 0)}
                    className="w-full rounded border border-slate-700/50 bg-slate-950 px-2 py-1 text-[11px] outline-none focus:border-emerald-500" />
                ) : kind === "color" ? (
                  <div className="flex gap-1">
                    <input type="color" value={s[k] || "#e11d48"} onChange={(e) => set(i, k, e.target.value)} className="h-7 w-8 shrink-0 cursor-pointer rounded border border-slate-700 bg-slate-950" />
                    <input value={s[k] || ""} onChange={(e) => set(i, k, e.target.value)} placeholder="#rrggbb"
                      className="w-full rounded border border-slate-700/50 bg-slate-950 px-2 py-1 text-[11px] outline-none focus:border-emerald-500" />
                  </div>
                ) : kind === "icon" ? (
                  <select value={s[k] || ""} onChange={(e) => set(i, k, e.target.value)}
                    className="w-full rounded border border-slate-700/50 bg-slate-950 px-2 py-1 text-[11px] outline-none focus:border-emerald-500">
                    <option value="">—</option>
                    {ICON_OPTIONS.map((o) => <option key={o} value={o}>{ICON_LABELS[o] || o}</option>)}
                  </select>
                ) : kind.startsWith("select:") ? (
                  <select value={s[k] || ""} onChange={(e) => set(i, k, e.target.value)}
                    className="w-full rounded border border-slate-700/50 bg-slate-950 px-2 py-1 text-[11px] outline-none focus:border-emerald-500">
                    {kind.slice(7).split("|").map((o) => <option key={o} value={o}>{TONE_LABELS[o] || o}</option>)}
                  </select>
                ) : (
                  <div className="flex gap-1">
                    <input value={s[k] || ""} onChange={(e) => set(i, k, e.target.value)}
                      className="w-full rounded border border-slate-700/50 bg-slate-950 px-2 py-1 text-[11px] outline-none focus:border-emerald-500" />
                    {kind === "media" && (
                      <button onClick={() => pickMedia((p) => set(i, k, p))} title="Выбрать из медиа"
                        className="shrink-0 rounded border border-slate-700/50 bg-slate-800 px-1.5 text-slate-300 hover:bg-slate-700"><ImageIcon size={12} /></button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
      <button onClick={() => onChange([...list, { ...empty }])}
        className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-dashed border-slate-600 px-2 py-1.5 text-[11px] text-slate-400 hover:border-emerald-500 hover:text-emerald-400">
        <Plus size={12} /> Добавить: {spec.item}
      </button>
    </div>
  );
}

/* ================= Основной редактор ================= */

export default function SiteContentEditor({ site, onBack, addToast }) {
  const page = `site:${site.id}`;
  const [blocks, setBlocks] = useState([]);
  const [types, setTypes] = useState({});
  const [loading, setLoading] = useState(false);
  const [newType, setNewType] = useState("banner");
  const [selected, setSelected] = useState(null);
  const [drafts, setDrafts] = useState({});
  const [device, setDevice] = useState("desktop");
  const [full, setFull] = useState(false);
  const [frameKey, setFrameKey] = useState(0);
  const [frameLoading, setFrameLoading] = useState(true);
  const [mediaOpen, setMediaOpen] = useState(false);
  const mediaCb = useRef(null);
  const frameRef = useRef(null);
  const notify = useCallback((m, t = "info") => addToast && addToast(m, t), [addToast]);

  const pickMedia = (cb) => { mediaCb.current = cb; setMediaOpen(true); };
  const onPicked = (p) => { setMediaOpen(false); mediaCb.current?.(p); };
  const reloadFrame = useCallback(() => { setFrameLoading(true); setFrameKey((k) => k + 1); }, []);

  const load = useCallback(async (reload = false) => {
    setLoading(true);
    try {
      const [b, t] = await Promise.all([
        apiGet(`/site-builder/blocks?page=${encodeURIComponent(page)}&all=true`),
        apiGet("/site-builder/block-types"),
      ]);
      setBlocks(b.blocks || []);
      setTypes(t.types || {});
      setDrafts({});
      if (reload) reloadFrame();
    } catch (e) { notify("Ошибка: " + e.message, "error"); }
    finally { setLoading(false); }
  }, [page, notify, reloadFrame]);

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  // Клик по области на сайте (в iframe) → открыть соответствующий блок
  useEffect(() => {
    const onMsg = (e) => {
      if (e.data?.type !== "sb:select") return;
      const id = String(e.data.id || "");
      let target = null;
      if (id === "header") target = blocks.find((b) => b.type === "header");
      else if (id.startsWith("sec:")) {
        const key = id.slice(4);
        target = blocks.find((b) => b.type === `sec_${key}`) || blocks.find((b) => b.type === "sections");
      } else target = blocks.find((b) => String(b.id) === id);
      if (target) {
        setSelected(target.id);
        setTimeout(() => document.getElementById(`sb-block-${target.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" }), 60);
      }
    };
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, [blocks]);

  // Выбор блока в панели → скролл сайта к этой области
  const selectBlock = (b) => {
    const id = selected === b.id ? null : b.id;
    setSelected(id);
    if (!id) return;
    const sbId = b.type === "header" ? "header" : b.type.startsWith("sec_") ? `sec:${b.type.slice(4)}` : String(b.id);
    frameRef.current?.contentWindow?.postMessage({ type: "sb:scroll", id: sbId }, "*");
  };

  const addBlock = async (type, atIndex) => {
    const content = { ...(types[type] || {}) };
    const sort = atIndex == null ? blocks.reduce((m, b) => Math.max(m, b.sort_order), -1) + 1 : atIndex;
    const r = await apiPost("/site-builder/blocks", { page, type, content, sort_order: sort }).catch((e) => ({ error: e.message }));
    if (r.error) return notify(r.error, "error");
    if (atIndex != null) {
      const ordered = blocks.map((b) => b.id);
      ordered.splice(atIndex, 0, r.id);
      await apiPost("/site-builder/reorder", { page, ordered_ids: ordered }).catch(() => {});
    }
    setSelected(r.id);
    load(true);
  };

  const saveBlock = async (b) => {
    const content = drafts[b.id];
    if (!content) return;
    const r = await apiPut(`/site-builder/blocks/${b.id}`, { content }).catch((e) => ({ error: e.message }));
    if (r.error) return notify(r.error, "error");
    notify("Сохранено — обновляю сайт", "success");
    setDrafts((d) => { const n = { ...d }; delete n[b.id]; return n; });
    load(true);
  };

  const saveAll = async () => {
    for (const [id, content] of Object.entries(drafts)) {
      await apiPut(`/site-builder/blocks/${id}`, { content }).catch(() => {});
    }
    notify("Все изменения сохранены", "success");
    setDrafts({});
    load(true);
  };

  const toggleBlock = async (b) => {
    await apiPut(`/site-builder/blocks/${b.id}`, { is_active: !b.is_active }).catch((e) => notify(e.message, "error"));
    load(true);
  };

  const removeBlock = async (b) => {
    if (!window.confirm(`Удалить блок «${TYPE_LABELS[b.type] || b.type}»?`)) return;
    await apiDelete(`/site-builder/blocks/${b.id}`).catch((e) => notify(e.message, "error"));
    if (selected === b.id) setSelected(null);
    load(true);
  };

  const move = async (b, dir) => {
    const idx = blocks.findIndex((x) => x.id === b.id);
    if (!blocks[idx + dir]) return;
    const ordered = blocks.map((x) => x.id);
    [ordered[idx], ordered[idx + dir]] = [ordered[idx + dir], ordered[idx]];
    await apiPost("/site-builder/reorder", { page, ordered_ids: ordered }).catch((e) => notify(e.message, "error"));
    load(true);
  };

  const fieldVal = (b, key) => {
    const c = drafts[b.id] || b.content;
    const v = c[key];
    return LIST_FIELDS.has(key) && Array.isArray(v) ? v.join(", ") : (v ?? "");
  };

  const setField = (b, key, raw) => {
    const base = { ...(drafts[b.id] || b.content) };
    if (LIST_FIELDS.has(key)) {
      base[key] = raw.split(",").map((s) => s.trim()).filter(Boolean).map((s) => (/^\d+$/.test(s) ? Number(s) : s));
    } else if (NUMBER_FIELDS.has(key)) {
      base[key] = Number(raw) || 0;
    } else {
      base[key] = raw;
    }
    setDrafts((d) => ({ ...d, [b.id]: base }));
  };

  const renderField = (b, key) => {
    const val = (drafts[b.id] || b.content)[key];
    const label = b.type === "sections" ? (SECTION_LABELS[key] || key) : (FIELD_LABELS[key] || key);

    if (typeof val === "boolean") {
      return (
        <label key={key} className="flex cursor-pointer items-center gap-2 rounded-lg bg-slate-950/60 px-2.5 py-1.5">
          <input type="checkbox" checked={!!val} onChange={(e) => setField(b, key, e.target.checked)} className="accent-emerald-500" />
          <span className="text-xs text-slate-300">{label}</span>
        </label>
      );
    }
    if (key in ARRAY_SPECS) {
      return (
        <div key={key}>
          <label className="mb-1 block text-[11px] text-slate-500">{label}</label>
          <ArrayEditor specKey={key} items={Array.isArray(val) ? val : []} onChange={(v) => setField(b, key, v)} pickMedia={pickMedia} />
        </div>
      );
    }
    return (
      <div key={key}>
        <label className="mb-1 block text-[11px] text-slate-500">{label}</label>
        {TEXTAREA_FIELDS.has(key) ? (
          <textarea rows={4} value={fieldVal(b, key)} onChange={(e) => setField(b, key, e.target.value)}
            className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-2.5 py-1.5 text-xs outline-none focus:border-emerald-500" />
        ) : SELECT_FIELDS[key] ? (
          <select value={fieldVal(b, key)} onChange={(e) => setField(b, key, e.target.value)}
            className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-2.5 py-1.5 text-xs outline-none focus:border-emerald-500">
            {SELECT_FIELDS[key].map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        ) : isColorField(key) ? (
          <div className="flex gap-1.5">
            <input type="color" value={fieldVal(b, key) || "#e11d48"} onChange={(e) => setField(b, key, e.target.value)}
              className="h-8 w-10 shrink-0 cursor-pointer rounded-lg border border-slate-700 bg-slate-950" />
            <input value={fieldVal(b, key)} onChange={(e) => setField(b, key, e.target.value)} placeholder="#rrggbb"
              className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-2.5 py-1.5 text-xs outline-none focus:border-emerald-500" />
          </div>
        ) : (
          <div className="flex gap-1.5">
            <input value={fieldVal(b, key)} onChange={(e) => setField(b, key, e.target.value)}
              type={NUMBER_FIELDS.has(key) ? "number" : "text"}
              className="w-full rounded-lg border border-slate-700/50 bg-slate-950 px-2.5 py-1.5 text-xs outline-none focus:border-emerald-500" />
            {(MEDIA_FIELDS.has(key) || LIST_FIELDS.has(key)) && (
              <button onClick={() => pickMedia((p) => setField(b, key, LIST_FIELDS.has(key) ? (fieldVal(b, key) ? fieldVal(b, key) + ", " + p : p) : p))}
                title="Выбрать из медиа" className="shrink-0 rounded-lg border border-slate-700/50 bg-slate-800 px-2 text-slate-300 hover:bg-slate-700">
                <ImageIcon size={13} />
              </button>
            )}
            {MEDIA_FIELDS.has(key) && fieldVal(b, key) && (
              <button onClick={() => setField(b, key, "")} title="Убрать картинку"
                className="shrink-0 rounded-lg border border-slate-700/50 bg-slate-800 px-2 text-slate-400 hover:bg-red-900/40 hover:text-red-300">
                <X size={13} />
              </button>
            )}
          </div>
        )}
        {MEDIA_FIELDS.has(key) && fieldVal(b, key) && !/\.(mp4|webm|mov)/i.test(fieldVal(b, key)) && (
          <img src={imgUrl(fieldVal(b, key))} alt="" className="mt-1 h-12 rounded object-cover" onError={(e) => (e.target.style.display = "none")} />
        )}
      </div>
    );
  };

  const dirtyCount = Object.keys(drafts).length;

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-slate-700/30 glass p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button onClick={onBack} className="rounded-lg bg-slate-800 p-2 hover:bg-slate-700"><ArrowLeft size={16} /></button>
            <div>
              <h2 className="text-lg font-bold text-white">Редактор: {site.city || site.name}</h2>
              <p className="text-xs text-slate-500">{site.domain} · {blocks.length} блоков{dirtyCount ? ` · ${dirtyCount} не сохранено` : ""}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {dirtyCount > 0 && (
              <button onClick={saveAll} className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">
                <Save size={15} /> Сохранить всё ({dirtyCount})
              </button>
            )}
            <button onClick={reloadFrame} className="rounded-lg bg-slate-800 p-2 text-slate-300 hover:bg-slate-700" title="Обновить превью"><RefreshCw size={15} /></button>
            <div className="flex rounded-lg bg-slate-800 p-0.5">
              <button onClick={() => setDevice("desktop")} className={`rounded-md p-1.5 ${device === "desktop" ? "bg-emerald-500 text-slate-950" : "text-slate-400"}`} title="Десктоп"><Monitor size={15} /></button>
              <button onClick={() => setDevice("mobile")} className={`rounded-md p-1.5 ${device === "mobile" ? "bg-emerald-500 text-slate-950" : "text-slate-400"}`} title="Мобильный"><Smartphone size={15} /></button>
            </div>
            <button onClick={() => setFull((f) => !f)} className="rounded-lg bg-slate-800 p-2 text-slate-300 hover:bg-slate-700" title={full ? "Обычный размер" : "На весь экран"}>
              {full ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
            </button>
            <select value={newType} onChange={(e) => setNewType(e.target.value)}
              className="rounded-lg border border-slate-700/50 bg-slate-950 px-3 py-2 text-sm outline-none">
              {Object.keys(types).map((t) => <option key={t} value={t}>{TYPE_LABELS[t] || t}</option>)}
            </select>
            <button onClick={() => addBlock(newType)} className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">
              <Plus size={15} /> Блок
            </button>
          </div>
        </div>
      </div>

      <div className={full ? "fixed inset-0 z-40 flex items-start gap-4 overflow-auto bg-slate-950 p-4" : "flex items-start gap-4"}>
        <div className="min-w-0 flex-1">
          <div className={`relative mx-auto overflow-hidden rounded-2xl border border-slate-700/40 bg-white shadow-2xl transition-all ${device === "mobile" ? "max-w-sm" : "w-full"}`}>
            {frameLoading && (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80 text-sm text-slate-500">
                Загрузка {site.domain}...
              </div>
            )}
            <iframe ref={frameRef} key={frameKey} src={`${site.url}?_edit=${frameKey}`} onLoad={() => setFrameLoading(false)}
              className={`w-full border-0 ${full ? "h-[calc(100vh-140px)]" : "h-[75vh]"}`} title={site.domain} />
          </div>
          <p className="mt-2 text-center text-xs text-slate-500">
            Живой сайт {site.domain} — кликни по любой области, чтобы открыть её настройки. Зелёная рамка = редактируемый блок.
          </p>
        </div>

        <div className="w-96 shrink-0 space-y-2">
          <div className="rounded-2xl border border-slate-700/30 glass p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-bold text-white">Блоки страницы</span>
              <span className="text-xs text-slate-500">{blocks.length}</span>
            </div>
            {loading && <div className="py-6 text-center text-xs text-slate-500">Загрузка...</div>}
            {!loading && blocks.length === 0 && (
              <div className="py-6 text-center text-xs text-slate-500">
                Блоков нет — добавь через «+ Блок».<br />«Секция: …» редактирует встроенные разделы сайта.
              </div>
            )}
            <div className="space-y-2">
              {blocks.map((b, i) => {
                const open = selected === b.id;
                const dirty = !!drafts[b.id];
                return (
                  <div key={b.id} id={`sb-block-${b.id}`} className={`rounded-xl border ${open ? "border-emerald-500/60" : "border-slate-700/40"} bg-slate-900/60`}>
                    <div className="flex items-center gap-1.5 px-3 py-2">
                      <button onClick={() => selectBlock(b)} className="flex min-w-0 flex-1 items-center gap-2 text-left">
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${b.is_active ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-700 text-slate-400"}`}>
                          {TYPE_LABELS[b.type] || b.type}
                        </span>
                        <span className="truncate text-xs text-slate-400">
                          {b.content?.title || b.content?.logo_alt || b.content?.alt || b.content?.body?.slice(0, 30) || `#${b.id}`}
                        </span>
                        {dirty && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" title="Не сохранено" />}
                      </button>
                      <button onClick={() => move(b, -1)} disabled={i === 0} className="rounded p-1 text-slate-400 hover:bg-slate-700 disabled:opacity-30"><ChevronUp size={12} /></button>
                      <button onClick={() => move(b, 1)} disabled={i === blocks.length - 1} className="rounded p-1 text-slate-400 hover:bg-slate-700 disabled:opacity-30"><ChevronDown size={12} /></button>
                      <button onClick={() => toggleBlock(b)} className="rounded p-1 text-slate-400 hover:bg-slate-700" title={b.is_active ? "Скрыть" : "Показать"}>
                        {b.is_active ? <Eye size={12} /> : <EyeOff size={12} />}
                      </button>
                      <button onClick={() => removeBlock(b)} className="rounded p-1 text-red-400 hover:bg-red-900/40"><Trash2 size={12} /></button>
                    </div>
                    {open && (
                      <div className="space-y-2.5 border-t border-slate-700/40 px-3 py-3">
                        {Object.keys(b.content || {}).map((key) => renderField(b, key))}
                        {dirty && (
                          <button onClick={() => saveBlock(b)} className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-emerald-400">
                            <Save size={12} /> Сохранить
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {mediaOpen && <MediaPicker onPick={onPicked} onClose={() => setMediaOpen(false)} notify={notify} />}
    </div>
  );
}
