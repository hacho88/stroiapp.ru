import { useState, useEffect } from "react";
import { Image, Upload, ArrowRight, Monitor, RefreshCw, CheckCircle } from "lucide-react";

const API_BASE = "http://127.0.0.1:8010/api";

async function apiGet(path) {
  const r = await fetch(API_BASE + path);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function apiPost(path, body) {
  const r = await fetch(API_BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function uploadImage(file) {
  const form = new FormData();
  form.append("file", file);
  const r = await fetch(API_BASE + "/opencart/images/upload", {
    method: "POST",
    body: form,
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export default function ImageManager({ addToast }) {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadingId, setUploadingId] = useState(null);
  const [heroUrl, setHeroUrl] = useState("");
  const [savingHero, setSavingHero] = useState(false);

  useEffect(() => {
    loadCategories();
    loadHeroBanner();
  }, []);

  async function loadCategories() {
    setLoading(true);
    try {
      const data = await apiGet("/opencart/categories/tree");
      if (data.tree) {
        const flat = flattenTree(data.tree);
        setCategories(flat.filter((c) => c.image && c.image !== ""));
      }
    } catch (err) {
      addToast("Ошибка загрузки категорий: " + err.message, "error");
    }
    setLoading(false);
  }

  function flattenTree(items, level = 0) {
    const out = [];
    for (const item of items || []) {
      out.push({ ...item, level });
      if (item.children) out.push(...flattenTree(item.children, level + 1));
    }
    return out;
  }

  async function loadHeroBanner() {
    try {
      const data = await apiGet("/opencart/hero/banner");
      if (data.content) {
        const match = data.content.match(/src="([^"]+)"/);
        if (match) setHeroUrl(match[1]);
      }
    } catch (err) {
      console.log("Hero load error:", err);
    }
  }

  async function handleCategoryImage(categoryId, file) {
    setUploadingId(categoryId);
    try {
      const upload = await uploadImage(file);
      const imagePath = upload.path || upload.image || upload.url;
      if (!imagePath) throw new Error("Upload response missing path");
      await apiPost("/opencart/categories/update", {
        category_id: categoryId,
        image: imagePath,
      });
      addToast("Изображение обновлено", "success");
      loadCategories();
    } catch (err) {
      addToast("Ошибка загрузки: " + err.message, "error");
    }
    setUploadingId(null);
  }

  async function updateHeroBanner() {
    if (!heroUrl) return;
    setSavingHero(true);
    try {
      const data = await apiGet("/opencart/hero/banner");
      if (!data.content) throw new Error("Не удалось прочитать home.twig");
      const updated = data.content.replace(
        /src="[^"]+"/,
        `src="${heroUrl}"`
      );
      await apiPost("/opencart/hero/banner", {
        path: "catalog/view/theme/unishop2/template/common/home.twig",
        content: updated,
      });
      await apiPost("/opencart/site/clearCache", {});
      addToast("Слайдер обновлён", "success");
    } catch (err) {
      addToast("Ошибка обновления слайдера: " + err.message, "error");
    }
    setSavingHero(false);
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-white/[0.06] px-6 py-3">
        <div className="flex items-center gap-2 text-sm font-bold text-white">
          <Image size={16} className="text-amber-400" />
          Медиа-менеджер
        </div>
        <button
          onClick={loadCategories}
          className="flex items-center gap-1.5 rounded-lg bg-white/[0.05] px-3 py-1.5 text-xs font-semibold text-slate-300 transition hover:bg-white/[0.1]"
        >
          <RefreshCw size={13} /> Обновить
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Hero Banner Section */}
        <div className="mb-8 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
          <div className="mb-4 flex items-center gap-2 text-base font-bold text-white">
            <Monitor size={16} className="text-blue-400" />
            Главный слайдер (Hero Banner)
          </div>
          <div className="flex gap-3">
            <input
              type="text"
              value={heroUrl}
              onChange={(e) => setHeroUrl(e.target.value)}
              placeholder="URL изображения для слайдера..."
              className="flex-1 rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-blue-500/50"
            />
            <button
              onClick={updateHeroBanner}
              disabled={savingHero || !heroUrl}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-lg shadow-blue-500/20 transition-all hover:shadow-blue-500/40 disabled:opacity-40"
            >
              <ArrowRight size={14} />
              {savingHero ? "Сохранение..." : "Применить"}
            </button>
          </div>
          {heroUrl && (
            <div className="mt-4 overflow-hidden rounded-xl border border-white/[0.06]">
              <img src={heroUrl} alt="Hero preview" className="h-48 w-full object-cover" />
            </div>
          )}
        </div>

        {/* Categories Section */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
          <div className="mb-4 flex items-center gap-2 text-base font-bold text-white">
            <Image size={16} className="text-emerald-400" />
            Изображения категорий
          </div>

          {loading ? (
            <div className="py-12 text-center text-sm text-slate-500">Загрузка категорий...</div>
          ) : categories.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm text-slate-500">Категории с изображениями не найдены</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
              {categories.map((cat) => (
                <div
                  key={cat.category_id}
                  className="group relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.02] p-3 transition hover:border-white/[0.12]"
                >
                  <div className="mb-2 aspect-square overflow-hidden rounded-lg bg-slate-800">
                    {cat.image ? (
                      <img
                        src={`https://stroiapp.ru/image/${cat.image}`}
                        alt={cat.name}
                        className="h-full w-full object-contain p-2"
                        onError={(e) => {
                          e.target.style.display = "none";
                          e.target.nextSibling.style.display = "flex";
                        }}
                      />
                    ) : null}
                    <div
                      className="hidden h-full w-full items-center justify-center text-xs text-slate-600"
                      style={{ display: cat.image ? "none" : "flex" }}
                    >
                      Нет фото
                    </div>
                  </div>
                  <div className="mb-2 truncate text-xs font-semibold text-slate-300">
                    {cat.name}
                  </div>
                  <label className="flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-white/[0.05] py-2 text-[11px] font-semibold text-slate-400 transition hover:bg-white/[0.1] hover:text-white">
                    <Upload size={12} />
                    {uploadingId === cat.category_id ? "Загрузка..." : "Заменить"}
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files?.[0]) {
                          handleCategoryImage(cat.category_id, e.target.files[0]);
                        }
                      }}
                    />
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
