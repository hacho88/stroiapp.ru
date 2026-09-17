import React from "react";
import { createRoot } from "react-dom/client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import {
  AlertCircle, Award, BarChart3, Box, Building, Calculator, CheckCircle, Clipboard, Download, Eye, FileCheck, FileUp, Globe, LayoutDashboard,
  FileText, Folder, Image, MapPin, MessageSquare, MonitorCheck, Package, PenTool, Plus, Rocket, Save, Search, Send, Settings, ShieldCheck, ShoppingCart, Sparkles, Star, Tag, Users,
  RefreshCw, Target, TrendingUp, Upload, Wand2, X, Zap, Menu, LogOut
} from "lucide-react";
import "./index.css";
import { apiGet, apiPost, apiUpload, apiUrl, apiLogin, getToken, clearToken } from "./lib/api";
import SiteBuilder from "./components/SiteBuilder";
import YandexWebmaster from "./components/YandexWebmaster";
import { LayoutTemplate } from "lucide-react";

const budgets = [5000, 10000, 20000, 50000, 100000];
const TABS = [
  { id: "dashboard", label: "Дашборд", icon: LayoutDashboard },
  { id: "products", label: "Товары", icon: Package },
  { id: "campaigns", label: "Реклама", icon: Target },
  { id: "seo", label: "SEO", icon: Sparkles },
  { id: "competitors", label: "Конкуренты", icon: Eye },
  { id: "opencart", label: "OpenCart", icon: ShoppingCart },
  { id: "site", label: "Сайт", icon: MonitorCheck },
  { id: "site-builder", label: "Конструктор", icon: LayoutTemplate },
  { id: "files", label: "Файлы сайта", icon: Folder },
  { id: "ai-seo", label: "AI SEO", icon: Wand2 },
  { id: "competitors-bids", label: "Ставки", icon: Award },
  { id: "budget-roi", label: "Бюджет", icon: BarChart3 },
  { id: "promotions", label: "Акции", icon: Tag },
  { id: "tenders", label: "Тендеры", icon: FileText },
  { id: "reviews", label: "Отзывы", icon: MessageSquare },
  { id: "autosmeta", label: "Смета", icon: Calculator },
  { id: "content-factory", label: "Контент", icon: PenTool },
  { id: "clients-objects", label: "Объекты", icon: Building },
  { id: "sync", label: "Синхронизация", icon: RefreshCw },
  { id: "webmaster", label: "Вебмастер", icon: Globe },
  { id: "tools", label: "Инструменты", icon: Zap },
];

function money(value) {
  return new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB", maximumFractionDigits: 0 }).format(value || 0);
}

function roiColor(roi) {
  if (roi >= 150) return "text-emerald-400";
  if (roi >= 120) return "text-amber-400";
  return "text-red-400";
}

class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6 text-sm text-red-300">
          <div className="mb-1 font-bold">Ошибка интерфейса</div>
          <div className="font-mono text-xs break-all">{String(this.state.error)}</div>
          <button onClick={() => this.setState({ error: null })} className="mt-3 rounded bg-slate-800 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700">Повторить</button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [authed, setAuthed] = React.useState(!!getToken());
  const [mobileMenu, setMobileMenu] = React.useState(false);
  const mainRef = React.useRef(null);
  const [tab, setTab] = React.useState("dashboard");
  const [products, setProducts] = React.useState([]);
  const [compare, setCompare] = React.useState([]);
  const [selection, setSelection] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [query, setQuery] = React.useState("");
  const [seoResults, setSeoResults] = React.useState([]);
  const [seoLoading, setSeoLoading] = React.useState(false);
  const [seoStats, setSeoStats] = React.useState(null);
  const [geoPagesLoading, setGeoPagesLoading] = React.useState(false);
  const [geoPagesResult, setGeoPagesResult] = React.useState(null);
  const [competitorResults, setCompetitorResults] = React.useState([]);
  const [competitorLoading, setCompetitorLoading] = React.useState(false);
  const [campaigns, setCampaigns] = React.useState([]);
  const [innResult, setInnResult] = React.useState(null);
  const [innQuery, setInnQuery] = React.useState("");
  const [innLoading, setInnLoading] = React.useState(false);
  const [collapsed, setCollapsed] = React.useState(false);
  const [openCartStatus, setOpenCartStatus] = React.useState(null);
  const [openCartLoading, setOpenCartLoading] = React.useState(false);
  const [filePath, setFilePath] = React.useState("catalog/controller/product/product.php");
  const [fileListPath, setFileListPath] = React.useState("catalog/");
  const [fileItems, setFileItems] = React.useState([]);
  const [fileContent, setFileContent] = React.useState("");
  const [fileStatus, setFileStatus] = React.useState("");
  const [fileLoading, setFileLoading] = React.useState(false);
  const [siteHealth, setSiteHealth] = React.useState(null);
  const [siteErrorLog, setSiteErrorLog] = React.useState("");
  const [siteBackups, setSiteBackups] = React.useState([]);
  const [siteImages, setSiteImages] = React.useState(null);
  const [siteLoading, setSiteLoading] = React.useState(false);
  const [ocCategories, setOcCategories] = React.useState([]);
  const [ocOrders, setOcOrders] = React.useState([]);
  const [ocCustomers, setOcCustomers] = React.useState([]);
  const [ocDataLoading, setOcDataLoading] = React.useState(false);
  const [selectedOrder, setSelectedOrder] = React.useState(null);
  const [orderDetailLoading, setOrderDetailLoading] = React.useState(false);
  const [ocProducts, setOcProducts] = React.useState([]);
  const [ocProductQuery, setOcProductQuery] = React.useState("");
  const [selectedOcProduct, setSelectedOcProduct] = React.useState(null);
  const [ocProductLoading, setOcProductLoading] = React.useState(false);
  const [banners, setBanners] = React.useState([]);
  const [selectedBanner, setSelectedBanner] = React.useState(null);
  const [bannerLoading, setBannerLoading] = React.useState(false);
  const [settings, setSettings] = React.useState(null);
  const [settingsLoading, setSettingsLoading] = React.useState(false);
  const [selectedCategory, setSelectedCategory] = React.useState(null);
  const [categoryLoading, setCategoryLoading] = React.useState(false);
  const [selectedCustomer, setSelectedCustomer] = React.useState(null);
  const [customerLoading, setCustomerLoading] = React.useState(false);
  const [customerOrders, setCustomerOrders] = React.useState([]);
  const [toasts, setToasts] = React.useState([]);
  const [aiSeoProducts, setAiSeoProducts] = React.useState([]);
  const [aiSeoFilter, setAiSeoFilter] = React.useState('all');
  const [aiSeoLoading, setAiSeoLoading] = React.useState(false);
  const [aiSeoProgress, setAiSeoProgress] = React.useState({ current: 0, total: 0, ok: 0, fail: 0 });
  const [aiSeoLog, setAiSeoLog] = React.useState([]);
  const [aiSeoPreview, setAiSeoPreview] = React.useState(null);
  const [competitorsList, setCompetitorsList] = React.useState([]);
  const [competitorName, setCompetitorName] = React.useState("");
  const [competitorUrl, setCompetitorUrl] = React.useState("");
  const [compLoading, setCompLoading] = React.useState(false);
  const [compScanning, setCompScanning] = React.useState(null);
  const [compComparisons, setCompComparisons] = React.useState([]);
  const [compShowCompare, setCompShowCompare] = React.useState(false);
  const [compSelectedId, setCompSelectedId] = React.useState(null);
  const [compSelectedProducts, setCompSelectedProducts] = React.useState([]);
  const [compSelectedStats, setCompSelectedStats] = React.useState(null);
  const [aiRecs, setAiRecs] = React.useState(null);
  const [aiRecsLoading, setAiRecsLoading] = React.useState(false);
  const [aiKeywordResult, setAiKeywordResult] = React.useState(null);
  const [discoverQuery, setDiscoverQuery] = React.useState("");
  const [discoverLoading, setDiscoverLoading] = React.useState(false);
  const [bidsAnalysis, setBidsAnalysis] = React.useState(null);
  const [bidsLoading, setBidsLoading] = React.useState(false);
  const [selectedCity, setSelectedCity] = React.useState(null);
  const [geoCities, setGeoCities] = React.useState([]);
  const [geoRegions, setGeoRegions] = React.useState([]);
  const [compAds, setCompAds] = React.useState([]);
  const [compAdsLoading, setCompAdsLoading] = React.useState(false);
  const [compAdsStrategy, setCompAdsStrategy] = React.useState(null);
  const [pwScanning, setPwScanning] = React.useState(null); // id конкурента, которого сканируем через Playwright
  const [pwUrl, setPwUrl] = React.useState(""); // URL для сканирования через Playwright
  const [pwUrlLoading, setPwUrlLoading] = React.useState(false);
  const [pwUrlResult, setPwUrlResult] = React.useState(null);
  const [ourProductsAds, setOurProductsAds] = React.useState(null);
  const [ourProductsAdsLoading, setOurProductsAdsLoading] = React.useState(false);
  const [budgetAmount, setBudgetAmount] = React.useState(50000);
  const [budgetResults, setBudgetResults] = React.useState(null);
  const [budgetLoading, setBudgetLoading] = React.useState(false);
  const [budgetForecast, setBudgetForecast] = React.useState([]);
  const [promoBundles, setPromoBundles] = React.useState([]);
  const [promoList, setPromoList] = React.useState([]);
  const [promoLoading, setPromoLoading] = React.useState(false);
  const [promoName, setPromoName] = React.useState("");
  const [promoDiscount, setPromoDiscount] = React.useState(10);
  const [specialProducts, setSpecialProducts] = React.useState([]);
  const [specialSearch, setSpecialSearch] = React.useState("");
  const [specialSelected, setSpecialSelected] = React.useState(null);
  const [specialPriceInput, setSpecialPriceInput] = React.useState("");
  const [specialLoading, setSpecialLoading] = React.useState(false);
  const [tendersList, setTendersList] = React.useState([]);
  const [tenderRegion, setTenderRegion] = React.useState("Москва");
  const [tenderLoading, setTenderLoading] = React.useState(false);
  const [tenderCoverage, setTenderCoverage] = React.useState(null);
  const [reviewsList, setReviewsList] = React.useState([]);
  const [reviewsLoading, setReviewsLoading] = React.useState(false);
  const [kpText, setKpText] = React.useState("");
  const [kpTarget, setKpTarget] = React.useState("");
  const [smetaItems, setSmetaItems] = React.useState([]);
  const [smetaPaymentType, setSmetaPaymentType] = React.useState("nal");
  const [smetaLoading, setSmetaLoading] = React.useState(false);
  const [smetaInvoice, setSmetaInvoice] = React.useState(null);
  const [contentArticles, setContentArticles] = React.useState([]);
  const [contentQueue, setContentQueue] = React.useState([]);
  const [contentLoading, setContentLoading] = React.useState(false);
  const [contentCount, setContentCount] = React.useState(5);
  const [clientsList, setClientsList] = React.useState([]);
  const [objectsList, setObjectsList] = React.useState([]);
  const [objLoading, setObjLoading] = React.useState(false);
  const [objName, setObjName] = React.useState("");
  const [objAddress, setObjAddress] = React.useState("");
  const [objClient, setObjClient] = React.useState("");
  const [objStage, setObjStage] = React.useState("фундамент");
  const [objArea, setObjArea] = React.useState(100);
  const [objForecast, setObjForecast] = React.useState(null);
  const [catTree, setCatTree] = React.useState([]);
  const [catProducts, setCatProducts] = React.useState([]);
  const [selCatId, setSelCatId] = React.useState(null);
  const [selProduct, setSelProduct] = React.useState(null);
  const [prodSearch, setProdSearch] = React.useState("");
  const [catLoading, setCatLoading] = React.useState(false);

  // Live Sync states
  const [syncLog, setSyncLog] = React.useState([]);
  const [syncRunning, setSyncRunning] = React.useState(false);
  const [syncWatchRunning, setSyncWatchRunning] = React.useState(false);
  const [syncLoading, setSyncLoading] = React.useState(false);

  function addToast(message, type = 'success') {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => removeToast(id), 4000);
  }

  function removeToast(id) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  React.useEffect(() => {
    const onExpired = () => setAuthed(false);
    window.addEventListener("ai-auth-expired", onExpired);
    return () => window.removeEventListener("ai-auth-expired", onExpired);
  }, []);

  React.useEffect(() => {
    if (mainRef.current) mainRef.current.scrollTo(0, 0);
    window.scrollTo(0, 0);
  }, [tab]);

  React.useEffect(() => {
    if (!authed) return;
    Promise.all([apiGet("/product/list"), apiGet("/dashboard/compare")])
      .then(([productData, compareData]) => {
        setProducts(productData);
        setCompare(compareData);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [authed]);

  // Geo: load cities and detect user city
  React.useEffect(() => {
    if (!authed) return;
    apiGet("/geo/cities").then((data) => {
      if (data.cities) setGeoCities(data.cities);
    }).catch(() => {});
    apiGet("/geo/regions").then((data) => {
      if (data.regions) setGeoRegions(data.regions);
    }).catch(() => {});
    apiGet("/geo/detect").then((data) => {
      if (data.city) setSelectedCity(data.city);
    }).catch(() => {});
  }, [authed]);

  React.useEffect(() => {
    if (tab !== 'opencart') return;
    const interval = setInterval(() => {
      if (!ocDataLoading) {
        apiGet("/opencart/orders/list").then((data) => {
          if (data.orders) setOcOrders(data.orders);
        }).catch(() => {});
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [tab, ocDataLoading]);

  React.useEffect(() => {
    if (tab === 'sync') {
      checkSyncStatus();
    }
  }, [tab]);

  const avgRoi = products.length ? Math.round(products.reduce((s, p) => s + (p.roi || 0), 0) / products.length) : 0;
  const goodProducts = products.filter(p => (p.roi || 0) >= 120).length;

  async function calculate(budget) {
    const data = await apiPost("/dashboard/calculate", { budget });
    setSelection(data);
  }

  async function launchAll() {
    const result = await apiPost("/dashboard/launchAll", {});
    alert(`Кампания: ${result.status}, ID: ${result.campaign_id || "n/a"}`);
    const campaignsData = await apiGet("/dashboard/campaigns");
    setCampaigns(campaignsData);
  }

  async function updateProductCosts(sku, cost_price_cash, cost_price_cashless, retail_price, wholesale_price) {
    const updated = await apiPost("/product/update", {
      sku,
      cost_price_cash: Number(cost_price_cash) || 0,
      cost_price_cashless: Number(cost_price_cashless) || 0,
      retail_price: Number(retail_price) || 0,
      wholesale_price: Number(wholesale_price) || 0,
    });
    setProducts((items) => items.map((item) => (item.sku === sku ? updated : item)));
    setCompare(await apiGet("/dashboard/compare"));
  }

  async function importCosts(file) {
    const result = await apiUpload("/product/importCosts", file);
    const [productData, compareData] = await Promise.all([apiGet("/product/list"), apiGet("/dashboard/compare")]);
    setProducts(productData);
    setCompare(compareData);
    alert(`Импортировано: ${result.imported}, пропущено: ${result.skipped}`);
  }

  async function syncWithOpenCart() {
    if (!confirm("Синхронизировать все рассчитанные цены с реальным сайтом stroiapp.ru?")) return;
    setOpenCartLoading(true);
    try {
    const result = await apiGet("/opencart/syncPrices");
      setOpenCartStatus(`Массовая синхронизация: ${result.status}, обновлено: ${result.updated || 0}`);
    alert(`Синхронизация: ${result.status}, обновлено: ${result.updated || 0}`);
    } finally {
      setOpenCartLoading(false);
    }
  }

  async function checkOpenCart() {
    setOpenCartLoading(true);
    try {
      const result = await apiGet("/opencart/health");
      setOpenCartStatus(result.status === "connected" ? `OpenCart подключен, товаров: ${result.products}` : `Ошибка OpenCart: ${result.detail || "нет связи"}`);
    } finally {
      setOpenCartLoading(false);
    }
  }

  // Live Sync functions
  async function startFullSync() {
    setSyncRunning(true);
    setSyncLog([]);
    setSyncLoading(true);
    try {
      const resp = await fetch(`${apiUrl}/sync/full`, { method: "POST" });
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          const text = line.slice(6).trim();
          setSyncLog((prev) => [...prev, text]);
        }
      }
      addToast("Full sync завершен", "success");
    } catch (e) {
      addToast("Ошибка full sync: " + e.message, "error");
    } finally {
      setSyncRunning(false);
      setSyncLoading(false);
    }
  }

  async function startWatchMode() {
    setSyncLoading(true);
    try {
      const result = await apiPost("/sync/watch/start", {});
      if (result.status === "started" || result.status === "already_running") {
        setSyncWatchRunning(true);
        addToast("Watch mode запущен (PID: " + result.pid + ")", "success");
      }
    } catch (e) {
      addToast("Ошибка запуска watch: " + e.message, "error");
    } finally {
      setSyncLoading(false);
    }
  }

  async function stopWatchMode() {
    setSyncLoading(true);
    try {
      await apiPost("/sync/watch/stop", {});
      setSyncWatchRunning(false);
      addToast("Watch mode остановлен", "success");
    } catch (e) {
      addToast("Ошибка остановки watch: " + e.message, "error");
    } finally {
      setSyncLoading(false);
    }
  }

  async function checkSyncStatus() {
    try {
      const result = await apiGet("/sync/status");
      setSyncWatchRunning(result.running);
    } catch (e) {
      // ignore
    }
  }

  async function syncProductWithOpenCart(sku) {
    setOpenCartLoading(true);
    try {
      const result = await apiGet(`/opencart/syncProduct/${encodeURIComponent(sku)}`);
      setOpenCartStatus(`Товар ${sku}: ${result.status}, OpenCart product_id: ${result.opencart?.product_id || "n/a"}`);
      return result;
    } finally {
      setOpenCartLoading(false);
    }
  }

  async function bulkGenerateSEO() {
    setSeoLoading(true);
    try {
      const result = await apiGet("/seo/bulkGenerate");
      setSeoResults(result.results);
      alert(`Сгенерировано SEO для ${result.count} товаров`);
    } finally {
      setSeoLoading(false);
    }
  }

  async function massFixSEO() {
    setSeoLoading(true);
    try {
      const result = await apiPost("/opencart/seo/massFix", {});
      addToast(`Исправлено SEO у ${result.updated} товаров (лимит ${result.limit})`, "success");
    } catch (err) {
      addToast("Ошибка массового SEO: " + (err.message || ""), "error");
    } finally {
      setSeoLoading(false);
    }
  }

  async function loadSeoStats() {
    try {
      const result = await apiGet("/opencart/seo/productStats");
      setSeoStats(result);
    } catch (err) {
      addToast("Ошибка загрузки SEO статистики: " + (err.message || ""), "error");
    }
  }

  async function massFixCategoriesSEO() {
    setSeoLoading(true);
    try {
      const result = await apiPost("/opencart/seo/massFixCategories", {});
      addToast(`Исправлено SEO у ${result.updated} категорий (лимит ${result.limit})`, "success");
    } catch (err) {
      addToast("Ошибка массового SEO категорий: " + (err.message || ""), "error");
    } finally {
      setSeoLoading(false);
    }
  }

  async function generateGeoPages() {
    setGeoPagesLoading(true);
    try {
      const result = await apiPost("/geo/generate-pages", { limit: 50 });
      setGeoPagesResult(result);
      if (result.status === "ok") {
        addToast(`Сгенерировано ${result.total_generated} гео-страниц для ${result.total_products} товаров`, "success");
      } else {
        addToast("Ошибка: " + (result.message || JSON.stringify(result)), "error");
      }
    } catch (err) {
      addToast("Ошибка генерации гео-страниц: " + (err.message || ""), "error");
    } finally {
      setGeoPagesLoading(false);
    }
  }

  async function generateSitemap() {
    setSiteLoading(true);
    try {
      const result = await apiPost("/opencart/site/generateSitemap", {});
      addToast(`Sitemap сгенерирован: ${result.urls} URL (${result.path})`, "success");
    } catch (err) {
      addToast("Ошибка генерации sitemap: " + (err.message || ""), "error");
    } finally {
      setSiteLoading(false);
    }
  }

  async function generateRobots() {
    setSiteLoading(true);
    try {
      const result = await apiPost("/opencart/site/generateRobots", {});
      addToast(`Robots.txt сгенерирован: ${result.lines} строк (${result.path})`, "success");
    } catch (err) {
      addToast("Ошибка генерации robots.txt: " + (err.message || ""), "error");
    } finally {
      setSiteLoading(false);
    }
  }

  async function massFixDescriptions() {
    setOcDataLoading(true);
    try {
      const result = await apiPost("/opencart/product/massFixDescriptions", {});
      addToast(`Исправлено описаний у ${result.updated} товаров (лимит ${result.limit})`, "success");
    } catch (err) {
      addToast("Ошибка массового исправления описаний: " + (err.message || ""), "error");
    } finally {
      setOcDataLoading(false);
    }
  }

  async function findBrokenImages() {
    setSiteLoading(true);
    try {
      const result = await apiGet("/opencart/site/findBrokenImages");
      setSiteImages(result);
      addToast(`Проверка изображений: ${result.broken_count} битых, ${result.unused_count} неиспользуемых`, result.broken_count > 0 || result.unused_count > 0 ? "warning" : "success");
    } catch (err) {
      addToast("Ошибка проверки изображений: " + (err.message || ""), "error");
    } finally {
      setSiteLoading(false);
    }
  }

  async function cleanUnusedImages() {
    setSiteLoading(true);
    try {
      const result = await apiPost("/opencart/site/cleanUnusedImages", {});
      addToast(`Удалено ${result.deleted} неиспользуемых изображений`, "success");
      findBrokenImages();
    } catch (err) {
      addToast("Ошибка очистки изображений: " + (err.message || ""), "error");
    } finally {
      setSiteLoading(false);
    }
  }

  async function bulkRecalcPrices() {
    const markup = window.prompt("Введите наценку в % (например 15 для +15%, -10 для -10%):", "15");
    if (markup === null) return;
    setOcDataLoading(true);
    try {
      const result = await apiPost("/opencart/product/bulkRecalcPrices", { markup: Number(markup), limit: 1000 });
      addToast(`Обновлено ${result.updated} товаров, наценка ${result.markup}%`, "success");
    } catch (err) {
      addToast("Ошибка пересчёта цен: " + (err.message || ""), "error");
    } finally {
      setOcDataLoading(false);
    }
  }

  async function restoreBackup() {
    if (!window.confirm("ВОССТАНОВИТЬ САЙТ ИЗ БЭКАПА?\n\nЭто заменит все файлы и базу данных на последний бэкап. Продолжить?")) return;
    setSiteLoading(true);
    try {
      const result = await apiPost("/opencart/site/restoreBackup", {});
      const zipOk = result.results?.zip?.restored;
      const sqlOk = result.results?.sql?.restored;
      if (zipOk || sqlOk) {
        addToast(`Восстановлено: файлы=${zipOk ? 'OK' : 'FAIL'}, БД=${sqlOk ? 'OK' : 'FAIL'}`, "success");
      } else {
        addToast("Восстановление не удалось. Создайте бэкап через ai_backup_full.php", "error");
      }
    } catch (err) {
      addToast("Ошибка восстановления: " + (err.message || ""), "error");
    } finally {
      setSiteLoading(false);
    }
  }

  async function compareCompetitors() {
    setCompetitorLoading(true);
    try {
      setCompetitorResults(await apiGet("/competitors/compare"));
    } finally {
      setCompetitorLoading(false);
    }
  }

  async function validateInn() {
    if (!innQuery.trim()) return;
    setInnLoading(true);
    try {
      setInnResult(await apiGet(`/lead/validateInn?inn=${encodeURIComponent(innQuery.trim())}`));
    } finally {
      setInnLoading(false);
    }
  }

  async function listOpenCartFiles(path = fileListPath) {
    setFileLoading(true);
    try {
      const result = await apiGet(`/opencart/files/list?path=${encodeURIComponent(path)}`);
      setFileListPath(result.path);
      setFileItems(result.items || []);
      setFileStatus(`Открыта папка: ${result.path}`);
    } finally {
      setFileLoading(false);
    }
  }

  async function readOpenCartFile(path = filePath) {
    setFileLoading(true);
    try {
      const result = await apiGet(`/opencart/files/read?path=${encodeURIComponent(path)}`);
      setFilePath(result.path);
      setFileContent(result.content || "");
      setFileStatus(`Файл открыт: ${result.path}`);
    } finally {
      setFileLoading(false);
    }
  }

  async function writeOpenCartFile() {
    if (!confirm(`Сохранить файл на stroiapp.ru?\n${filePath}`)) return;
    setFileLoading(true);
    try {
      const result = await apiPost("/opencart/files/write", { path: filePath, content: fileContent });
      setFileStatus(`Сохранено. Backup: ${result.backup || "не создан"}`);
      addToast("Файл сохранён на сервере", "success");
    } finally {
      setFileLoading(false);
    }
  }

  async function backupOpenCartFile() {
    setFileLoading(true);
    try {
      const result = await apiPost("/opencart/files/backup", { path: filePath, content: "" });
      setFileStatus(`Backup создан: ${result.backup}`);
    } finally {
      setFileLoading(false);
    }
  }

  async function clearOpenCartCache() {
    setFileLoading(true);
    try {
      const result = await apiPost("/opencart/site/clearCache", {});
      setFileStatus(`Кэш очищен, файлов удалено: ${result.deleted}`);
      addToast(`Кэш очищен: ${result.deleted} файлов`, "success");
    } finally {
      setFileLoading(false);
    }
  }

  async function loadSiteStatus() {
    setSiteLoading(true);
    try {
      const [health, errorLog, backups] = await Promise.all([
        apiGet("/opencart/site/health"),
        apiGet("/opencart/site/errorLog"),
        apiGet("/opencart/site/backups"),
      ]);
      setSiteHealth(health);
      setSiteErrorLog(errorLog.log || "");
      setSiteBackups(backups.backups || []);
      addToast("Диагностика сайта обновлена", "success");
    } catch (err) {
      addToast("Ошибка диагностики: " + (err.message || "неизвестно"), "error");
    } finally {
      setSiteLoading(false);
    }
  }

  async function loadOpenCartData() {
    setOcDataLoading(true);
    try {
      const [categories, orders, customers, products, bannersData, settingsData] = await Promise.all([
        apiGet("/opencart/categories/tree"),
        apiGet("/opencart/orders/list?limit=30&page=1"),
        apiGet("/opencart/customers/list?limit=30&page=1"),
        apiGet("/opencart/products/list?limit=50&page=1"),
        apiGet("/opencart/banners/list"),
        apiGet("/opencart/settings/list"),
      ]);
      setOcCategories(categories.tree || []);
      setOcOrders(orders.orders || []);
      setOcCustomers(customers.customers || []);
      setOcProducts(products.products || []);
      setBanners(bannersData.banners || []);
      setSettings(settingsData.settings || null);
    } finally {
      setOcDataLoading(false);
    }
  }

  async function fetchBannerDetail(banner_id) {
    setBannerLoading(true);
    try {
      const result = await apiGet(`/opencart/banners/${banner_id}`);
      setSelectedBanner(result);
    } finally {
      setBannerLoading(false);
    }
  }

  async function updateBanner(banner_id, fields) {
    setBannerLoading(true);
    try {
      await apiPost("/opencart/banners/update", { banner_id, ...fields });
      setBanners((items) => items.map((b) => (b.banner_id === banner_id ? { ...b, ...fields } : b)));
      if (selectedBanner && selectedBanner.banner && selectedBanner.banner.banner_id === banner_id) {
        setSelectedBanner((prev) => ({ ...prev, banner: { ...prev.banner, ...fields } }));
      }
      addToast("Баннер обновлён", "success");
    } finally {
      setBannerLoading(false);
    }
  }

  async function updateSettings(fields) {
    setSettingsLoading(true);
    try {
      await apiPost("/opencart/settings/update", fields);
      setSettings((prev) => ({ ...prev, ...fields }));
      addToast("Настройки сохранены", "success");
    } finally {
      setSettingsLoading(false);
    }
  }

  async function fetchCategoryDetail(category_id) {
    setCategoryLoading(true);
    try {
      const result = await apiGet(`/opencart/categories/get?category_id=${category_id}`);
      setSelectedCategory(result);
    } finally {
      setCategoryLoading(false);
    }
  }

  async function updateCategory(category_id, fields) {
    setCategoryLoading(true);
    try {
      await apiPost("/opencart/categories/update", { category_id, ...fields });
      setSelectedCategory((prev) => ({ ...prev, ...fields }));
      addToast("Категория обновлена", "success");
    } finally {
      setCategoryLoading(false);
    }
  }

  async function fetchCustomerDetail(customer_id) {
    setCustomerLoading(true);
    try {
      const [detail, orders] = await Promise.all([
        apiGet(`/opencart/customers/${customer_id}`),
        apiGet(`/opencart/customers/${customer_id}/orders`),
      ]);
      setSelectedCustomer(detail);
      setCustomerOrders(orders.orders || []);
    } finally {
      setCustomerLoading(false);
    }
  }

  async function updateCustomerStatus(customer_id, status) {
    setCustomerLoading(true);
    try {
      await apiPost(`/opencart/customers/${customer_id}/status?status=${status}`, {});
      setOcCustomers((items) => items.map((c) => (c.customer_id === customer_id ? { ...c, status: String(status) } : c)));
      if (selectedCustomer && selectedCustomer.customer_id === customer_id) {
        setSelectedCustomer((prev) => ({ ...prev, status: String(status) }));
      }
      addToast("Статус клиента обновлён", "success");
    } finally {
      setCustomerLoading(false);
    }
  }

  async function fetchOcProductDetail(product_id) {
    setOcProductLoading(true);
    try {
      const result = await apiGet(`/opencart/products/${product_id}`);
      setSelectedOcProduct(result);
    } finally {
      setOcProductLoading(false);
    }
  }

  async function updateOcProduct(product_id, fields) {
    setOcProductLoading(true);
    try {
      await apiPost("/opencart/products/update", { product_id, ...fields });
      setOcProducts((items) => items.map((p) => (p.product_id === product_id ? { ...p, ...fields } : p)));
      if (selectedOcProduct && selectedOcProduct.product_id === product_id) {
        setSelectedOcProduct((prev) => ({ ...prev, ...fields }));
      }
      addToast("Товар обновлён", "success");
    } finally {
      setOcProductLoading(false);
    }
  }

  async function fetchOrderDetail(order_id) {
    setOrderDetailLoading(true);
    try {
      const result = await apiGet(`/opencart/orders/${order_id}`);
      setSelectedOrder(result);
    } finally {
      setOrderDetailLoading(false);
    }
  }

  async function updateOrderStatus(order_id, order_status_id) {
    await apiPost("/opencart/orders/status", { order_id, order_status_id });
    setOcOrders((orders) => orders.map((o) => (o.order_id === order_id ? { ...o, order_status_id } : o)));
    if (selectedOrder && selectedOrder.order && selectedOrder.order.order_id === order_id) {
      setSelectedOrder((prev) => ({ ...prev, order: { ...prev.order, order_status_id } }));
    }
    addToast("Статус заказа обновлён", "success");
  }

  async function loadCompetitors() {
    setCompLoading(true);
    try {
      const data = await apiGet("/competitors-bids/list");
      setCompetitorsList(data.competitors || []);
    } catch (err) {
      addToast("Ошибка загрузки конкурентов: " + err.message, "error");
    } finally {
      setCompLoading(false);
    }
  }

  async function addCompetitor() {
    const name = competitorName.trim();
    const url = competitorUrl.trim();
    if (!name) { addToast("Введите название конкурента", "error"); return; }
    try {
      await apiPost("/competitors-bids/add", { name, url });
      setCompetitorName("");
      setCompetitorUrl("");
      addToast("Конкурент добавлен", "success");
      loadCompetitors();
    } catch (err) {
      addToast("Ошибка добавления: " + err.message, "error");
    }
  }

  async function deleteCompetitor(id) {
    if (!confirm("Удалить конкурента?")) return;
    try {
      await apiPost("/competitors-bids/delete/" + id, {});
      addToast("Конкурент удалён", "success");
      loadCompetitors();
    } catch (err) {
      addToast("Ошибка удаления: " + err.message, "error");
    }
  }

  async function scanCompetitor(id) {
    setCompScanning(id);
    try {
      const data = await apiPost("/competitors-bids/scan/" + id, {});
      addToast("Найдено товаров: " + (data.items_found || 0), "success");
      await loadCompetitorProducts(id);
    } catch (err) {
      addToast("Ошибка сканирования: " + err.message, "error");
    } finally {
      setCompScanning(null);
    }
  }

  async function loadCompetitorProducts(id) {
    setCompSelectedId(id);
    setCompLoading(true);
    try {
      const data = await apiGet("/competitors-bids/products/" + id);
      setCompSelectedProducts(data.products || []);
      setCompSelectedStats(data.stats || null);
    } catch (err) {
      addToast("Ошибка загрузки товаров: " + err.message, "error");
    } finally {
      setCompLoading(false);
    }
  }

  async function loadAiRecommendations() {
    setAiRecsLoading(true);
    try {
      const data = await apiGet("/competitors-bids/recommendations?top_n=10");
      setAiRecs(data);
      addToast("AI-рекомендации получены", "success");
    } catch (err) {
      addToast("Ошибка AI-рекомендаций: " + err.message, "error");
    } finally {
      setAiRecsLoading(false);
    }
  }

  async function analyzeKeywordsForProduct(productName) {
    try {
      const data = await apiPost("/competitors-bids/analyze-keywords", { product_name: productName });
      setAiKeywordResult(data);
    } catch (err) {
      addToast("Ошибка анализа ключей: " + err.message, "error");
    }
  }

  async function analyzeBids() {
    setBidsLoading(true);
    try {
      // Берём ключевые слова из названий наших товаров
      const keywords = ocProducts.filter(p => p.name).map(p => p.name).slice(0, 20);
      if (keywords.length === 0) {
        addToast("Сначала загрузите товары из OpenCart", "warning");
        return;
      }
      const data = await apiPost("/competitors-bids/analyze-bids", { keywords });
      setBidsAnalysis(data);
      if (data.status === "no_token") {
        addToast(data.message, "warning");
      } else {
        addToast(`Анализ ставок: ${data.keywords_checked} ключевых слов`, "success");
      }
    } catch (err) {
      addToast("Ошибка анализа ставок: " + err.message, "error");
    } finally {
      setBidsLoading(false);
    }
  }

  async function autoDiscoverCompetitors() {
    const query = discoverQuery.trim();
    if (!query) { addToast("Введите поисковый запрос", "error"); return; }
    setDiscoverLoading(true);
    try {
      const data = await apiPost("/competitors-bids/discover", { query, max_competitors: 5 });
      addToast(`Найдено конкурентов: ${data.found}, добавлено: ${data.added}`, "success");
      loadCompetitors();
      // Показываем товары первого добавленного
      if (data.competitors && data.competitors.length > 0) {
        await loadCompetitorProducts(data.competitors[0].id);
      }
    } catch (err) {
      addToast("Ошибка автопоиска: " + err.message, "error");
    } finally {
      setDiscoverLoading(false);
    }
  }

  async function loadOurProductsAds() {
    setOurProductsAdsLoading(true);
    try {
      const data = await apiGet("/competitors-bids/our-products-ads?limit=20");
      setOurProductsAds(data);
      addToast(`Проверено товаров: ${data.products_checked}, найдено конкурентов: ${data.products_with_competitors}`, "success");
    } catch (err) {
      addToast("Ошибка анализа: " + err.message, "error");
    } finally {
      setOurProductsAdsLoading(false);
    }
  }

  async function addRecommendedCompetitors() {
    try {
      const data = await apiPost("/competitors-bids/add-recommended", {});
      addToast(`Добавлено конкурентов: ${data.total}`, "success");
      loadCompetitors();
    } catch (err) {
      addToast("Ошибка добавления: " + err.message, "error");
    }
  }

  async function loadCompetitorAds(competitorId) {
    setCompSelectedId(competitorId);
    setCompAdsLoading(true);
    try {
      const data = await apiPost(`/competitors-bids/scan-ads/${competitorId}`, {});
      if (data.ads) {
        setCompAds(data.ads);
        addToast(`Найдено объявлений: ${data.ads_found || data.ads.length}`, "success");
        // Загружаем стратегию
        const strategy = await apiGet(`/competitors-bids/ads-strategy/${competitorId}`);
        setCompAdsStrategy(strategy);
      } else {
        addToast("Объявления не найдены", "info");
      }
    } catch (err) {
      addToast("Ошибка сканирования рекламы: " + err.message, "error");
    } finally {
      setCompAdsLoading(false);
    }
  }

  async function scanWithPlaywright(competitorId) {
    setPwScanning(competitorId);
    try {
      const data = await apiPost(`/competitors-bids/scan-playwright/${competitorId}`, {});
      if (data.error) {
        addToast("Ошибка: " + data.error, "error");
      } else if (data.products_found > 0) {
        addToast(`Найдено товаров через браузер: ${data.products_found}`, "success");
        loadCompetitorProducts(competitorId);
      } else {
        addToast("Товаров не найдено (сайт может быть пустым или защищён)", "warning");
      }
    } catch (err) {
      addToast("Ошибка Playwright: " + err.message, "error");
    } finally {
      setPwScanning(null);
    }
  }

  async function scanAnyUrl() {
    if (!pwUrl || !pwUrl.startsWith("http")) {
      addToast("Введите корректный URL (с http:// или https://)", "error");
      return;
    }
    setPwUrlLoading(true);
    try {
      const data = await apiPost("/competitors-bids/scan-url-playwright", { url: pwUrl });
      setPwUrlResult(data);
      addToast(`Найдено товаров: ${data.products_found}`, "success");
    } catch (err) {
      addToast("Ошибка: " + err.message, "error");
    } finally {
      setPwUrlLoading(false);
    }
  }

  async function loadComparison() {
    setCompLoading(true);
    try {
      const data = await apiGet("/competitors-bids/compare");
      setCompComparisons(data.comparisons || []);
      setCompShowCompare(true);
    } catch (err) {
      addToast("Ошибка сравнения: " + err.message, "error");
    } finally {
      setCompLoading(false);
    }
  }

  async function calculateBudget() {
    if (!budgetAmount || budgetAmount <= 0) { addToast("Введите корректный бюджет", "error"); return; }
    setBudgetLoading(true);
    try {
      const data = await apiPost("/budget-roi/calculate", { budget: Number(budgetAmount) });
      setBudgetResults(data);
      addToast(`Подобрано ${data.selected_count || 0} товаров, ROI ${data.estimated_roi}%`, "success");
    } catch (err) {
      addToast("Ошибка расчёта: " + err.message, "error");
    } finally {
      setBudgetLoading(false);
    }
  }

  async function loadForecast() {
    try {
      const data = await apiGet("/budget-roi/forecast?days=30");
      setBudgetForecast(data.forecast || []);
    } catch (err) {
      console.error("loadForecast", err);
    }
  }

  async function findBundles() {
    setPromoLoading(true);
    try {
      const data = await apiPost("/promotions/find-bundles", {});
      setPromoBundles(data.bundles || []);
      addToast("Найдено связок: " + (data.total_found || 0), "success");
    } catch (err) {
      addToast("Ошибка поиска связок: " + err.message, "error");
    } finally {
      setPromoLoading(false);
    }
  }

  async function createPromotion() {
    const name = promoName.trim();
    if (!name) { addToast("Введите название акции", "error"); return; }
    try {
      const data = await apiPost("/promotions/create", { name, discount_pct: Number(promoDiscount), type: "bundle" });
      addToast("Акция создана: " + name, "success");
      setPromoName("");
      loadPromotions();
    } catch (err) {
      addToast("Ошибка создания акции: " + err.message, "error");
    }
  }

  async function loadPromotions() {
    try {
      const data = await apiGet("/promotions/list");
      setPromoList(data.promotions || []);
    } catch (err) {
      console.error("loadPromotions", err);
    }
  }

  async function loadSpecialProducts() {
    setSpecialLoading(true);
    try {
      const data = await apiGet("/opencart/special-prices/all?limit=100");
      setSpecialProducts(data.products || []);
    } catch (err) {
      addToast("Ошибка загрузки акций: " + err.message, "error");
    } finally {
      setSpecialLoading(false);
    }
  }

  async function setProductSpecialPrice() {
    if (!specialSelected || !specialPriceInput) { addToast("Выберите товар и введите акционную цену", "error"); return; }
    const price = parseFloat(specialPriceInput);
    if (isNaN(price) || price <= 0) { addToast("Введите корректную цену", "error"); return; }
    try {
      await apiPost("/opencart/special-prices", { product_id: specialSelected.product_id, special_price: price });
      addToast("Акция установлена: " + specialSelected.name, "success");
      setSpecialSelected(null);
      setSpecialPriceInput("");
      setSpecialSearch("");
      loadSpecialProducts();
    } catch (err) {
      addToast("Ошибка: " + err.message, "error");
    }
  }

  async function removeSpecialPrice(product_id) {
    try {
      await apiDelete(`/opencart/special-prices/${product_id}`);
      addToast("Акция удалена", "success");
      loadSpecialProducts();
    } catch (err) {
      addToast("Ошибка удаления: " + err.message, "error");
    }
  }

  async function searchTenders() {
    setTenderLoading(true);
    try {
      const data = await apiPost("/tenders/search", { region: tenderRegion });
      setTendersList(data.tenders || []);
      addToast("Найдено позиций: " + (data.total_found || 0), "success");
    } catch (err) {
      addToast("Ошибка поиска тендеров: " + err.message, "error");
    } finally {
      setTenderLoading(false);
    }
  }

  async function checkCoverage() {
    if (tendersList.length === 0) { addToast("Сначала найдите тендеры", "error"); return; }
    setTenderLoading(true);
    try {
      const data = await apiPost("/tenders/check-coverage", { items: tendersList });
      setTenderCoverage(data);
      addToast("Покрытие ассортиментом: " + data.coverage_percent + "%", "success");
    } catch (err) {
      addToast("Ошибка проверки покрытия: " + err.message, "error");
    } finally {
      setTenderLoading(false);
    }
  }

  async function submitTender() {
    if (tendersList.length === 0) { addToast("Нет товаров для заявки", "error"); return; }
    try {
      const data = await apiPost("/tenders/submit", { items: tendersList });
      addToast("Заявка подготовлена, итого: " + money(data.total_price), "success");
    } catch (err) {
      addToast("Ошибка подготовки заявки: " + err.message, "error");
    }
  }

  async function parseReviews() {
    setReviewsLoading(true);
    try {
      const data = await apiPost("/reviews/parse-competitors", {});
      setReviewsList(data.reviews || []);
      addToast("Спарсено отзывов: " + (data.negative_count || 0) + " негативных", "success");
    } catch (err) {
      addToast("Ошибка парсинга: " + err.message, "error");
    } finally {
      setReviewsLoading(false);
    }
  }

  async function generateKP() {
    const target = kpTarget.trim();
    if (!target) { addToast("Введите название конкурента", "error"); return; }
    try {
      const data = await apiPost("/reviews/generate-kp", { competitor_name: target, issues: ["Долгая доставка", "Высокие цены", "Нет безналичного расчёта"] });
      setKpText(data.kp_text || "");
      addToast("КП сгенерировано", "success");
    } catch (err) {
      addToast("Ошибка генерации КП: " + err.message, "error");
    }
  }

  async function deepseekChat(prompt, maxTokens = 800) {
    try {
      const data = await apiPost("/ai/deepseek/chat", { prompt, max_tokens: maxTokens, system: "Ты — помощник для строительного магазина в Москве." });
      return data.response || "";
    } catch (err) {
      addToast("DeepSeek error: " + err.message, "error");
      return "";
    }
  }

  async function recognizeSmeta() {
    setSmetaLoading(true);
    try {
      const data = await apiPost("/autosmeta/recognize", {});
      setSmetaItems(data.items || []);
      addToast("Распознано позиций: " + (data.matched_count || 0), "success");
    } catch (err) {
      addToast("Ошибка распознавания: " + err.message, "error");
    } finally {
      setSmetaLoading(false);
    }
  }

  async function generateInvoice() {
    if (smetaItems.length === 0) { addToast("Сначала распознайте смету", "error"); return; }
    try {
      const data = await apiPost("/autosmeta/generate-invoice", { payment_type: smetaPaymentType, items: smetaItems });
      setSmetaInvoice(data);
      addToast("Счёт сгенерирован: " + data.invoice_id + ", итого " + money(data.total), "success");
    } catch (err) {
      addToast("Ошибка генерации счёта: " + err.message, "error");
    }
  }

  async function generateContent() {
    const count = Math.min(Number(contentCount), 20);
    setContentLoading(true);
    try {
      const data = await apiPost("/content-factory/generate-articles", { count });
      setContentArticles(data.generated || []);
      addToast("Сгенерировано статей: " + (data.count || 0), "success");
      loadContentQueue();
    } catch (err) {
      addToast("Ошибка генерации: " + err.message, "error");
    } finally {
      setContentLoading(false);
    }
  }

  async function publishArticle(articleId) {
    try {
      const data = await apiPost("/content-factory/publish", { article_id: articleId });
      addToast("Статья опубликована: " + data.url, "success");
      loadContentQueue();
    } catch (err) {
      addToast("Ошибка публикации: " + err.message, "error");
    }
  }

  async function loadContentQueue() {
    try {
      const data = await apiGet("/content-factory/queue");
      setContentQueue(data.queue || []);
    } catch (err) {
      console.error("loadContentQueue", err);
    }
  }

  async function loadClients() {
    setObjLoading(true);
    try {
      const data = await apiGet("/clients-objects/clients");
      setClientsList(data.clients || []);
    } catch (err) {
      addToast("Ошибка загрузки клиентов: " + err.message, "error");
    } finally {
      setObjLoading(false);
    }
  }

  async function loadObjects() {
    try {
      const data = await apiGet("/clients-objects/objects");
      setObjectsList(data.objects || []);
    } catch (err) {
      console.error("loadObjects", err);
    }
  }

  async function addObject() {
    const name = objName.trim();
    if (!name) { addToast("Введите название объекта", "error"); return; }
    try {
      await apiPost("/clients-objects/add-object", { name, address: objAddress, client_name: objClient, stage: objStage });
      addToast("Объект добавлен", "success");
      setObjName(""); setObjAddress(""); setObjClient("");
      loadObjects();
    } catch (err) {
      addToast("Ошибка добавления: " + err.message, "error");
    }
  }

  async function forecastDemand() {
    try {
      const data = await apiPost("/clients-objects/forecast-demand", { stage: objStage, area: Number(objArea) });
      setObjForecast(data);
      addToast("Прогноз готов: " + (data.forecast?.length || 0) + " позиций", "success");
    } catch (err) {
      addToast("Ошибка прогноза: " + err.message, "error");
    }
  }

  const filteredProducts = products
    .filter((p) => { const v = query.trim().toLowerCase(); return !v || (p.sku || "").toLowerCase().includes(v) || (p.name || "").toLowerCase().includes(v); })
    .sort((a, b) => b.roi - a.roi);

  const sidebarWidth = collapsed ? "w-16" : "w-56";

  if (!authed) {
    return <LoginScreen onSuccess={() => setAuthed(true)} />;
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 bg-grid" style={{ height: "100dvh" }}>
      {/* Sidebar (desktop) */}
      <aside className={`${sidebarWidth} hidden md:flex flex-col border-r border-slate-800 bg-slate-900/80 backdrop-blur transition-all duration-300`}>
        <div className="flex h-16 items-center gap-3 border-b border-slate-800 px-4">
          <Box className="shrink-0 text-emerald-400" size={24} />
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <span className="font-bold tracking-tight block">AI StroiApp</span>
              {selectedCity && (
                <select
                  value={selectedCity.id}
                  onChange={(e) => {
                    const city = geoCities.find(c => c.id === e.target.value);
                    if (city) setSelectedCity(city);
                  }}
                  className="mt-0.5 w-full text-[10px] bg-slate-800 border border-slate-700 rounded px-1 py-0.5 text-slate-300 outline-none cursor-pointer"
                >
                  {geoRegions.map(region => (
                    <optgroup key={region} label={region}>
                      {geoCities.filter(c => c.region === region).map(city => (
                        <option key={city.id} value={city.id}>{city.name}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              )}
            </div>
          )}
        </div>
        <nav className="flex-1 space-y-1 p-2">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${active ? "bg-emerald-500/10 text-emerald-400" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"}`}
              >
                <Icon size={20} />
                {!collapsed && <span>{t.label}</span>}
              </button>
            );
          })}
        </nav>
        <div className="border-t border-slate-800 p-2">
          <button onClick={() => { clearToken(); setAuthed(false); }} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 hover:bg-slate-800">
            <LogOut size={20} />
            {!collapsed && <span>Выйти</span>}
          </button>
          <button onClick={() => setCollapsed((c) => !c)} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 hover:bg-slate-800">
            <Settings size={20} />
            {!collapsed && <span>Свернуть</span>}
          </button>
          {!collapsed && <div className="px-3 pb-1 text-[10px] text-slate-600">v17.09-5</div>}
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileMenu && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm" onClick={() => setMobileMenu(false)} />
          <aside className="absolute left-0 top-0 flex h-full w-72 flex-col border-r border-slate-800 bg-slate-900 shadow-2xl">
            <div className="flex h-16 items-center justify-between border-b border-slate-800 px-4">
              <div className="flex items-center gap-3">
                <Box className="text-emerald-400" size={24} />
                <span className="font-bold tracking-tight">AI StroiApp</span>
              </div>
              <button onClick={() => setMobileMenu(false)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800">
                <X size={20} />
              </button>
            </div>
            {selectedCity && (
              <div className="border-b border-slate-800 p-3">
                <select
                  value={selectedCity.id}
                  onChange={(e) => {
                    const city = geoCities.find(c => c.id === e.target.value);
                    if (city) setSelectedCity(city);
                  }}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-200 outline-none"
                >
                  {geoRegions.map(region => (
                    <optgroup key={region} label={region}>
                      {geoCities.filter(c => c.region === region).map(city => (
                        <option key={city.id} value={city.id}>{city.name}</option>
                      ))}
                    </optgroup>
                  ))}
                </select>
              </div>
            )}
            <nav className="flex-1 space-y-1 overflow-y-auto p-2">
              {TABS.map((t) => {
                const Icon = t.icon;
                const active = tab === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => { setTab(t.id); setMobileMenu(false); }}
                    className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-colors ${active ? "bg-emerald-500/10 text-emerald-400" : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"}`}
                  >
                    <Icon size={20} />
                    <span>{t.label}</span>
                  </button>
                );
              })}
            </nav>
            <div className="border-t border-slate-800 p-2">
              <button onClick={() => { clearToken(); setAuthed(false); }} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-slate-400 hover:bg-slate-800">
                <LogOut size={20} />
                <span>Выйти</span>
              </button>
            </div>
          </aside>
        </div>
      )}

      {/* Main */}
      <main ref={mainRef} className="flex-1 overflow-auto">
        {/* Top bar */}
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between gap-2 border-b border-slate-800 bg-slate-950/80 px-3 backdrop-blur md:px-6">
          <div className="flex items-center gap-2 md:gap-4">
            <button onClick={() => setMobileMenu(true)} className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 md:hidden">
              <Menu size={22} />
            </button>
            <h1 className="truncate text-base font-bold md:text-lg">{TABS.find((t) => t.id === tab)?.label}</h1>
          </div>
          <div className="hidden flex-1 items-center justify-center px-8 md:flex">
            <div className="relative w-full max-w-md">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Поиск по товарам, заказам, клиентам..."
                className="w-full rounded-lg border border-slate-700 bg-slate-900/50 py-2 pl-10 pr-4 text-sm outline-none focus:border-emerald-500"
                onChange={(e) => {
                  const v = e.target.value.trim().toLowerCase();
                  if (!v) return;
                  // Автопереключение на нужную вкладку по результатам
                  const hasProduct = products.some(p => p.name.toLowerCase().includes(v) || p.sku.toLowerCase().includes(v));
                  if (hasProduct) { setTab('products'); setQuery(v); return; }
                  const hasOrder = ocOrders.some(o => o.firstname?.toLowerCase().includes(v) || o.lastname?.toLowerCase().includes(v) || String(o.order_id).includes(v));
                  if (hasOrder) { setTab('opencart'); return; }
                  const hasCustomer = ocCustomers.some(c => c.firstname?.toLowerCase().includes(v) || c.lastname?.toLowerCase().includes(v) || c.email?.toLowerCase().includes(v));
                  if (hasCustomer) { setTab('opencart'); return; }
                }}
              />
            </div>
          </div>
          <div className="flex items-center gap-2 md:gap-3">
            <button onClick={syncWithOpenCart} className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium hover:bg-slate-700">
              <ShieldCheck size={16} /> <span className="hidden sm:inline">OpenCart</span>
            </button>
            <button onClick={launchAll} className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-3 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">
              <Rocket size={16} /> <span className="hidden sm:inline">Запустить</span>
            </button>
          </div>
        </header>

        <div className="p-3 pb-24 md:p-6 md:pb-6">
          {/* DASHBOARD */}
          {tab === "dashboard" && (
            <div className="space-y-6">
              {/* KPI */}
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
                <KpiCard icon={Package} label="Товаров" value={products.length.toString()} color="text-emerald-400" />
                <KpiCard icon={TrendingUp} label="Средний ROI" value={`${avgRoi}%`} color={avgRoi >= 120 ? "text-emerald-400" : "text-amber-400"} />
                <KpiCard icon={Target} label="Топ товаров" value={goodProducts.toString()} color="text-emerald-400" />
                <KpiCard icon={BarChart3} label="Кампаний" value={campaigns.length.toString()} color="text-sky-400" />
              </div>

              {/* Charts */}
              <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                  <h2 className="mb-4 text-lg font-bold">Топ 10 товаров по ROI</h2>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={products.slice(0, 10).map((p, i) => ({ name: p.name.substring(0, 15), roi: Math.round(p.roi || 0), fill: (p.roi || 0) >= 120 ? '#34d399' : '#f59e0b' }))} layout="vertical">
                        <XAxis type="number" stroke="#64748b" fontSize={12} />
                        <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} width={120} />
                        <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} itemStyle={{ color: '#e2e8f0' }} />
                        <Bar dataKey="roi" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                  <h2 className="mb-4 text-lg font-bold">Распределение по ROI</h2>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={[
                          { name: 'ROI ≥ 120%', value: products.filter(p => (p.roi || 0) >= 120).length, color: '#34d399' },
                          { name: 'ROI 80-120%', value: products.filter(p => { const r = p.roi || 0; return r >= 80 && r < 120; }).length, color: '#f59e0b' },
                          { name: 'ROI < 80%', value: products.filter(p => (p.roi || 0) < 80).length, color: '#ef4444' },
                        ]} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={5} dataKey="value">
                          {[
                            { name: 'ROI ≥ 120%', value: products.filter(p => (p.roi || 0) >= 120).length, color: '#34d399' },
                            { name: 'ROI 80-120%', value: products.filter(p => { const r = p.roi || 0; return r >= 80 && r < 120; }).length, color: '#f59e0b' },
                            { name: 'ROI < 80%', value: products.filter(p => (p.roi || 0) < 80).length, color: '#ef4444' },
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} itemStyle={{ color: '#e2e8f0' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="mt-2 flex justify-center gap-4 text-xs">
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-400"></span> ROI ≥ 120%</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-400"></span> 80-120%</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-400"></span> &lt; 80%</span>
                  </div>
                </div>
              </div>

              {/* Budget + Compare */}
              <div className="grid gap-6 lg:grid-cols-3">
                <div className="col-span-2 space-y-4 rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                  <h2 className="text-lg font-bold">Быстрый выбор бюджета</h2>
                  <div className="flex flex-wrap gap-2">
                    {budgets.map((b) => (
                      <button key={b} onClick={() => calculate(b)} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold hover:bg-emerald-500 hover:text-slate-950">{money(b)}</button>
                    ))}
                  </div>
                  {selection && (
                    <div className="rounded-xl bg-slate-950 p-4 text-sm">
                      <div className="grid grid-cols-4 gap-4">
                        <div><div className="text-slate-400">Товаров</div><div className="text-lg font-bold">{selection.products.length}</div></div>
                        <div><div className="text-slate-400">Расход</div><div className="text-lg font-bold text-amber-400">{money(selection.spent)}</div></div>
                        <div><div className="text-slate-400">Сохранено</div><div className="text-lg font-bold text-emerald-400">{money(selection.saved)}</div></div>
                        <div><div className="text-slate-400">Прибыль</div><div className="text-lg font-bold text-emerald-400">{money(selection.expected_profit)}</div></div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                  <h2 className="mb-4 text-lg font-bold">Бюджеты</h2>
                  {loading ? <div className="text-slate-400">Загрузка...</div> : (
                    <div className="space-y-3">
                      {compare.map((c) => (
                        <div key={c.budget} className="flex items-center justify-between rounded-lg bg-slate-950 p-3">
                          <div><div className="font-semibold">{money(c.budget)}</div><div className="text-xs text-slate-400">{money(c.spent)} / {money(c.saved)}</div></div>
                          <div className="text-right"><div className="text-emerald-400 font-bold">{money(c.expected_profit)}</div></div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* PRODUCTS */}
          {tab === "products" && (
            <ProductsTreePanel
              catTree={catTree} setCatTree={setCatTree}
              catProducts={catProducts} setCatProducts={setCatProducts}
              selCatId={selCatId} setSelCatId={setSelCatId}
              selProduct={selProduct} setSelProduct={setSelProduct}
              prodSearch={prodSearch} setProdSearch={setProdSearch}
              catLoading={catLoading} setCatLoading={setCatLoading}
              addToast={addToast}
            />
          )}

          {/* CAMPAIGNS */}
          {tab === "campaigns" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Yandex Direct</h2>
                <p className="mb-4 text-sm text-slate-400">Запуск кампаний для товаров с ROI ≥ 120%. Авто-создание объявлений и ключевых слов.</p>
                <button onClick={launchAll} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400"><Rocket size={16} className="inline mr-2" />Запустить кампанию</button>
              </div>
              {campaigns.length > 0 && (
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                  <h2 className="mb-4 text-lg font-bold">Кампании</h2>
                  <div className="overflow-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-slate-400"><tr><th className="pb-2">ID</th><th>Название</th><th>Статус</th></tr></thead>
                      <tbody>
                        {campaigns.map((c) => (
                          <tr key={c.Id} className="border-t border-slate-800"><td className="py-3 font-mono">{c.Id}</td><td>{c.Name}</td><td><span className="rounded bg-emerald-500/10 px-2 py-1 text-xs text-emerald-400">{c.Status}</span></td></tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SEO */}
          {tab === "seo" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">SEO-автоматизация</h2>
                <p className="mb-4 text-sm text-slate-400">Генерация описаний и мета-тегов через DeepSeek AI для товаров с ROI ≥ 120%.</p>
                <button onClick={bulkGenerateSEO} disabled={seoLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{seoLoading ? "Генерация..." : "Сгенерировать SEO"}</button>
              </div>
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Массовое исправление SEO</h2>
                <p className="mb-4 text-sm text-slate-400">Автоматически заполнить пустые meta_title, meta_description и meta_keyword у товаров на сайте stroiapp.ru.</p>
                <button onClick={massFixSEO} disabled={seoLoading} className="btn-shine rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 glow-emerald">{seoLoading ? "Исправление..." : "Исправить пустые SEO"}</button>
              </div>
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Статистика SEO товаров</h2>
                <p className="mb-4 text-sm text-slate-400">Сколько товаров имеют заполненные meta-теги, а сколько — нет.</p>
                <div className="mb-4 flex gap-2">
                  <button onClick={loadSeoStats} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium hover:bg-slate-700">Обновить статистику</button>
                </div>
                {seoStats && (
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="rounded-xl bg-slate-950 p-4 text-center">
                      <div className="text-2xl font-bold text-emerald-400">{seoStats.total}</div>
                      <div className="text-slate-500">Всего товаров</div>
                    </div>
                    <div className="rounded-xl bg-slate-950 p-4 text-center">
                      <div className="text-2xl font-bold text-emerald-400">{seoStats.with_meta}</div>
                      <div className="text-slate-500">С SEO</div>
                    </div>
                    <div className="rounded-xl bg-slate-950 p-4 text-center">
                      <div className="text-2xl font-bold text-amber-400">{seoStats.without_meta}</div>
                      <div className="text-slate-500">Без SEO</div>
                    </div>
                  </div>
                )}
              </div>
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Массовое SEO категорий</h2>
                <p className="mb-4 text-sm text-slate-400">Автоматически заполнить пустые meta-теги у категорий на сайте stroiapp.ru.</p>
                <button onClick={massFixCategoriesSEO} disabled={seoLoading} className="btn-shine rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 glow-emerald">{seoLoading ? "Исправление..." : "Исправить SEO категорий"}</button>
              </div>
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Гео-страницы (215+ городов и районов)</h2>
                <p className="mb-4 text-sm text-slate-400">Сгенерировать уникальные SEO-страницы для каждого товара под все районы Москвы и города МО. Каждая партия: 50 товаров × 215+ городов = ~10750 страниц. Это даст максимальный геотрафик из Москвы и области.</p>
                <button onClick={generateGeoPages} disabled={geoPagesLoading} className="btn-shine rounded-lg bg-indigo-500 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-400 disabled:opacity-50 glow-indigo">{geoPagesLoading ? "Генерация..." : "Сгенерировать гео-страницы (50 товаров)"}</button>
                {geoPagesResult && (
                  <div className="mt-4 rounded-xl bg-slate-950 p-4 text-sm">
                    <div className="grid grid-cols-3 gap-3 text-center">
                      <div>
                        <div className="text-xl font-bold text-emerald-400">{geoPagesResult.total_products}</div>
                        <div className="text-slate-500">Товаров</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-indigo-400">{geoPagesResult.total_generated}</div>
                        <div className="text-slate-500">Гео-страниц</div>
                      </div>
                      <div>
                        <div className="text-xl font-bold text-amber-400">{geoPagesResult.total_errors || 0}</div>
                        <div className="text-slate-500">Ошибок</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              {seoResults.length > 0 && (
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                  <h2 className="mb-4 text-lg font-bold">Результаты ({seoResults.length})</h2>
                  <div className="max-h-[500px] overflow-auto space-y-3">
                    {seoResults.map((r) => (
                      <div key={r.sku} className="rounded-xl bg-slate-950 p-4">
                        <div className="mb-1 font-mono text-xs text-slate-400">{r.sku}</div>
                        <div className="mb-1 font-semibold text-emerald-400">{r.title}</div>
                        <div className="text-sm text-slate-300">{r.description}</div>
                        <div className="mt-2 text-xs text-slate-500">{r.keywords}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* COMPETITORS */}
          {tab === "competitors" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Анализ конкурентов</h2>
                <p className="mb-4 text-sm text-slate-400">Сравнение цен с конкурентами.</p>
                <button onClick={compareCompetitors} disabled={competitorLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{competitorLoading ? "Анализ..." : "Сравнить"}</button>
              </div>
              {competitorResults.length > 0 && (
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                  <div className="overflow-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="text-slate-400"><tr><th className="pb-2">SKU</th><th>Конкурент</th><th>Наша</th><th>Их</th><th>Разница</th></tr></thead>
                      <tbody>
                        {competitorResults.map((r) => (
                          <tr key={r.sku + r.competitor_name} className="border-t border-slate-800">
                            <td className="py-3 font-mono">{r.sku}</td>
                            <td>{r.competitor_name}</td>
                            <td>{money(r.our_price)}</td>
                            <td>{money(r.competitor_price)}</td>
                            <td className={r.diff > 0 ? "text-emerald-400" : "text-red-400"}>{r.diff > 0 ? "+" : ""}{r.diff_pct}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* OPENCART */}
          {tab === "opencart" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold">Управление OpenCart</h2>
                    <p className="text-sm text-slate-400">Категории, последние заказы и клиенты с сайта stroiapp.ru.</p>
                  </div>
                  <button onClick={loadOpenCartData} disabled={ocDataLoading} className="btn-shine rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 glow-emerald">
                    {ocDataLoading ? "Загрузка..." : "Загрузить данные"}
                  </button>
                </div>
              </div>
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Массовое исправление описаний</h2>
                <p className="mb-4 text-sm text-slate-400">Автоматически заполнить пустые description у товаров на сайте stroiapp.ru.</p>
                <button onClick={massFixDescriptions} disabled={ocDataLoading} className="btn-shine rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 glow-emerald">{ocDataLoading ? "Исправление..." : "Исправить описания"}</button>
              </div>
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <h2 className="mb-2 text-lg font-bold">Массовый пересчёт цен</h2>
                <p className="mb-4 text-sm text-slate-400">Повысить или понизить все цены на stroiapp.ru на заданный % (например +15% или -10%).</p>
                <button onClick={bulkRecalcPrices} disabled={ocDataLoading} className="btn-shine rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 glow-emerald">{ocDataLoading ? "Пересчёт..." : "Пересчитать цены"}</button>
              </div>
              <div className="grid gap-6 xl:grid-cols-3">
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><Package size={18} className="text-emerald-400" /> Товары</h3>
                  <div className="mb-3 flex gap-2">
                    <input value={ocProductQuery} onChange={(e) => setOcProductQuery(e.target.value)} placeholder="Поиск по названию..." className="min-w-0 flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                  </div>
                  <div className="max-h-[520px] space-y-2 overflow-auto text-sm">
                    {ocProducts.filter((p) => { const v = ocProductQuery.trim().toLowerCase(); return !v || (p.name || "").toLowerCase().includes(v) || (p.model || "").toLowerCase().includes(v); }).map((product) => {
                      const isOpen = selectedOcProduct && selectedOcProduct.product_id === product.product_id;
                      return (
                        <div key={product.product_id}>
                          <button onClick={() => fetchOcProductDetail(product.product_id)} className="w-full rounded-xl bg-slate-950 p-3 text-left hover:bg-slate-900">
                            <div className="flex justify-between gap-2"><span className="truncate font-medium">{product.name || "Без названия"}</span><span className="shrink-0 text-slate-400">{money(Number(product.price || 0))}</span></div>
                            <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                              <span>ID: {product.product_id} | Модель: {product.model || "—"} | Остаток: {product.quantity || 0}</span>
                              <span className={`badge ${product.status === '1' ? 'badge-active' : 'badge-inactive'}`}><span className="badge-dot"></span>{product.status === '1' ? 'Вкл' : 'Выкл'}</span>
                            </div>
                          </button>
                          {isOpen && (
                            <div className="mt-2 rounded-xl border border-slate-800 bg-slate-950 p-4">
                              {ocProductLoading ? <div className="text-sm text-slate-500">Загрузка...</div> : (
                                <div className="space-y-3 text-sm">
                                  <div className="font-semibold">{selectedOcProduct.name}</div>
                                  <div className="grid grid-cols-2 gap-2">
                                    <div><span className="text-slate-500">Цена:</span> <input type="number" value={selectedOcProduct.price || 0} onChange={(e) => updateOcProduct(product.product_id, { price: Number(e.target.value) })} className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                    <div><span className="text-slate-500">Нал:</span> <input type="number" value={selectedOcProduct.cash_price || 0} onChange={(e) => updateOcProduct(product.product_id, { cash_price: Number(e.target.value) })} className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                    <div><span className="text-slate-500">Безнал:</span> <input type="number" value={selectedOcProduct.non_cash_price || 0} onChange={(e) => updateOcProduct(product.product_id, { non_cash_price: Number(e.target.value) })} className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                    <div><span className="text-slate-500">Кол-во:</span> <input type="number" value={selectedOcProduct.quantity || 0} onChange={(e) => updateOcProduct(product.product_id, { quantity: Number(e.target.value) })} className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                  </div>
                                  <div><span className="text-slate-500">Статус:</span>
                                    <select value={selectedOcProduct.status || 0} onChange={(e) => updateOcProduct(product.product_id, { status: Number(e.target.value) })} className="ml-2 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none">
                                      <option value={0}>Отключен</option>
                                      <option value={1}>Включен</option>
                                    </select>
                                  </div>
                                  <div className="border-t border-slate-800 pt-2">
                                    <div className="mb-1 font-semibold text-slate-400">SEO</div>
                                    <div className="space-y-1">
                                      <div><span className="text-slate-500">Meta Title:</span> <input value={selectedOcProduct.meta_title || ''} onChange={(e) => updateOcProduct(product.product_id, { meta_title: e.target.value })} className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                      <div><span className="text-slate-500">Meta Desc:</span> <input value={selectedOcProduct.meta_description || ''} onChange={(e) => updateOcProduct(product.product_id, { meta_description: e.target.value })} className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                      <div><span className="text-slate-500">Keywords:</span> <input value={selectedOcProduct.meta_keyword || ''} onChange={(e) => updateOcProduct(product.product_id, { meta_keyword: e.target.value })} className="w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {!ocProducts.length && <div className="text-slate-500">Нажми «Загрузить данные»</div>}
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><Folder size={18} className="text-amber-400" /> Категории</h3>
                  <div className="max-h-[520px] space-y-2 overflow-auto text-sm">
                    {ocCategories.map((category) => (
                      <CategoryNode key={category.category_id} node={category} onSelect={fetchCategoryDetail} selectedId={selectedCategory?.category_id} />
                    ))}
                    {!ocCategories.length && <div className="text-slate-500">Нажми «Загрузить данные»</div>}
                  </div>
                  {selectedCategory && (
                    <div className="mt-3 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm">
                      {categoryLoading ? <div className="text-slate-500">Загрузка...</div> : (
                        <div className="space-y-2">
                          <div className="font-semibold">Редактировать категорию #{selectedCategory.category_id}</div>
                          <div><span className="text-slate-500">Название:</span> <input value={selectedCategory.name || ''} onChange={(e) => updateCategory(selectedCategory.category_id, { name: e.target.value })} className="ml-2 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                          <div><span className="text-slate-500">Meta Title:</span> <input value={selectedCategory.meta_title || ''} onChange={(e) => updateCategory(selectedCategory.category_id, { meta_title: e.target.value })} className="ml-2 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                          <div><span className="text-slate-500">Meta Desc:</span> <input value={selectedCategory.meta_description || ''} onChange={(e) => updateCategory(selectedCategory.category_id, { meta_description: e.target.value })} className="ml-2 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                          <div><span className="text-slate-500">Meta Keywords:</span> <input value={selectedCategory.meta_keyword || ''} onChange={(e) => updateCategory(selectedCategory.category_id, { meta_keyword: e.target.value })} className="ml-2 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                          <div><span className="text-slate-500">Статус:</span>
                            <select value={selectedCategory.status || 0} onChange={(e) => updateCategory(selectedCategory.category_id, { status: Number(e.target.value) })} className="ml-2 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none">
                              <option value={0}>Отключена</option>
                              <option value={1}>Включена</option>
                            </select>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><ShoppingCart size={18} className="text-emerald-400" /> Заказы</h3>
                  <div className="max-h-[520px] space-y-3 overflow-auto">
                    {ocOrders.map((order) => {
                      const isOpen = selectedOrder && selectedOrder.order && selectedOrder.order.order_id === order.order_id;
                      return (
                        <div key={order.order_id}>
                          <button onClick={() => fetchOrderDetail(order.order_id)} className="w-full rounded-xl bg-slate-950 p-3 text-left text-sm hover:bg-slate-900">
                            <div className="flex justify-between gap-3"><span className="font-mono text-emerald-400">#{order.order_id}</span><span>{money(Number(order.total || 0))}</span></div>
                            <div className="mt-1 text-slate-300">{order.firstname} {order.lastname}</div>
                            <div className="text-xs text-slate-500">{order.telephone || order.email}</div>
                            <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                              <span>{order.date_added}</span>
                              <span className={`badge ${order.order_status_id === '5' ? 'badge-active' : (order.order_status_id === '0' ? 'badge-inactive' : 'badge-inactive')}`}>
                                <span className="badge-dot"></span>
                                {order.order_status_id === '0' ? 'Отменён' : order.order_status_id === '1' ? 'В обработке' : order.order_status_id === '2' ? 'Обработан' : order.order_status_id === '3' ? 'Отправлен' : order.order_status_id === '5' ? 'Завершён' : order.order_status_id === '7' ? 'Ожидание' : order.order_status_id === '8' ? 'Отказ' : order.order_status_id === '15' ? 'Принят' : order.order_status_id === '16' ? 'Отменён' : 'Статус ' + order.order_status_id}
                              </span>
                            </div>
                          </button>
                          {isOpen && (
                            <div className="mt-2 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm">
                              {orderDetailLoading ? <div className="text-slate-500">Загрузка...</div> : (
                                <>
                                  <div className="mb-3 flex flex-wrap items-center gap-2">
                                    <span className="text-slate-400">Статус:</span>
                                    <select
                                      value={selectedOrder.order.order_status_id || 0}
                                      onChange={(e) => updateOrderStatus(order.order_id, Number(e.target.value))}
                                      className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none"
                                    >
                                      <option value={0}>Отменён</option>
                                      <option value={1}>В обработке</option>
                                      <option value={2}>Обработан</option>
                                      <option value={3}>Отправлен</option>
                                      <option value={5}>Завершён</option>
                                      <option value={7}>Ожидание</option>
                                      <option value={8}>Отказ</option>
                                      <option value={9}>Возврат</option>
                                      <option value={10}>Ошибка</option>
                                      <option value={15}>Принят</option>
                                      <option value={16}>Отменён (покупателем)</option>
                                    </select>
                                  </div>
                                  <div className="mb-2 text-slate-400">Email: {selectedOrder.order.email}</div>
                                  <div className="mb-2 text-slate-400">Телефон: {selectedOrder.order.telephone}</div>
                                  <div className="mb-2 text-slate-400">Адрес: {selectedOrder.order.payment_city}, {selectedOrder.order.payment_address_1}</div>
                                  <div className="mb-2 text-slate-400">Комментарий: {selectedOrder.order.comment || "—"}</div>
                                  <div className="mt-3 font-bold text-slate-300">Товары:</div>
                                  <div className="mt-1 space-y-1">
                                    {(selectedOrder.products || []).map((p) => (
                                      <div key={p.order_product_id} className="flex justify-between text-xs">
                                        <span className="truncate">{p.name}</span>
                                        <span className="text-slate-400">{p.quantity} × {money(Number(p.price || 0))}</span>
                                      </div>
                                    ))}
                                  </div>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {!ocOrders.length && <div className="text-sm text-slate-500">Нажми «Загрузить данные»</div>}
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><Users size={18} className="text-sky-400" /> Клиенты</h3>
                  <div className="max-h-[520px] space-y-3 overflow-auto">
                    {ocCustomers.map((customer) => {
                      const isOpen = selectedCustomer && selectedCustomer.customer_id === customer.customer_id;
                      return (
                        <div key={customer.customer_id}>
                          <button onClick={() => fetchCustomerDetail(customer.customer_id)} className="w-full rounded-xl bg-slate-950 p-3 text-left text-sm hover:bg-slate-900">
                            <div className="flex justify-between gap-2">
                              <span className="font-semibold">{customer.firstname} {customer.lastname}</span>
                              <span className={`shrink-0 text-xs ${customer.status === '1' ? 'text-emerald-400' : 'text-slate-500'}`}>{customer.status === '1' ? 'Активен' : 'Отключён'}</span>
                            </div>
                            <div className="text-xs text-slate-400">{customer.email}</div>
                            <div className="text-xs text-slate-500">{customer.telephone}</div>
                          </button>
                          {isOpen && (
                            <div className="mt-2 rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm">
                              {customerLoading ? <div className="text-slate-500">Загрузка...</div> : (
                                <div className="space-y-2">
                                  <div className="font-semibold">Клиент #{selectedCustomer.customer_id}</div>
                                  <div className="text-slate-400">Email: {selectedCustomer.email}</div>
                                  <div className="text-slate-400">Телефон: {selectedCustomer.telephone}</div>
                                  <div className="text-slate-400">Дата регистрации: {selectedCustomer.date_added}</div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-slate-500">Статус:</span>
                                    <select value={selectedCustomer.status || 0} onChange={(e) => updateCustomerStatus(customer.customer_id, Number(e.target.value))} className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none">
                                      <option value={0}>Отключён</option>
                                      <option value={1}>Активен</option>
                                    </select>
                                  </div>
                                  {customerOrders.length > 0 && (
                                    <div className="border-t border-slate-800 pt-2">
                                      <div className="mb-2 font-semibold text-slate-400">История заказов ({customerOrders.length})</div>
                                      <div className="max-h-32 space-y-1 overflow-auto">
                                        {customerOrders.map((o) => (
                                          <div key={o.order_id} className="flex justify-between rounded bg-slate-900 px-2 py-1 text-xs">
                                            <span className="font-mono text-emerald-400">#{o.order_id}</span>
                                            <span>{money(Number(o.total || 0))}</span>
                                            <span className="text-slate-500">{o.date_added?.split(' ')[0]}</span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {!ocCustomers.length && <div className="text-sm text-slate-500">Нажми «Загрузить данные»</div>}
                  </div>
                </div>
              </div>
              <div className="grid gap-6 xl:grid-cols-3">
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><Image size={18} className="text-pink-400" /> Баннеры</h3>
                  <div className="max-h-[520px] space-y-2 overflow-auto text-sm">
                    {banners.map((banner) => {
                      const isOpen = selectedBanner && selectedBanner.banner && selectedBanner.banner.banner_id === banner.banner_id;
                      return (
                        <div key={banner.banner_id}>
                          <button onClick={() => fetchBannerDetail(banner.banner_id)} className="w-full rounded-xl bg-slate-950 p-3 text-left hover:bg-slate-900">
                            <div className="flex justify-between gap-2"><span className="truncate font-medium">{banner.name}</span><span className={`shrink-0 text-xs ${banner.status === '1' ? 'text-emerald-400' : 'text-slate-500'}`}>{banner.status === '1' ? 'Вкл' : 'Выкл'}</span></div>
                          </button>
                          {isOpen && (
                            <div className="mt-2 rounded-xl border border-slate-800 bg-slate-950 p-4">
                              {bannerLoading ? <div className="text-sm text-slate-500">Загрузка...</div> : (
                                <div className="space-y-3 text-sm">
                                  <div><span className="text-slate-500">Название:</span> <input value={selectedBanner.banner.name || ''} onChange={(e) => updateBanner(banner.banner_id, { name: e.target.value })} className="ml-2 w-full rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none" /></div>
                                  <div><span className="text-slate-500">Статус:</span>
                                    <select value={selectedBanner.banner.status || 0} onChange={(e) => updateBanner(banner.banner_id, { status: Number(e.target.value) })} className="ml-2 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-sm outline-none">
                                      <option value={0}>Отключен</option>
                                      <option value={1}>Включен</option>
                                    </select>
                                  </div>
                                  <div className="mt-2 font-semibold text-slate-300">Изображения:</div>
                                  <div className="mt-1 space-y-1">
                                    {(selectedBanner.images || []).map((img) => (
                                      <div key={img.banner_image_id} className="rounded bg-slate-900 p-2 text-xs">
                                        <div className="truncate font-medium">{img.title || '—'}</div>
                                        <div className="text-slate-500">{img.link || '—'}</div>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {!banners.length && <div className="text-slate-500">Нажми «Загрузить данные»</div>}
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5 xl:col-span-2">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><Settings size={18} className="text-slate-300" /> Настройки магазина</h3>
                  {settings ? (
                    <div className="grid gap-3 text-sm sm:grid-cols-2">
                      {[
                        { key: 'config_name', label: 'Название магазина' },
                        { key: 'config_owner', label: 'Владелец' },
                        { key: 'config_email', label: 'Email' },
                        { key: 'config_telephone', label: 'Телефон' },
                        { key: 'config_address', label: 'Адрес' },
                        { key: 'config_meta_title', label: 'Meta Title' },
                        { key: 'config_meta_description', label: 'Meta Description' },
                        { key: 'config_meta_keyword', label: 'Meta Keywords' },
                      ].map((field) => (
                        <div key={field.key}>
                          <span className="text-slate-500">{field.label}:</span>
                          <input
                            value={settings[field.key] || ''}
                            onChange={(e) => updateSettings({ [field.key]: e.target.value })}
                            className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm outline-none focus:border-emerald-500"
                          />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-slate-500">Нажми «Загрузить данные»</div>
                  )}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                <h3 className="mb-4 flex items-center gap-2 font-bold"><Image size={18} className="text-pink-400" /> Загрузка фото</h3>
                <div className="text-sm text-slate-400">
                  <p className="mb-3">Загрузить изображение на stroiapp.ru. Файл сохранится в catalog/ через API.</p>
                  <div className="flex flex-wrap items-center gap-3">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        try {
                          const result = await apiUpload("/opencart/images/upload", file);
                          addToast(`Фото загружено: ${result.path || file.name}`, "success");
                          e.target.value = "";
                        } catch (err) {
                          addToast("Ошибка загрузки: " + (err.message || "неизвестно"), "error");
                        }
                      }}
                      className="text-sm file:rounded-lg file:border-0 file:bg-emerald-500 file:px-4 file:py-2 file:text-sm file:font-bold file:text-slate-950 hover:file:bg-emerald-400"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* FILES */}
          {tab === "files" && (
            <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
                  <h2 className="mb-2 font-bold">Файлы OpenCart</h2>
                  <p className="mb-3 text-sm text-slate-400">Редактирование файлов сайта через единый API. Перед сохранением создаётся backup.</p>
                  <div className="flex gap-2">
                    <input value={fileListPath} onChange={(e) => setFileListPath(e.target.value)} className="min-w-0 flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <button onClick={() => listOpenCartFiles()} disabled={fileLoading} className="rounded bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700 disabled:opacity-50">Открыть</button>
                  </div>
                </div>
                <div className="max-h-[calc(100dvh-280px)] overflow-auto rounded-2xl border border-slate-700/30 glass glass-hover p-2 pb-20 md:pb-2">
                  {fileItems.map((item) => {
                    const next = `${fileListPath.replace(/\/?$/, "/")}${item.name}`;
                    return (
                      <button key={item.name} onClick={() => item.type === "directory" ? listOpenCartFiles(`${next}/`) : readOpenCartFile(next)} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-800">
                        {item.type === "directory" ? <Folder size={16} className="text-amber-400" /> : <FileText size={16} className="text-sky-400" />}
                        <span className="truncate">{item.name}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
              <div className="space-y-4">
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <input value={filePath} onChange={(e) => setFilePath(e.target.value)} className="min-w-[260px] flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <button onClick={() => readOpenCartFile()} disabled={fileLoading} className="rounded bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700 disabled:opacity-50">Читать</button>
                    <button onClick={backupOpenCartFile} disabled={fileLoading} className="rounded bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700 disabled:opacity-50">Backup</button>
                    <button onClick={writeOpenCartFile} disabled={fileLoading} className="inline-flex items-center gap-2 rounded bg-emerald-500 px-3 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"><Save size={16} /> Сохранить</button>
                    <button onClick={clearOpenCartCache} disabled={fileLoading} className="rounded bg-amber-500 px-3 py-2 text-sm font-bold text-slate-950 hover:bg-amber-400 disabled:opacity-50">Кэш</button>
                  </div>
                  {fileStatus && <div className="text-sm text-emerald-400">{fileStatus}</div>}
                </div>
                <textarea value={fileContent} onChange={(e) => setFileContent(e.target.value)} spellCheck={false} className="h-[calc(100vh-250px)] w-full rounded-2xl border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-slate-100 outline-none focus:border-emerald-500" />
              </div>
            </div>
          )}

          {/* SITE */}
          {tab === "site" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold">Безопасное управление stroiapp.ru</h2>
                    <p className="text-sm text-slate-400">Health, ошибки PHP/OpenCart, кэш, backups и быстрый переход к редактированию файлов.</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button onClick={loadSiteStatus} disabled={siteLoading} className="btn-shine rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 glow-emerald">
                      {siteLoading ? "Проверка..." : "Проверить сайт"}
                    </button>
                    <button onClick={clearOpenCartCache} disabled={fileLoading} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-amber-400 disabled:opacity-50">
                      Очистить кэш
                    </button>
                    <button onClick={generateSitemap} disabled={siteLoading} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-sky-400 disabled:opacity-50">
                      Sitemap
                    </button>
                    <button onClick={generateRobots} disabled={siteLoading} className="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-indigo-400 disabled:opacity-50">
                      Robots
                    </button>
                    <button onClick={findBrokenImages} disabled={siteLoading} className="rounded-lg bg-rose-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-rose-400 disabled:opacity-50">
                      Изображения
                    </button>
                    <button onClick={cleanUnusedImages} disabled={siteLoading} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-500 disabled:opacity-50">
                      Очистить лишнее
                    </button>
                    <button onClick={restoreBackup} disabled={siteLoading} className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-bold text-white hover:bg-purple-500 disabled:opacity-50">
                      Восстановить
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><MonitorCheck size={18} className="text-emerald-400" /> Health</h3>
                  {siteHealth ? (
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-slate-500">Статус</span><span className="badge badge-active"><span className="badge-dot"></span>{siteHealth.status}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">PHP</span><span>{siteHealth.php}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">OpenCart</span><span>{siteHealth.opencart}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Время</span><span>{siteHealth.time}</span></div>
                    </div>
                  ) : (
                    <div className="text-sm text-slate-500">Нажми «Проверить сайт»</div>
                  )}
                </div>

                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5 lg:col-span-2">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><AlertCircle size={18} className="text-red-400" /> Последние ошибки</h3>
                  <pre className="max-h-64 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300">
                    {siteErrorLog || "Ошибок не найдено или лог пока не загружен."}
                  </pre>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><ShieldCheck size={18} className="text-sky-400" /> Безопасные действия</h3>
                  <div className="space-y-2 text-sm">
                    <button onClick={() => { setTab("files"); setFileListPath("catalog/view/theme/"); listOpenCartFiles("catalog/view/theme/"); }} className="w-full rounded-lg bg-slate-800 px-3 py-2 text-left hover:bg-slate-700">
                      Открыть шаблоны темы
                    </button>
                    <button onClick={() => { setTab("files"); setFileListPath("catalog/view/javascript/"); listOpenCartFiles("catalog/view/javascript/"); }} className="w-full rounded-lg bg-slate-800 px-3 py-2 text-left hover:bg-slate-700">
                      Открыть JS сайта
                    </button>
                    <button onClick={() => { setTab("files"); setFilePath("catalog/controller/common/header.php"); readOpenCartFile("catalog/controller/common/header.php"); }} className="w-full rounded-lg bg-slate-800 px-3 py-2 text-left hover:bg-slate-700">
                      Header controller
                    </button>
                  </div>
                </div>

                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5 lg:col-span-2">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><FileCheck size={18} className="text-emerald-400" /> Последние backup</h3>
                  <div className="max-h-72 overflow-auto space-y-2 text-sm">
                    {siteBackups.map((backup) => (
                      <div key={backup.path} className="rounded-xl bg-slate-950 p-3">
                        <div className="truncate font-mono text-xs text-emerald-400">{backup.path}</div>
                        <div className="mt-1 flex justify-between text-xs text-slate-500">
                          <span>{backup.modified}</span>
                          <span>{backup.size} bytes</span>
                        </div>
                      </div>
                    ))}
                    {!siteBackups.length && <div className="text-slate-500">Backup не загружены. Нажми «Проверить сайт».</div>}
                  </div>
                </div>
              </div>

              {siteImages && (
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5 lg:col-span-3">
                  <h3 className="mb-4 flex items-center gap-2 font-bold"><Image size={18} className="text-rose-400" /> Изображения</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                    <div className="rounded-xl bg-slate-950 p-3 text-center">
                      <div className="text-2xl font-bold text-emerald-400">{siteImages.total_files}</div>
                      <div className="text-slate-500">Всего файлов</div>
                    </div>
                    <div className="rounded-xl bg-slate-950 p-3 text-center">
                      <div className="text-2xl font-bold text-emerald-400">{siteImages.total_db_images}</div>
                      <div className="text-slate-500">В БД</div>
                    </div>
                    <div className="rounded-xl bg-slate-950 p-3 text-center">
                      <div className="text-2xl font-bold text-amber-400">{siteImages.unused_count}</div>
                      <div className="text-slate-500">Неиспользуемых</div>
                    </div>
                    <div className="rounded-xl bg-slate-950 p-3 text-center">
                      <div className="text-2xl font-bold text-rose-400">{siteImages.broken_count}</div>
                      <div className="text-slate-500">Битых</div>
                    </div>
                  </div>
                  {siteImages.broken.length > 0 && (
                    <div className="mb-3">
                      <div className="mb-1 text-sm font-bold text-rose-400">Битые ссылки (первые 50):</div>
                      <div className="max-h-40 overflow-auto rounded-xl bg-slate-950 p-3 text-xs font-mono text-slate-300">
                        {siteImages.broken.map((img, i) => <div key={i} className="truncate">{img}</div>)}
                      </div>
                    </div>
                  )}
                  {siteImages.unused.length > 0 && (
                    <div>
                      <div className="mb-1 text-sm font-bold text-amber-400">Неиспользуемые файлы (первые 50):</div>
                      <div className="max-h-40 overflow-auto rounded-xl bg-slate-950 p-3 text-xs font-mono text-slate-300">
                        {siteImages.unused.map((img, i) => <div key={i} className="truncate">{img}</div>)}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* AI SEO */}
          {tab === "ai-seo" && (
            <AiSeoPanel
              products={aiSeoProducts}
              setProducts={setAiSeoProducts}
              filter={aiSeoFilter}
              setFilter={setAiSeoFilter}
              loading={aiSeoLoading}
              setLoading={setAiSeoLoading}
              progress={aiSeoProgress}
              setProgress={setAiSeoProgress}
              log={aiSeoLog}
              setLog={setAiSeoLog}
              preview={aiSeoPreview}
              setPreview={setAiSeoPreview}
              addToast={addToast}
            />
          )}

          {/* COMPETITORS BIDS */}
          {tab === "competitors-bids" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                  <div>
                    <h2 className="text-lg font-bold">Конкуренты и ставки</h2>
                    <p className="text-sm text-slate-400">Сканирование цен конкурентов, сравнение с нашими ценами.</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={loadCompetitors} disabled={compLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{compLoading ? "Загрузка..." : "Обновить"}</button>
                    <button onClick={loadComparison} disabled={compLoading} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400 disabled:opacity-50">Сравнить цены</button>
                    <button onClick={loadAiRecommendations} disabled={aiRecsLoading} className="rounded-lg bg-violet-500 px-4 py-2 text-sm font-bold text-white hover:bg-violet-400 disabled:opacity-50">{aiRecsLoading ? "AI думает..." : "AI Рекомендации"}</button>
                    <button onClick={loadOurProductsAds} disabled={ourProductsAdsLoading} className="rounded-lg bg-rose-500 px-4 py-2 text-sm font-bold text-white hover:bg-rose-400 disabled:opacity-50">{ourProductsAdsLoading ? "Поиск..." : "Конкуренция по товарам"}</button>
                    <button onClick={addRecommendedCompetitors} className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-amber-400">+10 конкурентов</button>
                    <button onClick={analyzeBids} disabled={bidsLoading} className="rounded-lg bg-red-500 px-4 py-2 text-sm font-bold text-white hover:bg-red-400 disabled:opacity-50">{bidsLoading ? "Анализ..." : "Ставки Яндекс"}</button>
                  </div>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Добавьте конкурента:</b> введите название и URL сайта → нажмите «Добавить».</p>
                    <p><b>2. Сканируйте цены:</b> в таблице конкурентов нажмите «Сканировать» — система соберёт цены с сайта.</p>
                    <p><b>3. Смотрите товары:</b> после сканирования нажмите «Товары» — увидите, что продаёт конкурент.</p>
                    <p><b>4. Сравните:</b> нажмите «Сравнить цены» — увидите, где наши цены выше/ниже.</p>
                    <p><b>5. AI Рекомендации:</b> нажмите фиолетовую кнопку — AI подскажет, на что запускать рекламу и какие ключи использовать.</p>
                    <p><b>6. Конкуренция по товарам:</b> розовая кнопка покажет, кто из конкурентов работает по вашим товарам.</p>
                    <p><b>7. Быстрое добавление:</b> жёлтая кнопка «+10 конкурентов» — мгновенно добавляет 10 популярных строительных магазинов Москвы.</p>
                  </div>
                </div>

                {/* Результаты анализа ставок Яндекс */}
                {bidsAnalysis && (
                  <div className="mb-6 rounded-xl bg-red-500/5 p-4 border border-red-500/20">
                    <div className="mb-2 flex items-center gap-2">
                      <span className="text-xs font-semibold uppercase tracking-wider text-red-400">Анализ ставок Яндекс Директ</span>
                      {bidsAnalysis.sandbox && (
                        <span className="rounded bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-400 uppercase">Sandbox</span>
                      )}
                      {bidsAnalysis.token_valid && (
                        <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400 uppercase">API OK</span>
                      )}
                    </div>
                    {bidsAnalysis.status === "no_token" ? (
                      <div className="text-sm text-slate-300">
                        <p className="mb-2"><b>Токен не настроен.</b> Для получения точных ставок нужен API-ключ Яндекс Директ.</p>
                        <p className="text-xs text-slate-500">Создайте приложение в oauth.yandex.ru и получите токен.</p>
                      </div>
                    ) : (
                      <div className="text-sm space-y-2">
                        <div className="flex flex-wrap gap-4 text-xs text-slate-400">
                          <span>Кампаний: <b className="text-slate-200">{bidsAnalysis.campaigns_count || 0}</b></span>
                          <span>Ключей проверено: <b className="text-slate-200">{bidsAnalysis.keywords_checked}</b></span>
                        </div>
                        {bidsAnalysis.bids && bidsAnalysis.bids.length > 0 ? (
                          <div className="mt-2">
                            <div className="text-xs font-semibold text-red-400 mb-1">Ставки по ключам</div>
                            <div className="space-y-1 max-h-48 overflow-y-auto">
                              {bidsAnalysis.bids.map((b, i) => (
                                <div key={i} className="flex justify-between items-center text-xs border-b border-slate-800 pb-1">
                                  <span className="text-slate-300 truncate max-w-[50%]">{b.Keyword}</span>
                                  <div className="flex gap-3">
                                    {b.Bid > 0 && <span className="text-emerald-400 font-mono">{(b.Bid / 1000000).toFixed(2)} ₽</span>}
                                    {b.ContextBid > 0 && <span className="text-blue-400 font-mono">РСЯ: {(b.ContextBid / 1000000).toFixed(2)} ₽</span>}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="rounded bg-slate-950/50 p-3 text-xs text-slate-400">
                            <p className="mb-1"><b>Нет данных по ставкам.</b></p>
                            <p>{bidsAnalysis.note}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Автопоиск конкурентов */}
                <div className="mb-6 rounded-xl bg-violet-500/5 p-4 border border-violet-500/20">
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-violet-400">Автопоиск конкурентов</div>
                  <div className="flex flex-wrap gap-2">
                    <input
                      value={discoverQuery}
                      onChange={(e) => setDiscoverQuery(e.target.value)}
                      placeholder="Например: строительные материалы москва"
                      className="min-w-[250px] flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-violet-500"
                    />
                    <button
                      onClick={autoDiscoverCompetitors}
                      disabled={discoverLoading}
                      className="rounded-lg bg-violet-500 px-4 py-2 text-sm font-bold text-white hover:bg-violet-400 disabled:opacity-50"
                    >
                      {discoverLoading ? "Поиск..." : "Найти и добавить"}
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">Система ищет в Яндексе по запросу, фильтрует агрегаторы (Авито, Озон и т.д.), добавляет сайты-магазины и сразу сканирует их товары.</p>
                </div>

                {/* Сканирование любого сайта через Playwright */}
                <div className="mb-6 rounded-xl bg-amber-500/5 p-4 border border-amber-500/20">
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-amber-400">Playwright — сканирование любого сайта</div>
                  <div className="flex flex-wrap gap-2">
                    <input
                      value={pwUrl}
                      onChange={(e) => setPwUrl(e.target.value)}
                      placeholder="https://site.com"
                      className="min-w-[250px] flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-amber-500"
                    />
                    <button
                      onClick={scanAnyUrl}
                      disabled={pwUrlLoading}
                      className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-amber-400 disabled:opacity-50"
                    >
                      {pwUrlLoading ? "Сканирование..." : "Сканировать"}
                    </button>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">Открывает сайт в реальном браузере Chrome, парсит товары даже из React/Vue. Не сохраняет в базу — только показывает.</p>

                  {pwUrlResult && pwUrlResult.products_found > 0 && (
                    <div className="mt-3 rounded border border-slate-700 bg-slate-950 p-3">
                      <div className="text-xs font-semibold text-amber-400 mb-2">Найдено товаров: {pwUrlResult.products_found} на {pwUrlResult.domain}</div>
                      <div className="space-y-1 max-h-48 overflow-y-auto">
                        {pwUrlResult.products.map((p, i) => (
                          <div key={i} className="flex justify-between text-xs border-b border-slate-800 pb-1">
                            <span className="text-slate-300 truncate max-w-[70%]">{p.name}</span>
                            <span className="text-emerald-400 font-mono">{p.price} {p.currency}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Добавление конкурента */}
                <div className="mb-6 rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Добавить конкурента</div>
                  <div className="flex flex-wrap gap-2">
                    <input value={competitorName} onChange={(e) => setCompetitorName(e.target.value)} placeholder="Название конкурента" className="min-w-[200px] flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <input value={competitorUrl} onChange={(e) => setCompetitorUrl(e.target.value)} placeholder="URL сайта (опционально)" className="min-w-[200px] flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <button onClick={addCompetitor} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">Добавить</button>
                  </div>
                </div>

                {/* Список конкурентов */}
                {competitorsList.length === 0 && !compLoading ? (
                  <div className="text-center text-slate-500 py-8">Нет конкурентов. Добавьте первого выше.</div>
                ) : (
                  <div className="overflow-auto rounded-xl border border-slate-700/30">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                          <th className="px-4 py-3">ID</th>
                          <th className="px-4 py-3">Название</th>
                          <th className="px-4 py-3">URL</th>
                          <th className="px-4 py-3">Добавлен</th>
                          <th className="px-4 py-3 text-right">Действия</th>
                        </tr>
                      </thead>
                      <tbody>
                        {competitorsList.map((c) => (
                          <tr key={c.id} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                            <td className="px-4 py-3 font-mono text-slate-500">{c.id}</td>
                            <td className="px-4 py-3 font-medium">{c.name}</td>
                            <td className="px-4 py-3 text-slate-400">{c.url || "—"}</td>
                            <td className="px-4 py-3 text-slate-400">{c.created_at?.slice(0, 10) || "—"}</td>
                            <td className="px-4 py-3 text-right">
                              <div className="flex justify-end gap-2">
                                {c.url && (
                                  <button onClick={() => scanCompetitor(c.id)} disabled={compScanning === c.id} className="rounded bg-sky-500/20 px-2 py-1 text-xs text-sky-400 hover:bg-sky-500/30 disabled:opacity-50">
                                    {compScanning === c.id ? "Сканирование..." : "Сканировать"}
                                  </button>
                                )}
                                <button onClick={() => loadCompetitorProducts(c.id)} className="rounded bg-emerald-500/20 px-2 py-1 text-xs text-emerald-400 hover:bg-emerald-500/30">Товары</button>
                                <button onClick={() => loadCompetitorAds(c.id)} disabled={compAdsLoading} className="rounded bg-rose-500/20 px-2 py-1 text-xs text-rose-400 hover:bg-rose-500/30 disabled:opacity-50">{compAdsLoading && compSelectedId === c.id ? "Поиск..." : "Реклама"}</button>
                                <button onClick={() => scanWithPlaywright(c.id)} disabled={pwScanning === c.id} className="rounded bg-violet-500/20 px-2 py-1 text-xs text-violet-400 hover:bg-violet-500/30 disabled:opacity-50">{pwScanning === c.id ? "Браузер..." : "Playwright"}</button>
                                <button onClick={() => deleteCompetitor(c.id)} className="rounded bg-red-500/20 px-2 py-1 text-xs text-red-400 hover:bg-red-500/30">Удалить</button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Товары выбранного конкурента */}
                {compSelectedId && compSelectedProducts.length > 0 && (
                  <div className="mt-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Товары конкурента #{compSelectedId}</h3>
                    {compSelectedStats && (
                      <div className="mb-3 flex flex-wrap gap-4 text-xs text-slate-400">
                        <span>Всего товаров: <b className="text-slate-200">{compSelectedStats.total_products}</b></span>
                        <span>Средняя цена: <b className="text-slate-200">{compSelectedStats.avg_price ? compSelectedStats.avg_price + ' ₽' : '—'}</b></span>
                        {compSelectedStats.categories?.length > 0 && (
                          <span>Категории: {compSelectedStats.categories.map(c => c.category).join(', ')}</span>
                        )}
                      </div>
                    )}
                    <div className="overflow-auto rounded-xl border border-slate-700/30 max-h-96">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-2">Название</th>
                            <th className="px-4 py-2 text-right">Цена</th>
                            <th className="px-4 py-2">Категория</th>
                          </tr>
                        </thead>
                        <tbody>
                          {compSelectedProducts.map((p, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-2">
                                <a href={p.product_url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline">{p.product_name}</a>
                                {p.description && <div className="text-xs text-slate-500 mt-1">{p.description}</div>}
                              </td>
                              <td className="px-4 py-2 text-right font-medium">{p.price ? p.price + ' ₽' : '—'}</td>
                              <td className="px-4 py-2 text-xs text-slate-400">{p.category || '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Рекламные объявления конкурента */}
                {compSelectedId && compAds.length > 0 && (
                  <div className="mt-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2">
                      <span className="inline-block w-2 h-2 rounded-full bg-rose-400 animate-pulse"></span>
                      Реклама конкурента #{compSelectedId}
                    </h3>
                    {compAdsStrategy && compAdsStrategy.top_keywords && (
                      <div className="mb-3 flex flex-wrap gap-2">
                        <span className="text-xs text-slate-500">Топ ключей:</span>
                        {compAdsStrategy.top_keywords.slice(0, 5).map((kw, i) => (
                          <span key={i} className="rounded bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 text-xs text-rose-400">{kw[0]} ({kw[1]})</span>
                        ))}
                      </div>
                    )}
                    <div className="space-y-2 max-h-96 overflow-auto">
                      {compAds.map((ad, i) => (
                        <div key={i} className="rounded-lg border border-rose-500/10 bg-rose-500/5 p-3">
                          <div className="text-xs font-semibold text-rose-300 mb-1">{ad.ad_title || "Без заголовка"}</div>
                          <div className="text-xs text-slate-400 mb-1">{ad.ad_text}</div>
                          <div className="flex flex-wrap items-center gap-2">
                            <a href={ad.ad_url} target="_blank" rel="noreferrer" className="text-xs text-sky-400 hover:underline truncate max-w-md">{ad.ad_url}</a>
                            <span className="text-xs text-slate-500">• {ad.keyword}</span>
                            {ad.ad_position && <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">{ad.ad_position}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Рекомендации по рекламе */}
                {aiRecs && aiRecs.status === "ok" && aiRecs.recommendations && aiRecs.recommendations.length > 0 && (
                  <div className="mt-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-violet-400 flex items-center gap-2">
                      <span className="inline-block w-2 h-2 rounded-full bg-violet-400 animate-pulse"></span>
                      AI Рекомендации — на что запускать рекламу
                    </h3>
                    <div className="space-y-3">
                      {aiRecs.recommendations.map((rec, i) => (
                        <div key={i} className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                            <div className="font-bold text-slate-200">{rec.product_name || rec.sku}</div>
                            <div className="flex gap-2">
                              <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-400">ROI {rec.expected_roi}%</span>
                              <span className="rounded bg-sky-500/20 px-2 py-0.5 text-xs text-sky-400">Ставка {rec.recommended_cpc}₽</span>
                            </div>
                          </div>
                          <div className="text-xs text-slate-400 mb-2">{rec.why}</div>
                          <div className="flex flex-wrap gap-1">
                            {(rec.keywords || []).map((kw, ki) => (
                              <span key={ki} className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300 border border-slate-700">{kw}</span>
                            ))}
                          </div>
                          <button onClick={() => analyzeKeywordsForProduct(rec.product_name)} className="mt-2 text-xs text-violet-400 hover:text-violet-300 underline">Подробнее по ключевым словам</button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {aiRecs && aiRecs.status === "ok" && (!aiRecs.recommendations || aiRecs.recommendations.length === 0) && (
                  <div className="mt-6 text-center text-slate-500 py-4">AI не нашёл рекомендаций. Добавьте конкурентов и просканируйте их сайты.</div>
                )}

                {/* Конкуренция по нашим товарам */}
                {ourProductsAds && ourProductsAds.status === "ok" && ourProductsAds.data && ourProductsAds.data.length > 0 && (
                  <div className="mt-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-rose-400 flex items-center gap-2">
                      <span className="inline-block w-2 h-2 rounded-full bg-rose-400 animate-pulse"></span>
                      Конкуренция по нашим товарам
                    </h3>
                    <div className="space-y-3">
                      {ourProductsAds.data.map((item, i) => (
                        <div key={i} className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4">
                          <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                            <div className="font-bold text-slate-200">{item.product_name}</div>
                            <div className="flex gap-2">
                              <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">Наша цена: {item.our_price}₽</span>
                              <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-400">ROI {item.our_roi}%</span>
                              <span className="rounded bg-rose-500/20 px-2 py-0.5 text-xs text-rose-400">{item.competitors_count} конкурентов в рекламе</span>
                            </div>
                          </div>
                          <div className="text-xs text-slate-500 mb-2">Запрос: {item.query}</div>
                          <div className="space-y-1">
                            {item.competitors_ads.slice(0, 3).map((ad, ai) => (
                              <div key={ai} className="flex items-start gap-2 text-xs">
                                <span className="text-rose-400 font-medium">{ad.domain}</span>
                                <span className="text-slate-400">{ad.ad_title || ad.ad_text}</span>
                              </div>
                            ))}
                            {item.competitors_ads.length > 3 && (
                              <div className="text-xs text-slate-500">+ ещё {item.competitors_ads.length - 3} объявлений</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {ourProductsAds && ourProductsAds.status === "ok" && (!ourProductsAds.data || ourProductsAds.data.length === 0) && (
                  <div className="mt-6 text-center text-slate-500 py-4">По нашим товарам не найдено рекламных объявлений конкурентов.</div>
                )}

                {/* Детальный анализ ключевых слов */}
                {aiKeywordResult && aiKeywordResult.keywords && (
                  <div className="mt-6 rounded-xl border border-slate-700/30 bg-slate-800/30 p-4">
                    <h4 className="mb-2 text-sm font-bold text-violet-400">Ключевые слова: {aiKeywordResult.product}</h4>
                    {aiKeywordResult.keywords.exact && (
                      <div className="mb-2">
                        <div className="text-xs text-slate-500 mb-1">Точные фразы (дешёвый клик):</div>
                        <div className="flex flex-wrap gap-1">
                          {aiKeywordResult.keywords.exact.map((k, i) => (
                            <span key={i} className="rounded bg-emerald-500/10 border border-emerald-500/20 px-2 py-1 text-xs text-emerald-400">{k}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {aiKeywordResult.keywords.broad && (
                      <div className="mb-2">
                        <div className="text-xs text-slate-500 mb-1">Широкие фразы (высокий спрос):</div>
                        <div className="flex flex-wrap gap-1">
                          {aiKeywordResult.keywords.broad.map((k, i) => (
                            <span key={i} className="rounded bg-sky-500/10 border border-sky-500/20 px-2 py-1 text-xs text-sky-400">{k}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    {aiKeywordResult.keywords.negative && (
                      <div>
                        <div className="text-xs text-slate-500 mb-1">Минус-слова:</div>
                        <div className="flex flex-wrap gap-1">
                          {aiKeywordResult.keywords.negative.map((k, i) => (
                            <span key={i} className="rounded bg-red-500/10 border border-red-500/20 px-2 py-1 text-xs text-red-400">-{k}</span>
                          ))}
                        </div>
                      </div>
                    )}
                    <button onClick={() => setAiKeywordResult(null)} className="mt-3 text-xs text-slate-500 hover:text-slate-300 underline">Закрыть</button>
                  </div>
                )}

                {/* Сравнение цен */}
                {compShowCompare && compComparisons.length > 0 && (
                  <div className="mt-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Сравнение цен с конкурентами</h3>
                    <div className="overflow-auto rounded-xl border border-slate-700/30">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-3">SKU</th>
                            <th className="px-4 py-3">Товар</th>
                            <th className="px-4 py-3 text-right">Наша цена</th>
                            <th className="px-4 py-3 text-right">Конкурент</th>
                            <th className="px-4 py-3 text-right">Разница</th>
                          </tr>
                        </thead>
                        <tbody>
                          {compComparisons.map((row, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-3 font-mono text-slate-500">{row.sku}</td>
                              <td className="px-4 py-3">{row.name}</td>
                              <td className="px-4 py-3 text-right font-medium">{money(row.our_price)}</td>
                              <td className="px-4 py-3 text-right text-slate-400">{row.competitor_name}<br/><span className="text-xs">{money(row.competitor_price)}</span></td>
                              <td className={`px-4 py-3 text-right font-bold ${row.diff > 0 ? "text-red-400" : "text-emerald-400"}`}>
                                {row.diff > 0 ? "+" : ""}{row.diff_pct}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
                {compShowCompare && compComparisons.length === 0 && !compLoading && (
                  <div className="mt-6 text-center text-slate-500 py-4">Нет данных для сравнения. Импортируйте цены конкурентов.</div>
                )}
              </div>
            </div>
          )}

          {/* BUDGET ROI */}
          {tab === "budget-roi" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold">Бюджет и окупаемость</h2>
                    <p className="text-sm text-slate-400">ИИ подбирает товары для рекламы по вашему бюджету, считает прибыль и срок окупаемости.</p>
                  </div>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Введите бюджет:</b> сумма в рублях, которую готовы потратить на закупку товаров под рекламу.</p>
                    <p><b>2. Нажмите «Рассчитать»:</b> ИИ подберёт товары из каталога, которые поместятся в бюджет с учётом наценки.</p>
                    <p><b>3. Смотрите KPI:</b> карточки покажут общую прибыль, ROI и маржинальность выбранных товаров.</p>
                    <p><b>4. Прогноз:</b> нажмите «Прогноз» для визуализации окупаемости по месяцам.</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-end gap-3 mb-6">
                  <div>
                    <div className="mb-1 text-xs text-slate-500">Бюджет на закупку, ₽</div>
                    <input type="number" value={budgetAmount} onChange={(e) => setBudgetAmount(e.target.value)} className="w-48 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                  </div>
                  <button onClick={calculateBudget} disabled={budgetLoading} className="rounded-lg bg-emerald-500 px-5 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{budgetLoading ? "Расчёт..." : "Рассчитать"}</button>
                  <button onClick={loadForecast} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">Прогноз</button>
                </div>

                {/* KPI результаты */}
                {budgetResults && (
                  <div className="mb-6 grid gap-4 md:grid-cols-5">
                    <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-1">Бюджет</div>
                      <div className="text-xl font-bold text-white">{money(budgetResults.budget)}</div>
                    </div>
                    <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-1">Товаров подобрано</div>
                      <div className="text-xl font-bold text-emerald-400">{budgetResults.selected_count}</div>
                    </div>
                    <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-1">Себестоимость</div>
                      <div className="text-xl font-bold text-slate-300">{money(budgetResults.total_cost)}</div>
                    </div>
                    <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-1">Прогноз прибыли</div>
                      <div className="text-xl font-bold text-emerald-400">{money(budgetResults.estimated_profit)}</div>
                    </div>
                    <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-1">ROI / Окупаемость</div>
                      <div className="text-xl font-bold text-sky-400">{budgetResults.estimated_roi}%</div>
                      <div className="text-xs text-slate-500">{budgetResults.break_even_days} дн.</div>
                    </div>
                  </div>
                )}

                {/* Таблица подобранных товаров */}
                {budgetResults && budgetResults.selected_products && budgetResults.selected_products.length > 0 && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Подобранные товары</h3>
                    <div className="overflow-auto rounded-xl border border-slate-700/30">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-3">Товар</th>
                            <th className="px-4 py-3 text-right">Цена продажи</th>
                            <th className="px-4 py-3 text-right">Цена закупа</th>
                            <th className="px-4 py-3 text-right">Маржа</th>
                            <th className="px-4 py-3 text-right">Маржа %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {budgetResults.selected_products.map((p, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-3">{p.name}</td>
                              <td className="px-4 py-3 text-right font-medium">{money(p.price)}</td>
                              <td className="px-4 py-3 text-right text-slate-400">{money(p.cash_price || p.price * 0.6)}</td>
                              <td className="px-4 py-3 text-right text-emerald-400">{money(p.margin)}</td>
                              <td className="px-4 py-3 text-right">{p.margin_pct}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* График прогноза */}
                {budgetForecast.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Прогноз прибыли (30 дней)</h3>
                    <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                      <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={budgetForecast}>
                            <XAxis dataKey="day" stroke="#64748b" fontSize={12} />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} itemStyle={{ color: '#e2e8f0' }} />
                            <Bar dataKey="cumulative" fill="#34d399" radius={[4, 4, 0, 0]} name="Накопленная прибыль" />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* PROMOTIONS */}
          {tab === "promotions" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold">Акции и локомотивы</h2>
                    <p className="text-sm text-slate-400">Поиск товаров-связок (локомотив + вагон), создание динамических акций.</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={findBundles} disabled={promoLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{promoLoading ? "Поиск..." : "Найти связки"}</button>
                    <button onClick={loadPromotions} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">Список акций</button>
                  </div>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Найдите связки:</b> нажмите «Найти связки» — система подберёт товары, которые часто покупают вместе.</p>
                    <p><b>2. Создайте акцию:</b> введите название, выберите связку и скидку (%) → нажмите «Создать акцию».</p>
                    <p><b>3. Список акций:</b> нажмите «Список акций» чтобы увидеть все активные акции и их эффективность.</p>
                    <p><b>4. Локомотив + вагон:</b> первый товар — основной, второй — дополнительный с повышенной маржой.</p>
                  </div>
                </div>

                {/* Создание акции */}
                <div className="mb-6 rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Создать акцию</div>
                  <div className="flex flex-wrap gap-2">
                    <input value={promoName} onChange={(e) => setPromoName(e.target.value)} placeholder="Название акции" className="min-w-[200px] flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <input type="number" value={promoDiscount} onChange={(e) => setPromoDiscount(e.target.value)} placeholder="Скидка %" className="w-24 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <button onClick={createPromotion} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">Создать</button>
                  </div>
                </div>

                {/* Найденные связки */}
                {promoBundles.length > 0 && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Найденные связки</h3>
                    <div className="overflow-auto rounded-xl border border-slate-700/30">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-3">Локомотив</th>
                            <th className="px-4 py-3 text-right">Цена</th>
                            <th className="px-4 py-3">Вагон</th>
                            <th className="px-4 py-3 text-right">Цена</th>
                            <th className="px-4 py-3 text-right">Скидка</th>
                            <th className="px-4 py-3 text-right">Итого</th>
                          </tr>
                        </thead>
                        <tbody>
                          {promoBundles.map((b, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-3 font-medium">{b.locomotive?.name}</td>
                              <td className="px-4 py-3 text-right">{money(b.locomotive?.price)}</td>
                              <td className="px-4 py-3">{b.wagon?.name}</td>
                              <td className="px-4 py-3 text-right text-slate-400">{money(b.wagon?.price)}</td>
                              <td className="px-4 py-3 text-right text-emerald-400">{money(b.discount)}</td>
                              <td className="px-4 py-3 text-right font-bold">{money(b.bundle_price)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Список акций */}
                {promoList.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Активные акции</h3>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {promoList.map((p) => (
                        <div key={p.promotion_id} className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-bold">{p.name}</span>
                            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-400">{p.status}</span>
                          </div>
                          <div className="text-xs text-slate-400">Скидка: {p.discount_pct}%</div>
                          <div className="text-xs text-slate-500">Товаров: {p.products?.length || 0}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Special Prices Manager */}
                <div className="mt-8 rounded-xl border border-slate-700/30 bg-slate-800/30 p-6">
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div>
                      <h3 className="text-base font-bold">Акционные цены на товары</h3>
                      <p className="text-xs text-slate-400">Установите скидочную цену — товар появится в блоке «Акции» на сайте.</p>
                    </div>
                    <button onClick={loadSpecialProducts} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">Обновить список</button>
                  </div>

                  {/* Add special price */}
                  <div className="mb-4 rounded-lg bg-slate-800/50 p-4 border border-slate-700/30">
                    <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Назначить акцию</div>
                    <div className="flex flex-wrap gap-2 items-end">
                      <div className="min-w-[280px] flex-1">
                        <input
                          value={specialSearch}
                          onChange={(e) => setSpecialSearch(e.target.value)}
                          placeholder="Поиск по названию или артикулу..."
                          className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500"
                        />
                        {specialSearch.trim() && !specialSelected && (
                          <div className="mt-1 max-h-40 overflow-auto rounded border border-slate-700 bg-slate-950">
                            {products.filter(p => (p.name?.toLowerCase().includes(specialSearch.toLowerCase()) || p.sku?.toLowerCase().includes(specialSearch.toLowerCase()))).slice(0, 5).map(p => (
                              <button key={p.product_id} onClick={() => { setSpecialSelected(p); setSpecialSearch(p.name + " (" + p.sku + ")"); }} className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-800">
                                <span className="truncate">{p.name}</span>
                                <span className="text-xs text-slate-500 ml-2 shrink-0">{money(p.price)}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      <input type="number" value={specialPriceInput} onChange={(e) => setSpecialPriceInput(e.target.value)} placeholder="Акц. цена" className="w-32 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                      <button onClick={setProductSpecialPrice} disabled={specialLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{specialLoading ? "..." : "Установить"}</button>
                    </div>
                    {specialSelected && (
                      <div className="mt-2 text-xs text-slate-400">Базовая цена: {money(specialSelected.price)} | SKU: {specialSelected.sku}</div>
                    )}
                  </div>

                  {/* Current special products */}
                  {specialProducts.length > 0 && (
                    <div>
                      <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">Текущие акции на сайте ({specialProducts.length})</h4>
                      <div className="overflow-auto rounded-xl border border-slate-700/30">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                              <th className="px-4 py-3">Товар</th>
                              <th className="px-4 py-3 text-right">Базовая</th>
                              <th className="px-4 py-3 text-right">Акция</th>
                              <th className="px-4 py-3 text-right">Скидка</th>
                              <th className="px-4 py-3 text-center">Действие</th>
                            </tr>
                          </thead>
                          <tbody>
                            {specialProducts.map((p) => (
                              <tr key={p.product_id} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                                <td className="px-4 py-3 font-medium">{p.name}</td>
                                <td className="px-4 py-3 text-right text-slate-400">{money(p.price)}</td>
                                <td className="px-4 py-3 text-right font-bold text-emerald-400">{money(p.special_price)}</td>
                                <td className="px-4 py-3 text-right text-amber-400">{p.discount}%</td>
                                <td className="px-4 py-3 text-center">
                                  <button onClick={() => removeSpecialPrice(p.product_id)} className="rounded bg-red-500/20 px-2 py-1 text-xs text-red-400 hover:bg-red-500/30">Убрать</button>
                                </td>
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
          )}

          {/* TENDERS */}
          {tab === "tenders" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold">Тендеры</h2>
                    <p className="text-sm text-slate-400">Поиск тендерных позиций по региону, проверка покрытия ассортиментом, подготовка заявки.</p>
                  </div>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Укажите регион:</b> введите город или область, где нужно найти тендерные закупки.</p>
                    <p><b>2. Найдите позиции:</b> нажмите «Найти позиции» — система покажет тендеры, связанные с нашими товарами.</p>
                    <p><b>3. Проверьте покрытие:</b> нажмите «Проверить покрытие» — узнайте, какие товары из тендера есть на нашем складе.</p>
                    <p><b>4. Подайте заявку:</b> если покрытие высокое, нажмите «Подать заявку» — система сформирует КП.</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-end gap-3 mb-6">
                  <div>
                    <div className="mb-1 text-xs text-slate-500">Регион</div>
                    <input value={tenderRegion} onChange={(e) => setTenderRegion(e.target.value)} className="w-48 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                  </div>
                  <button onClick={searchTenders} disabled={tenderLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{tenderLoading ? "Поиск..." : "Найти позиции"}</button>
                  <button onClick={checkCoverage} disabled={tenderLoading} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400 disabled:opacity-50">Проверить покрытие</button>
                  <button onClick={submitTender} className="rounded-lg bg-indigo-500 px-4 py-2 text-sm font-bold text-white hover:bg-indigo-400">Подготовить заявку</button>
                </div>

                {/* Покрытие */}
                {tenderCoverage && (
                  <div className="mb-6 grid gap-3 md:grid-cols-3">
                    <div className="rounded-xl bg-emerald-500/10 p-4 border border-emerald-500/20">
                      <div className="text-xs text-emerald-400 mb-1">Покрыто</div>
                      <div className="text-2xl font-bold text-emerald-400">{tenderCoverage.coverage_percent}%</div>
                      <div className="text-xs text-slate-500">{tenderCoverage.covered_items?.length || 0} позиций</div>
                    </div>
                    <div className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                      <div className="text-xs text-slate-500 mb-1">Всего позиций</div>
                      <div className="text-2xl font-bold text-white">{tendersList.length}</div>
                    </div>
                    <div className="rounded-xl bg-red-500/10 p-4 border border-red-500/20">
                      <div className="text-xs text-red-400 mb-1">Не хватает</div>
                      <div className="text-2xl font-bold text-red-400">{tenderCoverage.missing_items?.length || 0}</div>
                    </div>
                  </div>
                )}

                {/* Таблица тендерных позиций */}
                {tendersList.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Тендерные позиции</h3>
                    <div className="overflow-auto rounded-xl border border-slate-700/30">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-3">ID</th>
                            <th className="px-4 py-3">Название</th>
                            <th className="px-4 py-3 text-right">Объём</th>
                            <th className="px-4 py-3 text-right">Наша цена (безнал)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tendersList.map((t, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-3 font-mono text-slate-500">{t.tender_id}</td>
                              <td className="px-4 py-3">{t.name}</td>
                              <td className="px-4 py-3 text-right text-slate-400">{t.estimated_volume} {t.unit}</td>
                              <td className="px-4 py-3 text-right font-medium">{money(t.our_price_beznal)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* REVIEWS */}
          {tab === "reviews" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold">Отзывы и репутация</h2>
                    <p className="text-sm text-slate-400">Парсинг негативных отзывов о конкурентах, генерация коммерческих предложений.</p>
                  </div>
                  <button onClick={parseReviews} disabled={reviewsLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{reviewsLoading ? "Парсинг..." : "Спарсить отзывы"}</button>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Спарсьте отзывы:</b> нажмите «Спарсить отзывы» — система соберёт негативные отзывы о конкурентах с Яндекс.Карт и 2ГИС.</p>
                    <p><b>2. Изучите проблемы:</b> в карточках отзывов видны основные жалобы: цены, доставка, качество, сервис.</p>
                    <p><b>3. Сгенерируйте КП:</b> введите название конкурента → нажмите «Сгенерировать КП» — ИИ создаст коммерческое предложение, подчёркивая наши преимущества.</p>
                    <p><b>4. Используйте КП:</b> скопируйте текст и отправьте потенциальному клиенту.</p>
                  </div>
                </div>

                {/* Генерация КП */}
                <div className="mb-6 rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Генерация коммерческого предложения</div>
                  <div className="flex flex-wrap gap-2">
                    <input value={kpTarget} onChange={(e) => setKpTarget(e.target.value)} placeholder="Название конкурента" className="min-w-[200px] flex-1 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <button onClick={generateKP} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">Сгенерировать КП</button>
                  </div>
                  {kpText && (
                    <div className="mt-3 rounded-lg bg-slate-950 border border-slate-700 p-3">
                      <pre className="text-xs text-slate-300 whitespace-pre-wrap">{kpText}</pre>
                      <button onClick={() => navigator.clipboard.writeText(kpText).then(() => addToast("Скопировано", "success"))} className="mt-2 rounded bg-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-600">Копировать</button>
                    </div>
                  )}
                </div>

                {/* Список отзывов */}
                {reviewsList.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Негативные отзывы о конкурентах</h3>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {reviewsList.map((r, i) => (
                        <div key={i} className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-bold">{r.competitor}</span>
                            <span className="rounded bg-red-500/20 px-2 py-0.5 text-xs text-red-400">{r.rating}★</span>
                          </div>
                          <div className="text-xs text-slate-400 mb-2">{r.source}</div>
                          <div className="text-xs text-slate-500">Негативных: {r.negative_count}</div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {r.issues.map((issue, idx) => (
                              <span key={idx} className="rounded bg-orange-500/20 px-2 py-0.5 text-xs text-orange-400">{issue}</span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AUTOSMETA */}
          {tab === "autosmeta" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold">Автосмета</h2>
                    <p className="text-sm text-slate-400">Распознавание сметы, сверка со складом, генерация счёта (нал / безнал).</p>
                  </div>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Распознайте смету:</b> нажмите «Распознать смету» — система просканирует документ и вытащит список товаров (или подберёт похожие со склада).</p>
                    <p><b>2. Проверьте позиции:</b> в таблице отображаются распознанные товары с ценами нал/безнал. При необходимости скорректируйте количество.</p>
                    <p><b>3. Выберите тип оплаты:</b> переключатель «Наличные / Безналичные» задаёт формат счёта.</p>
                    <p><b>4. Сгенерируйте счёт:</b> нажмите «Сгенерировать счёт» — система выдаст итоговую сумму и ID счёта.</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-end gap-3 mb-6">
                  <button onClick={recognizeSmeta} disabled={smetaLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{smetaLoading ? "Распознавание..." : "Распознать смету"}</button>
                  <select value={smetaPaymentType} onChange={(e) => setSmetaPaymentType(e.target.value)} className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500">
                    <option value="nal">Наличные</option>
                    <option value="beznal">Безналичные</option>
                  </select>
                  <button onClick={generateInvoice} disabled={smetaItems.length === 0} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400 disabled:opacity-50">Сгенерировать счёт</button>
                </div>

                {/* Результат счёта */}
                {smetaInvoice && (
                  <div className="mb-6 rounded-xl bg-emerald-500/10 p-4 border border-emerald-500/20">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs text-emerald-400">Счёт {smetaInvoice.invoice_id}</div>
                        <div className="text-2xl font-bold text-emerald-400">{money(smetaInvoice.total)}</div>
                        <div className="text-xs text-slate-500">{smetaInvoice.payment_type === "nal" ? "Наличные" : "Безналичные"} · {smetaInvoice.items_count} позиций</div>
                      </div>
                      <button onClick={() => navigator.clipboard.writeText(smetaInvoice.invoice_id).then(() => addToast("Скопировано", "success"))} className="rounded bg-emerald-500/20 px-3 py-1.5 text-xs text-emerald-400 hover:bg-emerald-500/30">Копировать ID</button>
                    </div>
                  </div>
                )}

                {/* Таблица распознанных позиций */}
                {smetaItems.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Распознанные позиции</h3>
                    <div className="overflow-auto rounded-xl border border-slate-700/30">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-3">Товар</th>
                            <th className="px-4 py-3 text-right">Кол-во</th>
                            <th className="px-4 py-3 text-right">Цена нал</th>
                            <th className="px-4 py-3 text-right">Цена безнал</th>
                            <th className="px-4 py-3 text-right">Ед.</th>
                          </tr>
                        </thead>
                        <tbody>
                          {smetaItems.map((item, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-3">{item.name}</td>
                              <td className="px-4 py-3 text-right">{item.quantity}</td>
                              <td className="px-4 py-3 text-right">{money(item.price_nal)}</td>
                              <td className="px-4 py-3 text-right text-slate-400">{money(item.price_beznal)}</td>
                              <td className="px-4 py-3 text-right text-slate-500">{item.unit}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* CONTENT FACTORY */}
          {tab === "content-factory" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold">Контент-фабрика</h2>
                    <p className="text-sm text-slate-400">Генерация SEO-статей для блога, массовая публикация в OpenCart.</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={loadContentQueue} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">Очередь ({contentQueue.length})</button>
                  </div>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Задайте количество:</b> укажите, сколько SEO-статей нужно сгенерировать (от 1 до 20 за раз).</p>
                    <p><b>2. Сгенерируйте:</b> нажмите «Сгенерировать» — ИИ создаст уникальные статьи на строительную тематику.</p>
                    <p><b>3. Просмотрите:</b> каждая статья отображается карточкой с заголовком и текстом. Проверьте качество.</p>
                    <p><b>4. Публикуйте:</b> нажмите «Опубликовать» — статья отправится в блог OpenCart. Очередь показывает неопубликованные статьи.</p>
                  </div>
                </div>

                <div className="flex flex-wrap items-end gap-3 mb-6">
                  <div>
                    <div className="mb-1 text-xs text-slate-500">Количество статей</div>
                    <input type="number" value={contentCount} onChange={(e) => setContentCount(e.target.value)} min={1} max={20} className="w-24 rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                  </div>
                  <button onClick={generateContent} disabled={contentLoading} className="rounded-lg bg-emerald-500 px-5 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{contentLoading ? "Генерация..." : "Сгенерировать"}</button>
                </div>

                {/* Сгенерированные статьи */}
                {contentArticles.length > 0 && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Сгенерированные статьи</h3>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {contentArticles.map((a) => (
                        <div key={a.id} className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                          <div className="font-bold mb-2">{a.title}</div>
                          <div className="text-xs text-slate-400 line-clamp-4">{a.text}</div>
                          <button onClick={() => publishArticle(a.id)} className="mt-3 rounded bg-emerald-500/20 px-3 py-1 text-xs text-emerald-400 hover:bg-emerald-500/30">Опубликовать</button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Очередь */}
                {contentQueue.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Очередь на публикацию ({contentQueue.length})</h3>
                    <div className="space-y-2">
                      {contentQueue.map((a) => (
                        <div key={a.id} className="flex items-center justify-between rounded-xl bg-slate-800/50 p-3 border border-slate-700/30">
                          <span className="text-sm">{a.title}</span>
                          <button onClick={() => publishArticle(a.id)} className="rounded bg-sky-500/20 px-2 py-1 text-xs text-sky-400 hover:bg-sky-500/30">Опубликовать</button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* CLIENTS & OBJECTS */}
          {tab === "clients-objects" && (
            <div className="space-y-6">
              <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
                <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
                  <div>
                    <h2 className="text-lg font-bold">Клиенты и объекты</h2>
                    <p className="text-sm text-slate-400">Управление клиентами, объекты строительства, прогноз потребности материалов.</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={loadClients} disabled={objLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{objLoading ? "Загрузка..." : "Клиенты"}</button>
                    <button onClick={loadObjects} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">Объекты</button>
                  </div>
                </div>

                <div className="mb-4 rounded-lg bg-sky-500/10 border border-sky-500/20 p-4 text-sm text-slate-300">
                  <div className="font-bold text-sky-400 mb-1">Как работать с разделом</div>
                  <div className="text-xs space-y-1">
                    <p><b>1. Загрузите клиентов:</b> нажмите «Клиенты» — система подтянет список покупателей из OpenCart.</p>
                    <p><b>2. Добавьте объект:</b> введите название, адрес, клиента и текущий этап строительства → «Добавить объект».</p>
                    <p><b>3. Прогноз материалов:</b> выберите этап (фундамент, отделка и т.д.) и площадь м² → нажмите «Прогноз потребности».</p>
                    <p><b>4. Управляйте объектами:</b> нажмите «Объекты» чтобы увидеть все стройки и их текущий статус.</p>
                  </div>
                </div>

                {/* Добавление объекта */}
                <div className="mb-6 rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                  <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Добавить объект строительства</div>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                    <input value={objName} onChange={(e) => setObjName(e.target.value)} placeholder="Название объекта" className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <input value={objAddress} onChange={(e) => setObjAddress(e.target.value)} placeholder="Адрес" className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <input value={objClient} onChange={(e) => setObjClient(e.target.value)} placeholder="Клиент" className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                    <select value={objStage} onChange={(e) => setObjStage(e.target.value)} className="rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500">
                      <option value="фундамент">Фундамент</option>
                      <option value="каркас">Каркас</option>
                      <option value="кровля">Кровля</option>
                      <option value="отделка">Отделка</option>
                      <option value="инженерия">Инженерия</option>
                      <option value="сдача">Сдача</option>
                    </select>
                  </div>
                  <div className="mt-2 flex gap-2">
                    <button onClick={addObject} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">Добавить объект</button>
                    <button onClick={forecastDemand} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-bold text-white hover:bg-sky-400">Прогноз потребности</button>
                  </div>
                </div>

                {/* Прогноз */}
                {objForecast && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Прогноз потребности (этап: {objStage}, {objArea} м²)</h3>
                    <div className="overflow-auto rounded-xl border border-slate-700/30">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-3">Материал</th>
                            <th className="px-4 py-3 text-right">Количество</th>
                            <th className="px-4 py-3 text-right">Ед.</th>
                          </tr>
                        </thead>
                        <tbody>
                          {objForecast.forecast.map((item, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-3">{item.name}</td>
                              <td className="px-4 py-3 text-right font-medium">{Math.round(item.quantity * 100) / 100}</td>
                              <td className="px-4 py-3 text-right text-slate-400">{item.unit}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Объекты */}
                {objectsList.length > 0 && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Объекты строительства</h3>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      {objectsList.map((o) => (
                        <div key={o.object_id} className="rounded-xl bg-slate-800/50 p-4 border border-slate-700/30">
                          <div className="font-bold mb-1">{o.name}</div>
                          <div className="text-xs text-slate-400">{o.address || "—"}</div>
                          <div className="text-xs text-slate-500 mt-1">Клиент: {o.client_name || "—"}</div>
                          <div className="mt-2 rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-400 inline-block">{o.stage}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Клиенты */}
                {clientsList.length > 0 && (
                  <div>
                    <h3 className="mb-3 text-sm font-bold uppercase tracking-wider text-slate-500">Клиенты ({clientsList.length})</h3>
                    <div className="overflow-auto rounded-xl border border-slate-700/30">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-800/50 text-left text-xs uppercase tracking-wider text-slate-400">
                            <th className="px-4 py-3">Имя</th>
                            <th className="px-4 py-3">Email</th>
                            <th className="px-4 py-3">Телефон</th>
                          </tr>
                        </thead>
                        <tbody>
                          {clientsList.map((c, i) => (
                            <tr key={i} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                              <td className="px-4 py-3">{c.firstname || ""} {c.lastname || ""}</td>
                              <td className="px-4 py-3 text-slate-400">{c.email || "—"}</td>
                              <td className="px-4 py-3 text-slate-400">{c.telephone || "—"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SITE BUILDER */}
          {tab === "site-builder" && <SiteBuilder addToast={addToast} />}

          {/* YANDEX WEBMASTER */}
          {tab === "webmaster" && <YandexWebmaster />}

          {/* SYNC */}
          {tab === "sync" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2"><RefreshCw size={22} className="text-emerald-400"/>Live Sync</h2>
                  <p className="text-sm text-slate-400 mt-1">Мгновенная синхронизация файлов с production-хостингом stroiapp.ru</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${syncWatchRunning ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                    <span className={`h-2 w-2 rounded-full ${syncWatchRunning ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`}></span>
                    {syncWatchRunning ? "Watch активен" : "Watch выключен"}
                  </span>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-3">
                {/* Full Sync Card */}
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6 space-y-4">
                  <div className="flex items-center gap-2 text-emerald-400">
                    <Upload size={20} />
                    <h3 className="font-bold">Full Sync</h3>
                  </div>
                  <p className="text-sm text-slate-400">Разовая загрузка всех новых файлов на хостинг и очистка кэша.</p>
                  <button
                    onClick={startFullSync}
                    disabled={syncRunning || syncLoading}
                    className="w-full rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {syncRunning ? <RefreshCw size={16} className="animate-spin" /> : <Upload size={16} />}
                    {syncRunning ? "Синхронизация..." : "Запустить Full Sync"}
                  </button>
                </div>

                {/* Watch Mode Card */}
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6 space-y-4">
                  <div className="flex items-center gap-2 text-sky-400">
                    <MonitorCheck size={20} />
                    <h3 className="font-bold">Watch Mode</h3>
                  </div>
                  <p className="text-sm text-slate-400">Автоматическая синхронизация при каждом сохранении файла.</p>
                  <div className="flex gap-2">
                    {!syncWatchRunning ? (
                      <button
                        onClick={startWatchMode}
                        disabled={syncLoading}
                        className="flex-1 rounded-lg bg-sky-500 px-4 py-2.5 text-sm font-bold text-white hover:bg-sky-400 disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <RefreshCw size={16} />
                        Запустить Watch
                      </button>
                    ) : (
                      <button
                        onClick={stopWatchMode}
                        disabled={syncLoading}
                        className="flex-1 rounded-lg bg-red-500 px-4 py-2.5 text-sm font-bold text-white hover:bg-red-400 disabled:opacity-50 flex items-center justify-center gap-2"
                      >
                        <X size={16} />
                        Остановить Watch
                      </button>
                    )}
                  </div>
                </div>

                {/* Status Card */}
                <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6 space-y-4">
                  <div className="flex items-center gap-2 text-amber-400">
                    <Settings size={20} />
                    <h3 className="font-bold">Статус</h3>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Хостинг:</span>
                      <span className="text-emerald-400 font-medium">stroiapp.ru</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Watch режим:</span>
                      <span className={syncWatchRunning ? "text-emerald-400" : "text-slate-500"}>{syncWatchRunning ? "Активен" : "Выключен"}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Full sync:</span>
                      <span className={syncRunning ? "text-amber-400" : "text-slate-500"}>{syncRunning ? "В процессе" : "Готов"}</span>
                    </div>
                  </div>
                  <button
                    onClick={checkSyncStatus}
                    disabled={syncLoading}
                    className="w-full rounded-lg bg-slate-800 px-4 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 border border-slate-700 disabled:opacity-50"
                  >
                    Обновить статус
                  </button>
                </div>
              </div>

              {/* Log Output */}
              {(syncLog.length > 0 || syncRunning) && (
                <div className="rounded-2xl border border-slate-700/30 bg-slate-950 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                      <FileText size={14} />
                      Лог синхронизации
                    </h3>
                    <button onClick={() => setSyncLog([])} className="text-xs text-slate-500 hover:text-slate-300">Очистить</button>
                  </div>
                  <div className="rounded-lg bg-slate-900 border border-slate-800 p-3 h-64 overflow-auto font-mono text-xs space-y-1">
                    {syncLog.map((line, i) => (
                      <div key={i} className={`${line.includes("UPLOADED") ? "text-emerald-400" : line.includes("ERROR") ? "text-red-400" : line.includes("DONE") ? "text-sky-400 font-bold" : "text-slate-400"}`}>
                        {line}
                      </div>
                    ))}
                    {syncRunning && <div className="text-amber-400 animate-pulse">⏳ Синхронизация выполняется...</div>}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TOOLS */}
          {tab === "tools" && (
            <div className="grid gap-6 lg:grid-cols-2">
              <ToolCard icon={Send} title="Telegram" desc="Тестовое уведомление менеджеру.">
                <button onClick={() => apiPost("/telegram/test", {}).then((r) => alert("Статус: " + r.status))} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">Отправить</button>
              </ToolCard>
              <ToolCard icon={FileCheck} title="DaData — проверка ИНН" desc="Валидация ИНН, подтягивание названия и адреса.">
                <div className="flex gap-2">
                  <input value={innQuery} onChange={(e) => setInnQuery(e.target.value)} placeholder="ИНН" className="w-48 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-emerald-500" />
                  <button onClick={validateInn} disabled={innLoading} className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{innLoading ? "..." : "Проверить"}</button>
                </div>
                {innResult?.status === "found" && (
                  <div className="mt-3 rounded-lg bg-slate-950 p-3 text-sm space-y-1">
                    <div><span className="text-slate-400">Название:</span> {innResult.name}</div>
                    <div><span className="text-slate-400">ИНН/КПП:</span> {innResult.inn} / {innResult.kpp}</div>
                    <div><span className="text-slate-400">Адрес:</span> {innResult.address}</div>
                  </div>
                )}
              </ToolCard>
            </div>
          )}
        </div>
      </main>
      <ToastContainer toasts={toasts} remove={removeToast} />

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 flex items-stretch border-t border-slate-800 bg-slate-900/95 backdrop-blur md:hidden" style={{ paddingBottom: "env(safe-area-inset-bottom)" }}>
        {["dashboard", "products", "opencart", "ai-seo"].map((id) => {
          const t = TABS.find((x) => x.id === id);
          const Icon = t.icon;
          const active = tab === id;
          return (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex flex-1 flex-col items-center gap-1 py-2.5 text-[10px] font-medium transition-colors ${active ? "text-emerald-400" : "text-slate-500"}`}
            >
              <Icon size={20} />
              {t.label}
            </button>
          );
        })}
        <button
          onClick={() => setMobileMenu(true)}
          className="flex flex-1 flex-col items-center gap-1 py-2.5 text-[10px] font-medium text-slate-500"
        >
          <Menu size={20} />
          Меню
        </button>
      </nav>
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, color }) {
  return (
    <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-5">
      <div className="mb-2 flex items-center gap-2 text-slate-400"><Icon size={18} /><span className="text-xs font-medium uppercase tracking-wider">{label}</span></div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
    </div>
  );
}

function ToolCard({ icon: Icon, title, desc, children }) {
  return (
    <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-6">
      <div className="mb-3 flex items-center gap-2 text-emerald-400"><Icon size={20} /><h3 className="font-bold">{title}</h3></div>
      <p className="mb-4 text-sm text-slate-400">{desc}</p>
      {children}
    </div>
  );
}

function CategoryNode({ node, level = 0, onSelect, selectedId }) {
  const isSelected = selectedId === node.category_id;
  return (
    <div>
      <button
        onClick={() => onSelect && onSelect(node.category_id)}
        className={`w-full rounded-lg px-3 py-2 text-left hover:bg-slate-900 ${isSelected ? 'bg-slate-900 ring-1 ring-emerald-500/50' : 'bg-slate-950'}`}
        style={{ marginLeft: level * 14 }}
      >
        <span className="text-slate-500">#{node.category_id}</span> <span>{node.name || "Без названия"}</span>
      </button>
      {(node.children || []).map((child) => (
        <CategoryNode key={child.category_id} node={child} level={level + 1} onSelect={onSelect} selectedId={selectedId} />
      ))}
    </div>
  );
}

function ToastContainer({ toasts, remove }) {
  return (
    <div className="fixed bottom-20 right-4 z-50 flex flex-col gap-2 md:bottom-6 md:right-6">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium shadow-lg backdrop-blur ${
            toast.type === 'error'
              ? 'bg-red-500/90 text-white border border-red-400/30'
              : 'bg-emerald-500/90 text-slate-950 border border-emerald-400/30'
          } animate-in`}
          style={{ animationDuration: '0.3s' }}
        >
          {toast.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle size={18} />}
          <span>{toast.message}</span>
          <button onClick={() => remove(toast.id)} className="ml-2 opacity-70 hover:opacity-100"><X size={14} /></button>
        </div>
      ))}
    </div>
  );
}

function ProductTable({ rows, loading, onUpdateCosts, onSyncOpenCart }) {
  const [drafts, setDrafts] = React.useState({});
  const [savingSku, setSavingSku] = React.useState("");
  const [syncingSku, setSyncingSku] = React.useState("");

  const valueFor = (row, field) => drafts[row.sku]?.[field] ?? row[field] ?? "";
  const setDraft = (row, field, value) => setDrafts((c) => ({ ...c, [row.sku]: { cost_price_cash: valueFor(row, "cost_price_cash"), cost_price_cashless: valueFor(row, "cost_price_cashless"), retail_price: valueFor(row, "retail_price"), wholesale_price: valueFor(row, "wholesale_price"), ...c[row.sku], [field]: value } }));

  async function save(row) {
    setSavingSku(row.sku);
    try {
      await onUpdateCosts(row.sku, valueFor(row, "cost_price_cash"), valueFor(row, "cost_price_cashless"), valueFor(row, "retail_price"), valueFor(row, "wholesale_price"));
      setDrafts((c) => { const n = { ...c }; delete n[row.sku]; return n; });
    } finally { setSavingSku(""); }
  }

  async function sync(row) {
    setSyncingSku(row.sku);
    try {
      await onSyncOpenCart(row.sku);
    } finally { setSyncingSku(""); }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-700/30 glass glass-hover">
      {loading ? <div className="p-6 text-slate-400">Загрузка...</div> : (
        <div className="max-h-[calc(100dvh-220px)] overflow-auto pb-20 md:pb-0">
          <table className="w-full text-left text-sm">
            <thead className="sticky top-0 bg-slate-950 text-xs font-semibold uppercase text-slate-400">
              <tr><th className="px-4 py-3">SKU</th><th className="px-4 py-3">Товар</th><th className="px-4 py-3">Приход нал</th><th className="px-4 py-3">Приход безнал</th><th className="px-4 py-3">Розница</th><th className="px-4 py-3">Безнал продажа</th><th className="px-4 py-3">ROI</th><th className="px-4 py-3"></th></tr>
            </thead>
            <tbody>
              {rows.slice(0, 200).map((row) => (
                <tr key={row.sku} className="border-t border-slate-800/50 hover:bg-slate-800/30">
                  <td className="px-4 py-2.5 font-mono text-xs">{row.sku}</td>
                  <td className="max-w-[280px] px-4 py-2.5 truncate" title={row.name}>{row.name}</td>
                  <td className="px-4 py-2.5"><input type="number" value={valueFor(row, "cost_price_cash")} onChange={(e) => setDraft(row, "cost_price_cash", e.target.value)} className="w-20 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                  <td className="px-4 py-2.5"><input type="number" value={valueFor(row, "cost_price_cashless")} onChange={(e) => setDraft(row, "cost_price_cashless", e.target.value)} className="w-20 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                  <td className="px-4 py-2.5"><input type="number" value={valueFor(row, "retail_price")} onChange={(e) => setDraft(row, "retail_price", e.target.value)} className="w-24 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                  <td className="px-4 py-2.5"><input type="number" value={valueFor(row, "wholesale_price")} onChange={(e) => setDraft(row, "wholesale_price", e.target.value)} className="w-24 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs outline-none focus:border-emerald-500" /></td>
                  <td className={`px-4 py-2.5 font-semibold ${roiColor(row.roi)}`}>{row.roi}%</td>
                  <td className="px-4 py-2.5">
                    <div className="flex gap-1">
                      <button onClick={() => save(row)} disabled={savingSku === row.sku} className="rounded bg-emerald-500 px-2 py-1 text-xs font-bold text-slate-950 disabled:opacity-50">{savingSku === row.sku ? "..." : "OK"}</button>
                      <button onClick={() => sync(row)} disabled={syncingSku === row.sku} className="rounded bg-sky-500 px-2 py-1 text-xs font-bold text-slate-950 disabled:opacity-50">{syncingSku === row.sku ? "..." : "OC"}</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function AiSeoPanel({ products, setProducts, filter, setFilter, loading, setLoading, progress, setProgress, log, setLog, preview, setPreview, addToast }) {
  const [selectedIds, setSelectedIds] = React.useState(new Set());
  const [search, setSearch] = React.useState("");
  const [processingId, setProcessingId] = React.useState(null);

  React.useEffect(() => {
    setLoading(true);
    apiGet("/ai-seo/products")
      .then((data) => {
        setProducts(data.products || []);
        setLoading(false);
      })
      .catch((err) => {
        addToast("Ошибка загрузки товаров: " + err.message, "error");
        setLoading(false);
      });
  }, []);

  const withoutDesc = React.useMemo(() => products.filter((p) => !p.has_description), [products]);
  const withoutMeta = React.useMemo(() => products.filter((p) => !p.has_meta), [products]);

  const filtered = React.useMemo(() => {
    let list = products;
    if (filter === "no_desc") list = withoutDesc;
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter((p) => p.name.toLowerCase().includes(q));
    }
    return list;
  }, [products, filter, search]);

  function toggleAll(checked) {
    if (checked) setSelectedIds(new Set(filtered.map((p) => String(p.product_id))));
    else setSelectedIds(new Set());
  }

  function toggleOne(id, checked) {
    const next = new Set(selectedIds);
    if (checked) next.add(String(id));
    else next.delete(String(id));
    setSelectedIds(next);
  }

  async function generateOne(productId) {
    setProcessingId(productId);
    setLog((prev) => [...prev, `ID ${productId}: генерация...`]);
    try {
      const data = await apiPost("/opencart/products/generateSeo", { product_id: productId });
      if (data.error) {
        setLog((prev) => [...prev, `ID ${productId}: ОШИБКА — ${data.error}`]);
        setProgress((p) => ({ ...p, fail: p.fail + 1 }));
        addToast(`ID ${productId}: ошибка`, "error");
      } else {
        setLog((prev) => [...prev, `ID ${productId}: OK — ${data.meta_title?.slice(0, 40) || ""}`]);
        setProducts((prev) => prev.map((p) => (p.product_id === productId ? { ...p, has_description: true, has_meta: true } : p)));
        setProgress((p) => ({ ...p, ok: p.ok + 1 }));
        setPreview(data);
        addToast(`ID ${productId}: SEO сгенерировано`, "success");
      }
    } catch (err) {
      setLog((prev) => [...prev, `ID ${productId}: ОШИБКА — ${err.message}`]);
      setProgress((p) => ({ ...p, fail: p.fail + 1 }));
      addToast(`ID ${productId}: ошибка сети`, "error");
    } finally {
      setProcessingId(null);
    }
  }

  async function generateBatch(limit, source = "selected") {
    let ids;
    if (source === "all") {
      ids = products.map((p) => String(p.product_id));
      if (limit > 0) ids = ids.slice(0, limit);
    } else if (source === "all_no_desc") {
      ids = withoutDesc.map((p) => String(p.product_id));
      if (limit > 0) ids = ids.slice(0, limit);
    } else {
      ids = Array.from(selectedIds).slice(0, limit);
    }
    if (ids.length === 0) {
      addToast("Нет товаров для генерации", "error");
      return;
    }
    setProgress({ current: 0, total: ids.length, ok: 0, fail: 0 });
    setLog([`=== Начало: ${ids.length} товаров ===`]);
    for (let i = 0; i < ids.length; i++) {
      await generateOne(Number(ids[i]));
      setProgress((p) => ({ ...p, current: i + 1 }));
      await new Promise((r) => setTimeout(r, 400));
    }
    addToast(`Готово: ${ids.length} товаров`, "success");
  }

  const pct = progress.total ? Math.round((progress.current / progress.total) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <div className="mb-1 flex items-center gap-2 text-slate-400"><Package size={16} /><span className="text-xs font-medium uppercase tracking-wider">Всего товаров</span></div>
          <div className="text-2xl font-bold text-white">{products.length}</div>
        </div>
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <div className="mb-1 flex items-center gap-2 text-slate-400"><FileCheck size={16} /><span className="text-xs font-medium uppercase tracking-wider">С описанием</span></div>
          <div className="text-2xl font-bold text-emerald-400">{products.length - withoutDesc.length}</div>
        </div>
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <div className="mb-1 flex items-center gap-2 text-slate-400"><AlertCircle size={16} /><span className="text-xs font-medium uppercase tracking-wider">Без описания</span></div>
          <div className="text-2xl font-bold text-orange-400">{withoutDesc.length}</div>
        </div>
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <div className="mb-1 flex items-center gap-2 text-slate-400"><Search size={16} /><span className="text-xs font-medium uppercase tracking-wider">Без meta</span></div>
          <div className="text-2xl font-bold text-sky-400">{withoutMeta.length}</div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
        <div className="flex flex-wrap items-center gap-3">
          <button onClick={() => setFilter("all")} className={`rounded-lg px-3 py-2 text-sm font-bold ${filter === "all" ? "bg-emerald-500 text-slate-950" : "bg-slate-800 text-slate-200 hover:bg-slate-700"}`}>Все</button>
          <button onClick={() => setFilter("no_desc")} className={`rounded-lg px-3 py-2 text-sm font-bold ${filter === "no_desc" ? "bg-emerald-500 text-slate-950" : "bg-slate-800 text-slate-200 hover:bg-slate-700"}`}>Без описания</button>
          <div className="h-8 w-px bg-slate-700" />
          <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2">
            <Search size={14} className="text-slate-500" />
            <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Поиск по названию..." className="bg-transparent text-sm outline-none text-slate-200 placeholder:text-slate-500 w-48" />
          </div>
          <div className="flex-1" />
          <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold">Пакет:</span>
          <button onClick={() => generateBatch(10)} disabled={selectedIds.size === 0} className="rounded-lg bg-sky-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed">10</button>
          <button onClick={() => generateBatch(50)} disabled={selectedIds.size === 0} className="rounded-lg bg-sky-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed">50</button>
          <button onClick={() => generateBatch(100)} disabled={selectedIds.size === 0} className="rounded-lg bg-sky-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed">100</button>
          <button onClick={() => generateBatch(0, "all_no_desc")} className="rounded-lg bg-amber-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-amber-400">Все без описания</button>
          <button onClick={() => { if (window.confirm(`Сгенерировать SEO для ВСЕХ ${products.length} товаров? Существующие описания и meta будут перезаписаны.`)) generateBatch(0, "all"); }} className="rounded-lg bg-rose-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-rose-400">Все товары</button>
        </div>
      </div>

      {/* Progress */}
      {progress.total > 0 && (
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
            <span>Прогресс генерации</span>
            <span>{progress.current} / {progress.total}</span>
          </div>
          <div className="h-8 rounded-lg bg-slate-800 overflow-hidden">
            <div className="h-full bg-emerald-500 text-xs font-bold text-slate-950 flex items-center justify-center transition-all duration-300" style={{ width: pct + "%" }}>{pct}%</div>
          </div>
          <div className="mt-2 flex gap-4 text-xs text-slate-400">
            <span className="text-emerald-400">OK: {progress.ok}</span>
            <span className="text-red-400">Fail: {progress.fail}</span>
            <span>Осталось: {progress.total - progress.current}</span>
          </div>
        </div>
      )}

      {/* Log */}
      {log.length > 0 && (
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Лог генерации</span>
            <button onClick={() => setLog([])} className="text-xs text-slate-500 hover:text-slate-300">Очистить</button>
          </div>
          <div className="max-h-48 overflow-auto rounded-lg bg-slate-950 p-3 text-xs font-mono text-slate-300 space-y-0.5">
            {log.map((l, i) => (
              <div key={i} className={l.includes("ОШИБКА") ? "text-red-400" : l.includes("OK") ? "text-emerald-400" : "text-slate-400"}>{l}</div>
            ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-700/30 glass glass-hover">
        {loading ? (
          <div className="p-8 text-center text-slate-400">Загрузка товаров...</div>
        ) : (
          <div className="max-h-[calc(100dvh-420px)] overflow-auto pb-20 md:pb-0">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-slate-950 text-xs font-semibold uppercase text-slate-400">
                <tr>
                  <th className="px-4 py-3 w-px"><input type="checkbox" onChange={(e) => toggleAll(e.target.checked)} /></th>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Название товара</th>
                  <th className="px-4 py-3 w-px text-center">Описание</th>
                  <th className="px-4 py-3 w-px text-center">Meta</th>
                  <th className="px-4 py-3 w-px">Действие</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan="6" className="px-4 py-8 text-center text-slate-500">Товары не найдены</td></tr>
                ) : (
                  filtered.map((p) => (
                    <tr key={p.product_id} className={`border-t border-slate-800/50 hover:bg-slate-800/30 transition-colors ${processingId === p.product_id ? "bg-slate-800/50" : ""}`}>
                      <td className="px-4 py-2.5"><input type="checkbox" checked={selectedIds.has(String(p.product_id))} onChange={(e) => toggleOne(p.product_id, e.target.checked)} /></td>
                      <td className="px-4 py-2.5 font-mono text-xs text-slate-500">{p.product_id}</td>
                      <td className="max-w-[380px] px-4 py-2.5 truncate text-slate-200" title={p.name}>{p.name}</td>
                      <td className="px-4 py-2.5 text-center">{p.has_description ? <CheckCircle size={16} className="inline text-emerald-400" /> : <AlertCircle size={16} className="inline text-orange-400" />}</td>
                      <td className="px-4 py-2.5 text-center">{p.has_meta ? <CheckCircle size={16} className="inline text-emerald-400" /> : <AlertCircle size={16} className="inline text-orange-400" />}</td>
                      <td className="px-4 py-2.5">
                        <button onClick={() => generateOne(p.product_id)} disabled={processingId === p.product_id} className="rounded bg-emerald-500 px-2.5 py-1.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed">{processingId === p.product_id ? "..." : "Generate"}</button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
        <div className="border-t border-slate-800/50 px-4 py-2 text-xs text-slate-500">
          Показано: {filtered.length} / {products.length}
        </div>
      </div>

      {/* Preview Modal */}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => setPreview(null)}>
          <div className="max-h-[85vh] w-[92%] max-w-3xl overflow-auto rounded-2xl border border-slate-700/50 bg-slate-900 p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-5 flex items-center justify-between border-b border-slate-700 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white">{preview.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">ID: {preview.product_id}</p>
              </div>
              <button onClick={() => setPreview(null)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"><X size={20} /></button>
            </div>
            <div className="space-y-4 text-sm">
              <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Meta Title</div>
                <div className="text-slate-200">{preview.meta_title}</div>
              </div>
              <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Meta Description</div>
                <div className="text-slate-200">{preview.meta_description}</div>
              </div>
              <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Keywords</div>
                <div className="text-slate-200">{preview.meta_keyword}</div>
              </div>
              <div className="rounded-lg bg-slate-800/50 p-4 border border-slate-700/30">
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">SEO Описание</div>
                <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">{preview.description}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ProductsTreePanel({ catTree, setCatTree, catProducts, setCatProducts, selCatId, setSelCatId, selProduct, setSelProduct, prodSearch, setProdSearch, catLoading, setCatLoading, addToast }) {
  const [expanded, setExpanded] = React.useState(new Set());
  const [editingProduct, setEditingProduct] = React.useState(null);
  const [savingId, setSavingId] = React.useState(null);
  const [showAddForm, setShowAddForm] = React.useState(false);
  const [addForm, setAddForm] = React.useState({ name: "", sku: "", model: "", cash_price: "", non_cash_price: "", price: "", quantity: "1" });
  const [detailEdit, setDetailEdit] = React.useState(false);
  const [detailForm, setDetailForm] = React.useState(null);
  const [uploadingImg, setUploadingImg] = React.useState(false);
  const [generatingSeo, setGeneratingSeo] = React.useState(false);
  const [allAttributes, setAllAttributes] = React.useState([]);
  const [productAttrs, setProductAttrs] = React.useState([]);
  const [savingAttrs, setSavingAttrs] = React.useState(false);
  const [catOpen, setCatOpen] = React.useState(false);

  const MARKUP = 1.285; // 28.5%

  React.useEffect(() => {
    setCatLoading(true);
    apiGet("/opencart/categories/list")
      .then((data) => {
        const cats = data.categories || [];
        const map = {};
        const tree = [];
        cats.forEach((c) => { c.children = []; map[c.category_id] = c; });
        cats.forEach((c) => {
          if (c.parent_id && c.parent_id !== "0" && map[c.parent_id]) map[c.parent_id].children.push(c);
          else tree.push(c);
        });
        if (data.status === "error") { addToast("Категории: " + (data.detail || "ошибка"), "error"); setCatLoading(false); return; }
        setCatTree(tree);
        setCatLoading(false);
        if (!selCatId && tree.length) loadCategory(tree[0].category_id);
      })
      .catch((err) => { addToast("Ошибка загрузки категорий: " + err.message, "error"); setCatLoading(false); });
  }, []);

  function loadCategory(categoryId) {
    setSelCatId(categoryId);
    setCatOpen(false);
    setCatLoading(true);
    apiGet("/opencart/products/byCategory?category_id=" + categoryId)
      .then((data) => {
        if (data.status === "error") { addToast("Товары: " + (data.detail || "ошибка"), "error"); setCatProducts([]); setCatLoading(false); return; }
        setCatProducts(data.products || []); setCatLoading(false);
      })
      .catch((err) => { addToast("Ошибка загрузки товаров: " + err.message, "error"); setCatProducts([]); setCatLoading(false); });
  }

  function toggleExpand(id) { const next = new Set(expanded); if (next.has(id)) next.delete(id); else next.add(id); setExpanded(next); }

  function renderTree(nodes, level = 0) {
    return nodes.map((node) => {
      const hasChildren = (node.children || []).length > 0;
      const isExpanded = expanded.has(node.category_id);
      const isSelected = selCatId === node.category_id;
      return (
        <div key={node.category_id}>
          <button onClick={() => { loadCategory(node.category_id); if (hasChildren) toggleExpand(node.category_id); }} className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${isSelected ? "bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/50" : "text-slate-300 hover:bg-slate-800"}`} style={{ paddingLeft: 12 + level * 16 }}>
            {hasChildren && <span onClick={(e) => { e.stopPropagation(); toggleExpand(node.category_id); }} className="text-slate-500 hover:text-slate-300 cursor-pointer">{isExpanded ? "▼" : "▶"}</span>}
            {!hasChildren && <span className="w-4" />}
            <Folder size={14} className={isSelected ? "text-emerald-400" : "text-slate-500"} />
            <span className="truncate">{node.name}</span>
            <span className="ml-auto text-xs text-slate-500">#{node.category_id}</span>
          </button>
          {hasChildren && isExpanded && <div>{renderTree(node.children, level + 1)}</div>}
        </div>
      );
    });
  }

  function startEdit(p) { setEditingProduct({ ...p, _cash: p.cash_price || "", _nonCash: p.non_cash_price || "", _price: p.price || "", _priceNonCash: p.price_non_cash || "" }); }

  function updateEditPrice(val) {
    const price = parseFloat(val) || 0;
    const priceNonCash = +(price * MARKUP).toFixed(2);
    setEditingProduct((prev) => ({ ...prev, _price: val, _priceNonCash: String(priceNonCash) }));
  }

  async function saveProduct(ed) {
    if (!ed || !ed.product_id) return;
    setSavingId(ed.product_id);
    const cash = parseFloat(ed._cash) || 0;
    const nonCash = parseFloat(ed._nonCash) || 0;
    const price = parseFloat(ed._price) || 0;
    const priceNonCash = parseFloat(ed._priceNonCash) || 0;
    try {
      await apiPost("/opencart/products/update", { product_id: Number(ed.product_id), cash_price: cash, non_cash_price: nonCash, price, price_non_cash: priceNonCash });
      setCatProducts((prev) => prev.map((p) => (p.product_id === ed.product_id ? { ...p, cash_price: cash, non_cash_price: nonCash, price, price_non_cash: priceNonCash } : p)));
      addToast("Цены сохранены", "success");
      setEditingProduct(null);
    } catch (err) {
      addToast("Ошибка сохранения: " + err.message, "error");
    } finally {
      setSavingId(null);
    }
  }

  async function fetchFullProduct(p) {
    try {
      const full = await apiGet("/opencart/products/" + p.product_id);
      if (full && full.product_id) return { ...p, ...full };
    } catch {}
    return p;
  }

  async function openProductDetail(p) {
    setSelProduct(p);
    loadProductAttributes(p.product_id);
    const full = await fetchFullProduct(p);
    setSelProduct((prev) => (prev && prev.product_id === p.product_id ? full : prev));
  }

  async function openDetailEdit(p) {
    const full = p.description === undefined ? await fetchFullProduct(p) : p;
    setDetailEdit(true);
    loadProductAttributes(p.product_id);
    setDetailForm({
      product_id: full.product_id,
      name: full.name || "",
      sku: full.sku || "",
      model: full.model || "",
      cash_price: full.cash_price || "",
      non_cash_price: full.non_cash_price || "",
      price: full.price || "",
      price_non_cash: full.price_non_cash || "",
      quantity: full.quantity || "",
      description: stripHtml(full.description || ""),
      meta_title: full.meta_title || "",
      meta_description: full.meta_description || "",
      meta_keyword: full.meta_keyword || "",
      image: full.image || "",
      image_url: full.image_url || "",
    });
  }

  function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || "";
  }

  function updateDetailPrice(val) {
    const price = parseFloat(val) || 0;
    const priceNonCash = +(price * MARKUP).toFixed(2);
    setDetailForm((prev) => ({ ...prev, price: val, price_non_cash: String(priceNonCash) }));
  }

  async function uploadImage(file) {
    if (!file) return;
    setUploadingImg(true);
    try {
      const data = await apiUpload("/opencart/images/upload", file);
      if (data.status === "uploaded" || data.path) {
        setDetailForm((prev) => ({ ...prev, image: data.path, image_url: "" }));
        addToast("Фото загружено", "success");
      } else {
        addToast("Ошибка загрузки фото", "error");
      }
    } catch (err) {
      addToast("Ошибка загрузки фото: " + err.message, "error");
    } finally {
      setUploadingImg(false);
    }
  }

  async function saveDetail() {
    if (!detailForm || !detailForm.product_id) return;
    setSavingId(detailForm.product_id);
    const payload = {
      product_id: Number(detailForm.product_id),
      name: detailForm.name,
      sku: detailForm.sku,
      model: detailForm.model,
      cash_price: parseFloat(detailForm.cash_price) || 0,
      non_cash_price: parseFloat(detailForm.non_cash_price) || 0,
      price: parseFloat(detailForm.price) || 0,
      price_non_cash: parseFloat(detailForm.price_non_cash) || 0,
      quantity: parseInt(detailForm.quantity) || 0,
      description: detailForm.description,
      meta_title: detailForm.meta_title,
      meta_description: detailForm.meta_description,
      meta_keyword: detailForm.meta_keyword,
      image: detailForm.image,
    };
    try {
      await apiPost("/opencart/products/update", payload);
      setCatProducts((prev) => prev.map((p) => (p.product_id === detailForm.product_id ? { ...p, ...payload, image_url: detailForm.image ? (detailForm.image_url || "") : "" } : p)));
      if (selProduct && selProduct.product_id === detailForm.product_id) {
        setSelProduct((prev) => ({ ...prev, ...payload }));
      }
      addToast("Товар сохранён", "success");
      setDetailEdit(false);
      setDetailForm(null);
    } catch (err) {
      addToast("Ошибка сохранения: " + err.message, "error");
    } finally {
      setSavingId(null);
    }
  }

  async function generateSeo(productId) {
    if (!productId) return;
    setGeneratingSeo(true);
    try {
      const data = await apiPost("/opencart/products/generateSeo", { product_id: productId });
      if (data.error) {
        addToast("Ошибка генерации: " + data.error, "error");
      } else {
        setDetailForm((prev) => ({
          ...prev,
          description: data.description || prev.description,
          meta_title: data.meta_title || prev.meta_title,
          meta_description: data.meta_description || prev.meta_description,
          meta_keyword: data.meta_keyword || prev.meta_keyword,
        }));
        if (data.attributes && data.attributes.length) {
          setProductAttrs(data.attributes);
        }
        addToast("Описание, SEO и характеристики сгенерированы", "success");
      }
    } catch (err) {
      addToast("Ошибка генерации: " + err.message, "error");
    } finally {
      setGeneratingSeo(false);
    }
  }

  async function loadAllAttributes() {
    try {
      const data = await apiGet("/opencart/attributes/list");
      setAllAttributes(data.attributes || []);
    } catch (err) {
      console.error("loadAllAttributes", err);
    }
  }

  async function loadProductAttributes(productId) {
    if (!productId) return;
    try {
      const data = await apiGet("/opencart/products/attributes?product_id=" + productId);
      setProductAttrs(data.attributes || []);
    } catch (err) {
      console.error("loadProductAttributes", err);
      setProductAttrs([]);
    }
  }

  async function saveAttributes(productId) {
    if (!productId) return;
    setSavingAttrs(true);
    try {
      const attrs = productAttrs.filter((a) => a.attribute_id && (a.text || "").trim() !== "");
      await apiPost("/opencart/products/updateAttributes", { product_id: productId, attributes: attrs });
      addToast("Характеристики сохранены", "success");
    } catch (err) {
      addToast("Ошибка сохранения характеристик: " + err.message, "error");
    } finally {
      setSavingAttrs(false);
    }
  }

  function addAttributeRow() {
    setProductAttrs((prev) => [...prev, { attribute_id: "", name: "", text: "" }]);
  }

  function removeAttributeRow(index) {
    setProductAttrs((prev) => prev.filter((_, i) => i !== index));
  }

  function updateAttributeRow(index, field, value) {
    setProductAttrs((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      if (field === "attribute_id") {
        const found = allAttributes.find((a) => String(a.attribute_id) === String(value));
        if (found) next[index].name = found.name;
      }
      return next;
    });
  }

  React.useEffect(() => {
    loadAllAttributes();
  }, []);

  async function addProduct() {
    if (!addForm.name || !selCatId) { addToast("Название и категория обязательны", "error"); return; }
    const cash = parseFloat(addForm.cash_price) || 0;
    const nonCash = parseFloat(addForm.non_cash_price) || 0;
    const price = parseFloat(addForm.price) || 0;
    const priceNonCash = price > 0 ? +(price * MARKUP).toFixed(2) : parseFloat(addForm.price_non_cash) || 0;
    const payload = {
      name: addForm.name,
      sku: addForm.sku || "",
      model: addForm.model || "",
      cash_price: cash,
      non_cash_price: nonCash,
      price,
      price_non_cash: priceNonCash,
      quantity: parseInt(addForm.quantity) || 1,
      category_id: selCatId,
      status: 1,
    };
    try {
      await apiPost("/opencart/products/add", payload);
      addToast("Товар добавлен", "success");
      setShowAddForm(false);
      setAddForm({ name: "", sku: "", model: "", cash_price: "", non_cash_price: "", price: "", price_non_cash: "", quantity: "1" });
      loadCategory(selCatId);
    } catch (err) {
      addToast("Ошибка добавления: " + err.message, "error");
    }
  }

  function exportCSV() {
    const rows = catProducts.map((p) => [p.product_id, p.sku || "", `"${p.name}"`, p.cash_price || "", p.non_cash_price || "", p.price || "", p.price_non_cash || "", p.quantity || ""].join(";"));
    const csv = ["ID;SKU;Название;ПриходНал;ПриходБезнал;ПродажаНал;ПродажаБезнал;Остаток", ...rows].join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `products_${selCatId}_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    addToast(`Экспортировано ${rows.length} товаров`, "success");
  }

  function importCSV(file) {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target.result;
      const lines = text.split("\n").filter((l) => l.trim());
      if (lines.length < 2) { addToast("CSV пустой", "error"); return; }
      let ok = 0, fail = 0;
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(";");
        if (cols.length < 5) continue;
        const product_id = parseInt(cols[0].replace(/"/g, ""));
        const cash = parseFloat(cols[3].replace(/"/g, "").replace(",", ".")) || 0;
        const nonCash = parseFloat(cols[4].replace(/"/g, "").replace(",", ".")) || 0;
        const price = parseFloat(cols[5].replace(/"/g, "").replace(",", ".")) || 0;
        const priceNonCash = parseFloat(cols[6].replace(/"/g, "").replace(",", ".")) || 0;
        if (!product_id) continue;
        try {
          await apiPost("/opencart/products/update", { product_id, cash_price: cash, non_cash_price: nonCash, price, price_non_cash: priceNonCash });
          ok++;
        } catch { fail++; }
      }
      addToast(`Импорт: ${ok} OK, ${fail} ошибок`, fail === 0 ? "success" : "error");
      if (selCatId) loadCategory(selCatId);
    };
    reader.readAsText(file);
  }

  const filteredProducts = React.useMemo(() => {
    if (!prodSearch.trim()) return catProducts;
    const q = prodSearch.toLowerCase();
    return catProducts.filter((p) => (p.name || "").toLowerCase().includes(q) || (p.sku || "").toLowerCase().includes(q) || String(p.product_id).includes(q));
  }, [catProducts, prodSearch]);

  return (
    <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
      {/* Sidebar */}
      <div className="space-y-4">
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <button onClick={() => setCatOpen((o) => !o)} className="mb-3 flex w-full items-center gap-2 text-sm font-bold text-slate-200 lg:pointer-events-none">
            <Folder size={16} className="text-emerald-400" />Категории
            {selCatId && <span className="text-xs font-normal text-slate-500">#{selCatId}</span>}
            <span className="ml-auto text-xs text-slate-500 lg:hidden">{catOpen ? "▲ скрыть" : "▼ выбрать"}</span>
          </button>
          {catLoading && catTree.length === 0 ? <div className="text-sm text-slate-400">Загрузка...</div> : (
            <div className={`${catOpen ? "" : "hidden"} lg:block max-h-[50vh] lg:max-h-[calc(100dvh-200px)] overflow-auto space-y-0.5 pb-4 lg:pb-0`}>{renderTree(catTree)}</div>
          )}
        </div>
      </div>

      {/* Main */}
      <div className="space-y-4">
        {/* Toolbar */}
        <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2">
              <Search size={14} className="text-slate-500" />
              <input value={prodSearch} onChange={(e) => setProdSearch(e.target.value)} placeholder="Поиск по товару..." className="bg-transparent text-sm outline-none text-slate-200 placeholder:text-slate-500 w-48" />
            </div>
            <div className="flex-1" />
            <button onClick={() => setShowAddForm(true)} disabled={!selCatId} className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-3 py-2 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-40 disabled:cursor-not-allowed"><Plus size={14} />Добавить</button>
            <button onClick={exportCSV} disabled={catProducts.length === 0} className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-40"><Download size={14} />CSV</button>
            <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700">
              <Upload size={14} />CSV
              <input type="file" accept=".csv" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) importCSV(f); e.target.value = ""; }} />
            </label>
            <span className="text-xs text-slate-500">{filteredProducts.length} товаров</span>
          </div>
        </div>

        {catLoading && catProducts.length === 0 ? (
          <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-8 text-center text-slate-400">Загрузка товаров...</div>
        ) : filteredProducts.length === 0 ? (
          <div className="rounded-2xl border border-slate-700/30 glass glass-hover p-8 text-center text-slate-500">{selCatId ? "В этой категории нет товаров" : "Выберите категорию"}</div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {filteredProducts.map((p) => {
              const isEditing = editingProduct && editingProduct.product_id === p.product_id;
              return (
                <div key={p.product_id} className="rounded-2xl border border-slate-700/30 glass glass-hover p-4 text-left">
                  <div className="flex gap-3">
                    <div className="h-16 w-16 flex-shrink-0 rounded-lg bg-slate-800 overflow-hidden cursor-pointer" onClick={() => openProductDetail(p)}>
                      {p.image_url ? <img src={p.image_url} alt={p.name} className="h-full w-full object-cover" /> : <div className="flex h-full w-full items-center justify-center text-slate-600"><Image size={20} /></div>}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-semibold text-slate-200 cursor-pointer" onClick={() => openProductDetail(p)}>{p.name}</div>
                      <div className="mt-0.5 text-xs text-slate-500">ID: {p.product_id} {p.sku ? "| SKU: " + p.sku : ""}</div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {p.has_description ? <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-bold text-emerald-400">SEO</span> : <span className="rounded bg-orange-500/20 px-1.5 py-0.5 text-[10px] font-bold text-orange-400">NO SEO</span>}
                        {p.has_meta ? <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-bold text-emerald-400">META</span> : <span className="rounded bg-orange-500/20 px-1.5 py-0.5 text-[10px] font-bold text-orange-400">NO META</span>}
                      </div>
                    </div>
                  </div>

                  {/* Price Editor */}
                  {isEditing ? (
                    <div className="mt-3 space-y-2">
                      <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Приход</div>
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <div className="text-[10px] text-slate-500 mb-0.5">Наличные</div>
                          <input type="number" value={editingProduct._cash} onChange={(e) => setEditingProduct((prev) => ({ ...prev, _cash: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                        </div>
                        <div className="flex-1">
                          <div className="text-[10px] text-slate-500 mb-0.5">Безнал</div>
                          <input type="number" value={editingProduct._nonCash} onChange={(e) => setEditingProduct((prev) => ({ ...prev, _nonCash: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Продажа</div>
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <div className="text-[10px] text-slate-500 mb-0.5">Наличные</div>
                          <input type="number" value={editingProduct._price} onChange={(e) => updateEditPrice(e.target.value)} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                        </div>
                        <div className="flex-1">
                          <div className="text-[10px] text-slate-500 mb-0.5">Безнал (+28.5%)</div>
                          <input type="number" value={editingProduct._priceNonCash} onChange={(e) => setEditingProduct((prev) => ({ ...prev, _priceNonCash: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => saveProduct(editingProduct)} disabled={savingId === p.product_id} className="flex-1 rounded bg-emerald-500 px-2 py-1.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{savingId === p.product_id ? "Сохранение..." : "Сохранить"}</button>
                        <button onClick={() => setEditingProduct(null)} className="rounded bg-slate-800 px-2 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700">Отмена</button>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-3 flex items-center justify-between">
                      <div className="text-xs text-slate-400 space-y-0.5">
                        <div><span className="text-slate-500">Приход:</span> <span className="text-emerald-400 font-mono">{Number(p.cash_price || 0).toFixed(0)}₽</span> / <span className="text-sky-400 font-mono">{Number(p.non_cash_price || 0).toFixed(0)}₽</span></div>
                        <div><span className="text-slate-500">Продажа:</span> <span className="text-slate-300 font-mono">{Number(p.price || 0).toFixed(0)}₽</span> / <span className="text-slate-300 font-mono">{Number(p.price_non_cash || 0).toFixed(0)}₽</span></div>
                      </div>
                      <button onClick={() => startEdit(p)} className="rounded bg-slate-800 px-2 py-1 text-[10px] font-bold text-slate-200 hover:bg-slate-700">Edit</button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Product Detail Modal */}
      {selProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => { setSelProduct(null); setDetailEdit(false); setDetailForm(null); }}>
          <div className="max-h-[90vh] w-[95%] max-w-4xl overflow-auto rounded-2xl border border-slate-700/50 bg-slate-900 p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-5 flex items-center justify-between border-b border-slate-700 pb-4">
              <div className="flex items-center gap-4">
                <div className="h-16 w-16 flex-shrink-0 rounded-lg bg-slate-800 overflow-hidden">
                  {selProduct.image_url ? <img src={selProduct.image_url} alt={selProduct.name} className="h-full w-full object-cover" /> : <div className="flex h-full w-full items-center justify-center text-slate-600"><Image size={24} /></div>}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">{selProduct.name}</h3>
                  <p className="text-xs text-slate-500">ID: {selProduct.product_id} {selProduct.sku ? "| SKU: " + selProduct.sku : ""} | Модель: {selProduct.model || "—"}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {!detailEdit && <button onClick={() => openDetailEdit(selProduct)} className="rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-bold text-slate-950 hover:bg-emerald-400">Редактировать</button>}
                <button onClick={() => { setSelProduct(null); setDetailEdit(false); setDetailForm(null); }} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"><X size={20} /></button>
              </div>
            </div>

            {detailEdit && detailForm ? (
              <div className="space-y-4">
                {/* Image upload */}
                <div className="flex items-center gap-4">
                  <div className="h-20 w-20 flex-shrink-0 rounded-lg bg-slate-800 overflow-hidden">
                    {detailForm.image_url || detailForm.image ? (
                      <img src={detailForm.image_url || (detailForm.image ? "https://stroiapp.ru/image/" + detailForm.image : "")} alt="" className="h-full w-full object-cover" />
                    ) : <div className="flex h-full w-full items-center justify-center text-slate-600"><Image size={24} /></div>}
                  </div>
                  <div className="flex-1">
                    <div className="text-xs text-slate-500 mb-1">Фотография товара</div>
                    <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-xs font-medium text-slate-200 hover:bg-slate-700 border border-slate-700">
                      <Upload size={14} />{uploadingImg ? "Загрузка..." : "Загрузить фото"}
                      <input type="file" accept="image/*" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadImage(f); e.target.value = ""; }} />
                    </label>
                    {detailForm.image && <div className="mt-1 text-[10px] text-slate-500 truncate">{detailForm.image}</div>}
                  </div>
                </div>

                {/* Basic info */}
                <div className="grid grid-cols-3 gap-3">
                  <div><div className="text-xs text-slate-500 mb-1">Название</div><input value={detailForm.name} onChange={(e) => setDetailForm((p) => ({ ...p, name: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                  <div><div className="text-xs text-slate-500 mb-1">SKU</div><input value={detailForm.sku} onChange={(e) => setDetailForm((p) => ({ ...p, sku: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                  <div><div className="text-xs text-slate-500 mb-1">Модель</div><input value={detailForm.model} onChange={(e) => setDetailForm((p) => ({ ...p, model: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                </div>

                {/* Prices */}
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Приход</div>
                <div className="grid grid-cols-2 gap-3">
                  <div><div className="text-xs text-slate-500 mb-1">Наличные</div><input type="number" value={detailForm.cash_price} onChange={(e) => setDetailForm((p) => ({ ...p, cash_price: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                  <div><div className="text-xs text-slate-500 mb-1">Безнал</div><input type="number" value={detailForm.non_cash_price} onChange={(e) => setDetailForm((p) => ({ ...p, non_cash_price: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                </div>
                <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">Продажа</div>
                <div className="grid grid-cols-3 gap-3">
                  <div><div className="text-xs text-slate-500 mb-1">Наличные</div><input type="number" value={detailForm.price} onChange={(e) => updateDetailPrice(e.target.value)} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                  <div><div className="text-xs text-slate-500 mb-1">Безнал (+28.5%)</div><input type="number" value={detailForm.price_non_cash} onChange={(e) => setDetailForm((p) => ({ ...p, price_non_cash: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                  <div><div className="text-xs text-slate-500 mb-1">Остаток</div><input type="number" value={detailForm.quantity} onChange={(e) => setDetailForm((p) => ({ ...p, quantity: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                </div>

                {/* Description */}
                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <div className="text-xs text-slate-500">Описание товара</div>
                    <button onClick={() => generateSeo(detailForm.product_id)} disabled={generatingSeo} className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500 px-3 py-1 text-xs font-bold text-white hover:bg-indigo-400 disabled:opacity-50">
                      <Sparkles size={14} />{generatingSeo ? "Генерация..." : "Генерировать"}
                    </button>
                  </div>
                  <textarea value={detailForm.description} onChange={(e) => setDetailForm((p) => ({ ...p, description: e.target.value }))} rows={4} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500 resize-y" />
                </div>

                {/* Attributes */}
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Характеристики</div>
                  <button onClick={addAttributeRow} className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800 px-2 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 border border-slate-700">
                    <Plus size={12} />Добавить
                  </button>
                </div>
                <div className="space-y-2">
                  {productAttrs.length === 0 && <div className="text-xs text-slate-500 italic">Нет характеристик</div>}
                  {productAttrs.map((attr, idx) => (
                    <div key={idx} className="flex gap-2 items-center">
                      <select value={attr.attribute_id || ""} onChange={(e) => updateAttributeRow(idx, "attribute_id", e.target.value)} className="flex-1 rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500">
                        <option value="">Выберите...</option>
                        {allAttributes.map((a) => (
                          <option key={a.attribute_id} value={a.attribute_id}>{a.name} {a.group_name ? "(" + a.group_name + ")" : ""}</option>
                        ))}
                      </select>
                      <input value={attr.text || ""} onChange={(e) => updateAttributeRow(idx, "text", e.target.value)} placeholder="Значение" className="flex-1 rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" />
                      <button onClick={() => removeAttributeRow(idx)} className="rounded bg-red-500/20 px-2 py-1.5 text-xs text-red-400 hover:bg-red-500/30"><X size={14} /></button>
                    </div>
                  ))}
                  <button onClick={() => saveAttributes(detailForm.product_id)} disabled={savingAttrs} className="w-full rounded bg-sky-500 px-3 py-1.5 text-xs font-bold text-white hover:bg-sky-400 disabled:opacity-50">{savingAttrs ? "Сохранение..." : "Сохранить характеристики"}</button>
                </div>

                {/* SEO */}
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">SEO</div>
                  <button onClick={() => generateSeo(detailForm.product_id)} disabled={generatingSeo} className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500 px-3 py-1.5 text-xs font-bold text-white hover:bg-indigo-400 disabled:opacity-50">
                    <Sparkles size={14} />{generatingSeo ? "Генерация..." : "Автодополнение"}
                  </button>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  <div><div className="text-xs text-slate-500 mb-1">Meta Title</div><input value={detailForm.meta_title} onChange={(e) => setDetailForm((p) => ({ ...p, meta_title: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                  <div><div className="text-xs text-slate-500 mb-1">Meta Description</div><textarea value={detailForm.meta_description} onChange={(e) => setDetailForm((p) => ({ ...p, meta_description: e.target.value }))} rows={2} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500 resize-y" /></div>
                  <div><div className="text-xs text-slate-500 mb-1">Keywords</div><input value={detailForm.meta_keyword} onChange={(e) => setDetailForm((p) => ({ ...p, meta_keyword: e.target.value }))} className="w-full rounded bg-slate-800 border border-slate-700 px-2 py-1.5 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button onClick={saveDetail} disabled={savingId === detailForm.product_id} className="flex-1 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50">{savingId === detailForm.product_id ? "Сохранение..." : "Сохранить"}</button>
                  <button onClick={() => { setDetailEdit(false); setDetailForm(null); }} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700">Отмена</button>
                </div>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Цены</h4>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500">Приход наличные</div><div className="text-lg font-bold text-emerald-400">{selProduct.cash_price ? Number(selProduct.cash_price).toFixed(2) + " ₽" : "—"}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500">Приход безналичные</div><div className="text-lg font-bold text-sky-400">{selProduct.non_cash_price ? Number(selProduct.non_cash_price).toFixed(2) + " ₽" : "—"}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500">Продажа наличные</div><div className="text-lg font-bold text-white">{selProduct.price ? Number(selProduct.price).toFixed(2) + " ₽" : "—"}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500">Продажа безналичные</div><div className="text-lg font-bold text-white">{selProduct.price_non_cash ? Number(selProduct.price_non_cash).toFixed(2) + " ₽" : "—"}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500">Остаток</div><div className="text-lg font-bold text-white">{selProduct.quantity ?? "—"}</div></div>
                </div>
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500">Характеристики</h4>
                  {productAttrs.length === 0 ? (
                    <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30 text-sm text-orange-400">— не заполнено —</div>
                  ) : (
                    <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30 space-y-1">
                      {productAttrs.map((attr, idx) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span className="text-slate-500">{attr.name || "—"}</span>
                          <span className="text-slate-200 font-mono">{attr.text || "—"}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 pt-2">SEO & Описание</h4>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500 mb-1">Meta Title</div><div className="text-sm text-slate-200">{selProduct.meta_title || <span className="text-orange-400">— не заполнено —</span>}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500 mb-1">Meta Description</div><div className="text-sm text-slate-200">{selProduct.meta_description || <span className="text-orange-400">— не заполнено —</span>}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500 mb-1">Keywords</div><div className="text-sm text-slate-200">{selProduct.meta_keyword || <span className="text-orange-400">— не заполнено —</span>}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500 mb-1">Описание товара</div><div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap max-h-48 overflow-auto">{selProduct.description || <span className="text-orange-400">— не заполнено —</span>}</div></div>
                  <div className="rounded-lg bg-slate-800/50 p-3 border border-slate-700/30"><div className="text-xs text-slate-500 mb-1">Геотаргетинг</div><div className="text-sm text-emerald-400">Москва, Московская область</div></div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Product Modal */}
      {showAddForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => setShowAddForm(false)}>
          <div className="w-[95%] max-w-lg rounded-2xl border border-slate-700/50 bg-slate-900 p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between border-b border-slate-700 pb-3">
              <h3 className="text-lg font-bold text-white">Добавить товар</h3>
              <button onClick={() => setShowAddForm(false)} className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"><X size={20} /></button>
            </div>
            <div className="space-y-3">
              <div><div className="text-xs text-slate-500 mb-1">Название *</div><input value={addForm.name} onChange={(e) => setAddForm((p) => ({ ...p, name: e.target.value }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
              <div className="grid grid-cols-2 gap-3">
                <div><div className="text-xs text-slate-500 mb-1">SKU</div><input value={addForm.sku} onChange={(e) => setAddForm((p) => ({ ...p, sku: e.target.value }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                <div><div className="text-xs text-slate-500 mb-1">Модель</div><input value={addForm.model} onChange={(e) => setAddForm((p) => ({ ...p, model: e.target.value }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
              </div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Приход</div>
              <div className="grid grid-cols-2 gap-3">
                <div><div className="text-xs text-slate-500 mb-1">Наличные</div><input type="number" value={addForm.cash_price} onChange={(e) => setAddForm((p) => ({ ...p, cash_price: e.target.value }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                <div><div className="text-xs text-slate-500 mb-1">Безнал</div><input type="number" value={addForm.non_cash_price} onChange={(e) => setAddForm((p) => ({ ...p, non_cash_price: e.target.value }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
              </div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">Продажа</div>
              <div className="grid grid-cols-3 gap-3">
                <div><div className="text-xs text-slate-500 mb-1">Наличные</div><input type="number" value={addForm.price} onChange={(e) => setAddForm((p) => ({ ...p, price: e.target.value, price_non_cash: String(+(parseFloat(e.target.value || 0) * MARKUP).toFixed(2)) }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                <div><div className="text-xs text-slate-500 mb-1">Безнал (+28.5%)</div><input type="number" value={addForm.price_non_cash} onChange={(e) => setAddForm((p) => ({ ...p, price_non_cash: e.target.value }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
                <div><div className="text-xs text-slate-500 mb-1">Остаток</div><input type="number" value={addForm.quantity} onChange={(e) => setAddForm((p) => ({ ...p, quantity: e.target.value }))} className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 outline-none focus:border-emerald-500" /></div>
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={addProduct} className="flex-1 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400">Добавить</button>
                <button onClick={() => setShowAddForm(false)} className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700">Отмена</button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

function LoginScreen({ onSuccess }) {
  const [login, setLogin] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  async function submit(e) {
    e.preventDefault();
    if (busy) return;
    setError("");
    setBusy(true);
    try {
      await apiLogin(login.trim(), password);
      onSuccess();
    } catch (err) {
      setError(err.message || "Ошибка входа");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-slate-950 px-4 text-slate-100 bg-grid" style={{ height: "100dvh" }}>
      <div className="w-full max-w-sm rounded-3xl border border-slate-700/40 glass p-6 shadow-2xl shadow-emerald-500/5 md:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-400">
            <ShieldCheck size={30} />
          </div>
          <h1 className="text-xl font-bold">AI StroiApp Manager</h1>
          <p className="mt-1 text-sm text-slate-400">Войдите для продолжения</p>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-400">Логин</label>
            <input
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              autoFocus
              autoComplete="username"
              className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              placeholder="admin"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-400">Пароль</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="w-full rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              placeholder="••••••"
            />
          </div>
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-400">
              <AlertCircle size={16} className="shrink-0" /> {error}
            </div>
          )}
          <button
            type="submit"
            disabled={busy || !login.trim() || !password}
            className="w-full rounded-xl bg-emerald-500 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "Вход..." : "Войти"}
          </button>
        </form>
        <div className="mt-4 text-center text-[10px] text-slate-600">v17.09-5</div>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
