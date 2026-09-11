const { useState, useEffect } = React;

const API_URL = 'https://stroiapp.ru/index.php?route=api/ai_manager';
const TOKEN = 'change_this_ai_manager_token';

function apiPost(action, body) {
    return fetch(`${API_URL}&action=${action}&token=${TOKEN}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    }).then(r => r.json());
}

const TEMPLATES = {
    hero: (opts) => `<div class="sa-hero-wrap">\n    <div class="container">\n        <div class="row">\n            <div class="col-lg-4 col-md-5 col-sm-12">\n                <div class="sa-calc-card">AI Calculator</div>\n            </div>\n            <div class="col-lg-8 col-md-7 col-sm-12">\n                <div class="sa-slider-card">Slider: ${opts.brand || 'Brand'}</div>\n            </div>\n        </div>\n    </div>\n</div>`,
    features: () => `<div class="sa-features-bar">Features: Delivery, Warranty, Prices, Return, Support</div>`,
    categories: () => `<div class="sa-categories">Categories Grid (Twig loop)</div>`,
    products: () => `<div class="sa-section">Bestseller Products (Twig loop)</div>`,
    promotions: () => `<div class="sa-section">Promotions & Specials (Twig loop)</div>`,
    blog: () => `<div class="sa-section">Blog Posts (Twig loop)</div>`,
    manufacturers: () => `<div class="sa-section">Manufacturers Logos (Twig loop)</div>`
};

function generateDesign(prompt) {
    const p = prompt.toLowerCase();
    const opts = { brand: 'KNAUF', accent: '#FF4F00' };
    if (p.includes('кнауф') || p.includes('knauf')) opts.brand = 'KNAUF';
    if (p.includes('гипрок') || p.includes('gyproc')) opts.brand = 'Гипрок';
    if (p.includes('цемент')) opts.brand = 'ЦЕМЕНТ';
    if (p.includes('синий') || p.includes('blue')) opts.accent = '#4DA6D9';
    if (p.includes('зелен') || p.includes('green')) opts.accent = '#10B981';
    if (p.includes('красн') || p.includes('red')) opts.accent = '#EF4444';

    const sections = [];
    const keywords = {
        hero: ['калькулятор', 'hero', 'слайдер', 'баннер', 'главный экран'],
        features: ['преимуществ', 'доставк', 'гаранти', 'features', 'плюсы'],
        categories: ['категор', 'categories', 'рубрик'],
        products: ['хит', 'bestseller', 'популярные товары', 'товары'],
        promotions: ['акци', 'скидк', 'promotions', 'special', 'распродаж'],
        blog: ['блог', 'стат', 'blog', 'новост'],
        manufacturers: ['производител', 'бренд', 'manufacturer', 'партнер']
    };
    Object.keys(keywords).forEach(key => {
        if (keywords[key].some(k => p.includes(k))) sections.push(key);
    });
    if (sections.length === 0) sections.push('hero', 'features', 'categories');

    let twig = '{{ header }}\\n<link rel="stylesheet" href="catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css">\\n<div id="content" class="home-page">\\n';
    sections.forEach(s => { if (TEMPLATES[s]) twig += TEMPLATES[s](opts) + '\\n'; });
    twig += '</div>
{{ footer }}';

    let css = `.home-page { --sa-orange: ${opts.accent}; --sa-dark: #1A1A2E; --sa-gray: #F3F4F6; }
.sa-hero-wrap { background: var(--sa-gray); padding: 30px 0; }
.sa-calc-card { background: #F3F4F6; border-radius: 16px; padding: 24px; }
.sa-slider-card { border-radius: 16px; overflow: hidden; min-height: 400px; }
.sa-features-bar { background: #fff; padding: 28px 0; border-top: 1px solid #e5e5e5; border-bottom: 1px solid #e5e5e5; }
.sa-categories { background: var(--sa-gray); padding: 50px 0; }
.sa-section { padding: 50px 0; }
.sa-hero-wrap, .sa-features-bar, .sa-categories, .sa-section { width: 100vw; margin-left: calc(-50vw + 50%); margin-right: calc(-50vw + 50%); }`;

    return { twig, css, sections, opts };
}

function Designer() {
    const [prompt, setPrompt] = useState('');
    const [generated, setGenerated] = useState(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [activeSections, setActiveSections] = useState([]);
    const [previewHtml, setPreviewHtml] = useState('');

    const availableSections = [
        { key: 'hero', label: 'Hero + AI Калькулятор', icon: '&#x1F3A8;' },
        { key: 'features', label: 'Преимущества', icon: '&#x1F3C5;' },
        { key: 'categories', label: 'Категории', icon: '&#x1F4C1;' },
        { key: 'products', label: 'Хиты продаж', icon: '&#x1F4E6;' },
        { key: 'promotions', label: 'Акции', icon: '&#x1F4B5;' },
        { key: 'blog', label: 'Блог', icon: '&#x1F4D6;' },
        { key: 'manufacturers', label: 'Бренды', icon: '&#x1F3E2;' }
    ];

    const toggleSection = (key) => {
        setActiveSections(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
    };

    const generate = () => {
        setLoading(true);
        const design = generateDesign(prompt || 'hero calculator orange theme knauf');
        const sections = activeSections.length > 0 ? activeSections : design.sections;
        let twig = '{{ header }}\n<link rel="stylesheet" href="catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css">\n<div id="content" class="home-page">\n';
        sections.forEach(s => { if (TEMPLATES[s]) twig += TEMPLATES[s](design.opts) + '\n'; });
        twig += '</div>\n{{ footer }}';
        setGenerated({ ...design, twig, sections });
        setPreviewHtml(`<style>${design.css}</style><div class="home-page">${sections.map(s => TEMPLATES[s](design.opts)).join('')}</div>`);
        setLoading(false);
    };

    const exportToTheme = async () => {
        if (!generated) return;
        setLoading(true);
        try {
            await apiPost('theme/write', { path: 'template/common/home.twig', content: generated.twig });
            await apiPost('theme/write', { path: 'stylesheet/custom-stroyapp.css', content: generated.css });
            await apiPost('site/clearCache', {});
            setMessage('Экспортировано на сайт! Обновите stroiapp.ru');
        } catch (e) {
            setMessage('Ошибка: ' + e.message);
        }
        setLoading(false);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            <div style={{ padding: '20px 30px', background: '#fff', borderBottom: '1px solid #eee' }}>
                <h2 style={{ marginBottom: '16px', fontSize: '20px' }}>&#x1F3A8; AI Конструктор интерфейса</h2>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
                    <input
                        type="text"
                        placeholder="Опишите дизайн: 'сделай оранжевый hero с калькулятором, KNAUF слайдер, категории и акции'..."
                        value={prompt}
                        onChange={e => setPrompt(e.target.value)}
                        style={{ flex: 1, padding: '12px 16px', borderRadius: '10px', border: '1px solid #ddd', fontSize: '14px', fontFamily: 'inherit' }}
                    />
                    <button className="btn btn-primary" onClick={generate} disabled={loading} style={{ padding: '12px 24px' }}>
                        {loading ? 'Генерация...' : '&#x2728; Сгенерировать'}
                    </button>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {availableSections.map(s => (
                        <button
                            key={s.key}
                            onClick={() => toggleSection(s.key)}
                            style={{
                                padding: '8px 14px', borderRadius: '8px', border: '1px solid #ddd',
                                background: activeSections.includes(s.key) ? '#FF4F00' : '#fff',
                                color: activeSections.includes(s.key) ? '#fff' : '#333',
                                cursor: 'pointer', fontSize: '13px', fontWeight: 600,
                                display: 'flex', alignItems: 'center', gap: '6px'
                            }}
                        >
                            <span dangerouslySetInnerHTML={{ __html: s.icon }} /> {s.label}
                        </button>
                    ))}
                </div>
            </div>

            {message && <div className="error-box" style={{ margin: '10px 30px' }}>{message}</div>}

            <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid #eee' }}>
                    <div style={{ padding: '10px 20px', background: '#f8f8f8', borderBottom: '1px solid #eee', fontSize: '12px', fontWeight: 700, color: '#666' }}>
                        &#x1F4DD; Сгенерированный Twig
                    </div>
                    <textarea
                        style={{ flex: 1, padding: '16px', fontFamily: 'monospace', fontSize: '12px', lineHeight: 1.5, border: 'none', resize: 'none', background: '#fafafa' }}
                        value={generated ? generated.twig : 'Введите промпт и нажмите "Сгенерировать"...'}
                        onChange={e => generated && setGenerated({ ...generated, twig: e.target.value })}
                        readOnly={!generated}
                    />
                </div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderRight: '1px solid #eee' }}>
                    <div style={{ padding: '10px 20px', background: '#f8f8f8', borderBottom: '1px solid #eee', fontSize: '12px', fontWeight: 700, color: '#666' }}>
                        &#x1F3A8; Сгенерированный CSS
                    </div>
                    <textarea
                        style={{ flex: 1, padding: '16px', fontFamily: 'monospace', fontSize: '12px', lineHeight: 1.5, border: 'none', resize: 'none', background: '#fafafa' }}
                        value={generated ? generated.css : 'CSS появится здесь...'}
                        onChange={e => generated && setGenerated({ ...generated, css: e.target.value })}
                        readOnly={!generated}
                    />
                </div>
                <div style={{ width: '40%', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ padding: '10px 20px', background: '#f8f8f8', borderBottom: '1px solid #eee', fontSize: '12px', fontWeight: 700, color: '#666', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>&#x1F441; Превью</span>
                        {generated && (
                            <button className="btn btn-primary" style={{ padding: '6px 14px', fontSize: '12px' }} onClick={exportToTheme} disabled={loading}>
                                {loading ? '...' : '&#x1F680; Экспорт на сайт'}
                            </button>
                        )}
                    </div>
                    <div style={{ flex: 1, padding: '20px', overflow: 'auto', background: '#f5f5f7' }}>
                        {generated ? (
                            <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
                        ) : (
                            <div style={{ textAlign: 'center', color: '#999', paddingTop: '60px' }}>
                                <div style={{ fontSize: '48px', marginBottom: '16px' }}>&#x1F3A8;</div>
                                <p>Превью дизайна появится здесь</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
