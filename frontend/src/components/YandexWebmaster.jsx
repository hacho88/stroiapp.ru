import { useEffect, useState } from "react";
import {
  Globe,
  RefreshCw,
  FileText,
  Search,
  AlertCircle,
  CheckCircle2,
  Clock,
  ExternalLink,
  Users,
  Eye,
  MousePointerClick,
  TrendingUp,
} from "lucide-react";
import { apiGet, apiPost } from "../lib/api";

export default function YandexWebmaster() {
  const [status, setStatus] = useState(null);
  const [summary, setSummary] = useState(null);
  const [sitemaps, setSitemaps] = useState([]);
  const [queries, setQueries] = useState([]);
  const [counters, setCounters] = useState(null);
  const [metrika, setMetrika] = useState(null);
  const [metrikaPeriod, setMetrikaPeriod] = useState("month");
  const [loading, setLoading] = useState(false);
  const [recrawlUrls, setRecrawlUrls] = useState("");
  const [recrawlResult, setRecrawlResult] = useState(null);
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true);
    setMessage("");
    try {
      const st = await apiGet("/webmaster/status");
      setStatus(st);
      if (st.token_configured) {
        try {
          const sum = await apiGet("/webmaster/host/summary");
          setSummary(sum);
        } catch {
          setSummary(null);
        }
        try {
          const sm = await apiGet("/webmaster/sitemaps");
          setSitemaps(sm.sitemaps || []);
        } catch {
          setSitemaps([]);
        }
        try {
          const q = await apiGet("/webmaster/search-queries");
          setQueries(q.queries || []);
        } catch {
          setQueries([]);
        }
        try {
          const c = await apiGet("/webmaster/counters");
          setCounters(c);
        } catch {
          setCounters(null);
        }
        try {
          const m = await apiGet(`/metrika/traffic?period=${metrikaPeriod}`);
          setMetrika(m);
        } catch {
          setMetrika(null);
        }
      }
    } catch (e) {
      setMessage(`Ошибка: ${e.message}`);
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (status?.token_configured) {
      apiGet(`/metrika/traffic?period=${metrikaPeriod}`)
        .then(setMetrika)
        .catch(() => setMetrika(null));
    }
  }, [metrikaPeriod]);

  const addSitemap = async () => {
    setLoading(true);
    try {
      const r = await apiPost("/webmaster/sitemaps/add", { url: "https://stroiapp.ru/sitemap.xml" });
      setMessage(r.status === "already_added" ? "Sitemap уже добавлен" : "Sitemap добавлен");
      await load();
    } catch (e) {
      setMessage(`Ошибка: ${e.message}`);
    }
    setLoading(false);
  };

  const requestRecrawl = async () => {
    const urls = recrawlUrls
      .split("\n")
      .map((u) => u.trim())
      .filter(Boolean);
    if (!urls.length) {
      setMessage("Введите URL для переобхода");
      return;
    }
    setLoading(true);
    try {
      const r = await apiPost("/webmaster/recrawl", { urls });
      setRecrawlResult(r.results);
      setMessage(`Запрос переобхода: ${r.count} URL`);
    } catch (e) {
      setMessage(`Ошибка: ${e.message}`);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Globe className="text-amber-400" size={28} />
          <div>
            <h2 className="text-xl font-bold">Яндекс.Вебмастер</h2>
            <p className="text-sm text-slate-400">Мониторинг индексации stroiapp.ru</p>
          </div>
        </div>
        <div className="flex gap-2">
          <a
            href="https://webmaster.yandex.ru/site/https:stroiapp.ru:443/"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700"
          >
            <ExternalLink size={16} /> Открыть Вебмастер
          </a>
          <button
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-3 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} /> Обновить
          </button>
        </div>
      </div>

      {message && (
        <div className="rounded-xl border border-slate-700 bg-slate-900 p-4 text-sm">{message}</div>
      )}

      {/* Status */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-700/30 glass p-5">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            {status?.token_configured ? (
              <CheckCircle2 className="text-emerald-400" size={18} />
            ) : (
              <AlertCircle className="text-red-400" size={18} />
            )}
            API токен
          </div>
          <p className="mt-2 text-lg font-bold">
            {status?.token_configured ? "Настроен" : "Не настроен"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-700/30 glass p-5">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Globe size={18} /> Страниц в поиске
          </div>
          <p className="mt-2 text-lg font-bold">
            {summary?.searchable_pages_count ?? "—"}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-700/30 glass p-5">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Clock size={18} /> Sitemap файлов
          </div>
          <p className="mt-2 text-lg font-bold">{sitemaps.length || "—"}</p>
        </div>
      </div>

      {/* Counters */}
      {counters && (
        <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
          <CounterCard
            icon={Search}
            label="В поиске"
            value={counters.searchable_pages}
            color="text-emerald-400"
          />
          <CounterCard
            icon={Globe}
            label="Обойдено"
            value={counters.downloaded_pages}
            color="text-sky-400"
          />
          <CounterCard
            icon={FileText}
            label="Исключено"
            value={counters.excluded_pages}
            color="text-amber-400"
          />
          <CounterCard
            icon={FileText}
            label="Sitemap"
            value={counters.sitemaps_count}
            color="text-slate-300"
          />
          <CounterCard
            icon={CheckCircle2}
            label="URL в sitemap"
            value={counters.sitemaps_urls}
            color="text-emerald-400"
          />
          <CounterCard
            icon={AlertCircle}
            label="Ошибок sitemap"
            value={counters.sitemap_errors}
            color={counters.sitemap_errors > 0 ? "text-red-400" : "text-emerald-400"}
          />
        </div>
      )}
      {counters && !counters.available && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
          Хост ещё загружается в Вебмастер — счётчики появятся через несколько часов после верификации.
        </div>
      )}

      {!status?.token_configured && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
          Токен YANDEX_WEBMASTER_TOKEN не настроен. Добавьте его в backend/.env
        </div>
      )}

      {/* Metrika */}
      <div className="rounded-2xl border border-slate-700/30 glass p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-lg font-bold">
            <TrendingUp size={20} className="text-red-400" /> Метрика — трафик
            <span className="ml-2 rounded-full bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
              счётчик № 112359058
            </span>
          </h3>
          <div className="flex gap-1 rounded-lg bg-slate-900 p-1">
            {[
              { id: "day", label: "День" },
              { id: "week", label: "Неделя" },
              { id: "month", label: "Месяц" },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setMetrikaPeriod(p.id)}
                className={`rounded-md px-3 py-1 text-sm font-medium ${
                  metrikaPeriod === p.id
                    ? "bg-emerald-500 text-slate-950"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {metrika?.status === "access_denied" ? (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm">
            <p className="font-bold text-amber-400">Нет доступа к API Метрики</p>
            <p className="mt-1 text-slate-300">
              Добавьте право <code className="rounded bg-slate-800 px-1">metrika:read</code> в OAuth-приложение
              (oauth.yandex.ru → приложение StroiApp Webmaster → Доступ к данным), затем получите новый токен.
            </p>
          </div>
        ) : metrika?.status === "ok" ? (
          <div className="grid gap-4 md:grid-cols-4">
            <CounterCard icon={MousePointerClick} label="Визиты" value={metrika.visits} color="text-emerald-400" />
            <CounterCard icon={Users} label="Посетители" value={metrika.users} color="text-sky-400" />
            <CounterCard icon={Eye} label="Просмотры" value={metrika.pageviews} color="text-amber-400" />
            <CounterCard
              icon={TrendingUp}
              label="Отказы"
              value={metrika.bounce_rate !== undefined ? `${Number(metrika.bounce_rate).toFixed(1)}%` : null}
              color="text-slate-300"
            />
          </div>
        ) : (
          <p className="text-sm text-slate-400">
            {metrika?.detail || "Данные Метрики загружаются..."}
          </p>
        )}
      </div>

      {/* Sitemaps */}
      <div className="rounded-2xl border border-slate-700/30 glass p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-lg font-bold">
            <FileText size={20} /> Sitemap файлы
          </h3>
          <button
            onClick={addSitemap}
            disabled={loading}
            className="rounded-lg bg-emerald-500 px-3 py-1.5 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
          >
            Добавить sitemap
          </button>
        </div>
        {sitemaps.length === 0 ? (
          <p className="text-sm text-slate-400">
            Sitemap ещё не загружены Яндексом. Хост обрабатывается после верификации (может занять несколько часов).
          </p>
        ) : (
          <div className="space-y-2">
            {sitemaps.map((sm, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-slate-900 p-3 text-sm">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{sm.sitemap_url}</p>
                  <p className="text-xs text-slate-400">
                    Тип: {sm.sitemap_type} | Источник: {sm.source}
                  </p>
                </div>
                <div className="ml-4 flex items-center gap-4 text-right">
                  <div>
                    <p className="text-slate-400 text-xs">URL</p>
                    <p className="font-bold">{sm.urls_count ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-slate-400 text-xs">Ошибок</p>
                    <p className={`font-bold ${sm.errors_count > 0 ? "text-red-400" : "text-emerald-400"}`}>
                      {sm.errors_count ?? 0}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-bold ${
                      sm.sitemap_status === "IN_PROGRESS"
                        ? "bg-amber-500/20 text-amber-400"
                        : sm.sitemap_status === "OK"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-slate-700 text-slate-300"
                    }`}
                  >
                    {sm.sitemap_status || "—"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recrawl */}
      <div className="rounded-2xl border border-slate-700/30 glass p-6">
        <h3 className="mb-2 flex items-center gap-2 text-lg font-bold">
          <RefreshCw size={20} /> Запрос переобхода
        </h3>
        <p className="mb-3 text-sm text-slate-400">
          До 100 URL за раз. Используйте для ускорения индексации важных гео-страниц.
        </p>
        <textarea
          value={recrawlUrls}
          onChange={(e) => setRecrawlUrls(e.target.value)}
          placeholder={"https://stroiapp.ru/shtukaturka-gipsovaya-vidart-standart-seryy-30-kg-dmitrov\nhttps://stroiapp.ru/rotband-moscow"}
          rows={4}
          className="w-full rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm font-mono focus:border-emerald-500 focus:outline-none"
        />
        <button
          onClick={requestRecrawl}
          disabled={loading}
          className="mt-3 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
        >
          Запросить переобход
        </button>
        {recrawlResult && (
          <div className="mt-3 space-y-1">
            {recrawlResult.map((r, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                {r.status === "queued" ? (
                  <CheckCircle2 className="text-emerald-400" size={16} />
                ) : (
                  <AlertCircle className="text-red-400" size={16} />
                )}
                <span className="truncate">{r.url}</span>
                <span className="text-slate-400">{r.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search queries */}
      <div className="rounded-2xl border border-slate-700/30 glass p-6">
        <h3 className="mb-4 flex items-center gap-2 text-lg font-bold">
          <Search size={20} /> Поисковые запросы
        </h3>
        {queries.length === 0 ? (
          <p className="text-sm text-slate-400">
            Данные появятся после начала индексации страниц.
          </p>
        ) : (
          <div className="space-y-2">
            {queries.map((q, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-slate-900 p-3 text-sm">
                <span>{q.query_text}</span>
                <div className="flex gap-4 text-slate-400">
                  <span>Показы: {q.shows?.total ?? 0}</span>
                  <span>Клики: {q.clicks?.total ?? 0}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CounterCard({ icon: Icon, label, value, color = "text-emerald-400" }) {
  return (
    <div className="rounded-2xl border border-slate-700/30 glass p-4">
      <div className={`flex items-center gap-2 text-sm ${color}`}>
        <Icon size={18} />
        <span className="text-slate-400">{label}</span>
      </div>
      <p className={`mt-2 text-2xl font-bold ${color}`}>
        {value === null || value === undefined ? "—" : Number(value).toLocaleString("ru-RU")}
      </p>
    </div>
  );
}
