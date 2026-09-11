"""Deploy custom-stroyapp.css + home.twig + header.twig"""
import requests, json

# ===== 1. custom-stroyapp.css =====
css = """/* =========================================================
   StroiApp.ru — Custom Styles for UniShop2 Theme
   ========================================================= */

.home-page {
    --sa-orange: #FF4F00; --sa-orange-dark: #E04500; --sa-dark: #1A1A2E;
    --sa-gray: #F3F4F6; --sa-border: #E5E7EB; --sa-text: #111827; --sa-text2: #6B7280;
    font-family: 'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}

/* --- AI CALCULATOR --- */
.sa-calc-card {
    background: #F3F4F6; border-radius: 16px; padding: 24px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06); height: 100%;
}
.sa-calc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.sa-calc-header h3 { font-size: 20px; font-weight: 800; margin: 0; color: var(--sa-dark); display: flex; align-items: center; gap: 8px; }
.sa-badge { background: var(--sa-orange); color: #fff; font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 14px; letter-spacing: 0.5px; }
.sa-calc-desc { font-size: 13px; color: var(--sa-text2); margin: 0 0 18px 0; font-weight: 500; }
.sa-calc-fields { display: flex; flex-direction: column; gap: 10px; }
.sa-field { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border: 1px solid var(--sa-border); border-radius: 12px; background: #FFFFFF; transition: border-color 0.2s, box-shadow 0.2s; }
.sa-field:focus-within { border-color: var(--sa-orange); box-shadow: 0 0 0 3px rgba(255,79,0,0.1); }
.sa-field-icon { width: 36px; height: 36px; background: #F3F4F6; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.sa-field-body { flex: 1; }
.sa-field-body label { display: block; font-size: 10px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; font-weight: 600; }
.sa-field-body select, .sa-field-body input { width: 100%; border: none; background: transparent; font-size: 14px; font-weight: 700; color: var(--sa-text); outline: none; padding: 0; font-family: inherit; }
.sa-field-body input { font-size: 15px; }
.sa-btn-calc { background: var(--sa-orange); color: #fff; border: none; padding: 16px; border-radius: 14px; font-size: 15px; font-weight: 800; cursor: pointer; margin-top: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; transition: background 0.2s, box-shadow 0.2s; font-family: inherit; box-shadow: 0 4px 12px rgba(255,79,0,0.3); }
.sa-btn-calc:hover { background: var(--sa-orange-dark); box-shadow: 0 6px 16px rgba(255,79,0,0.4); }
.sa-calc-footer { text-align: center; font-size: 12px; color: #10B981; margin: 14px 0 0 0; font-weight: 600; }

/* --- HERO SLIDER --- */
.sa-slider-card { position: relative; border-radius: 16px; overflow: hidden; min-height: 420px; display: flex; align-items: flex-end; box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.sa-slider-img { position: absolute; inset: 0; z-index: 1; }
.sa-slider-img img { width: 100%; height: 100%; object-fit: cover; }
.sa-slider-overlay { position: absolute; inset: 0; background: linear-gradient(to top, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.15) 55%, rgba(0,0,0,0.05) 100%); z-index: 2; }
.sa-slider-content { position: relative; z-index: 3; padding: 40px; color: #fff; width: 100%; }
.sa-slider-logo { color: #4DA6D9; font-size: 56px; font-weight: 900; font-style: italic; margin-bottom: 12px; text-shadow: 0 2px 10px rgba(0,0,0,0.4); letter-spacing: -2px; line-height: 1; }
.sa-slider-content h3 { font-size: 28px; font-weight: 800; margin: 0 0 20px 0; line-height: 1.3; text-shadow: 0 2px 6px rgba(0,0,0,0.4); }
.sa-slider-props { display: flex; gap: 24px; margin-bottom: 24px; flex-wrap: wrap; }
.sa-slider-props span { display: flex; align-items: center; gap: 10px; font-size: 13px; line-height: 1.5; text-shadow: 0 1px 3px rgba(0,0,0,0.4); font-weight: 500; }
.sa-slider-props span i { font-style: normal; width: 34px; height: 34px; background: rgba(255,255,255,0.12); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 15px; flex-shrink: 0; border: 1px solid rgba(255,255,255,0.2); }
.sa-btn-slider { display: inline-block; background: var(--sa-orange); color: #fff; padding: 14px 30px; border-radius: 10px; font-weight: 700; font-size: 14px; text-decoration: none; transition: background 0.2s; box-shadow: 0 4px 12px rgba(255,79,0,0.3); }
.sa-btn-slider:hover { background: var(--sa-orange-dark); color: #fff; text-decoration: none; }
.sa-slider-nav { position: absolute; bottom: 16px; left: 0; right: 0; z-index: 4; display: flex; justify-content: space-between; align-items: center; padding: 0 40px; }
.sa-slider-dots { display: flex; gap: 8px; }
.sa-slider-dots span { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.35); cursor: pointer; }
.sa-slider-dots span.active { background: var(--sa-orange); }
.sa-slider-arrows { display: flex; gap: 8px; }
.sa-slider-arrows button { width: 40px; height: 40px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.25); background: rgba(255,255,255,0.85); cursor: pointer; font-size: 20px; color: #333; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.sa-slider-arrows button:hover { background: #fff; }

/* --- SEARCH BAR --- */
.sa-search-wrap { margin-top: 24px; }
.sa-search-box { display: flex; align-items: center; background: #fff; border-radius: 16px; padding: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); border: 1px solid var(--sa-border); }
.sa-search-cat { display: flex; align-items: center; gap: 8px; padding: 0 18px; border-right: 1px solid var(--sa-border); color: var(--sa-text2); font-size: 14px; flex-shrink: 0; white-space: nowrap; font-weight: 500; }
.sa-search-cat select { border: none; background: transparent; font-size: 14px; color: var(--sa-text); outline: none; cursor: pointer; font-family: inherit; font-weight: 500; }
.sa-search-box input { flex: 1; border: none; padding: 14px 18px; font-size: 15px; outline: none; font-family: inherit; }
.sa-search-go { background: var(--sa-orange); color: #fff; border: none; padding: 14px 32px; border-radius: 12px; font-weight: 800; font-size: 15px; cursor: pointer; flex-shrink: 0; font-family: inherit; transition: background 0.2s; }
.sa-search-go:hover { background: var(--sa-orange-dark); }
.sa-search-tags { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
.sa-search-tags a { color: var(--sa-text2); font-size: 13px; text-decoration: none; padding: 6px 14px; background: #fff; border-radius: 20px; border: 1px solid var(--sa-border); transition: all 0.2s; font-weight: 500; }
.sa-search-tags a:hover { background: var(--sa-orange); color: #fff; border-color: var(--sa-orange); }

/* --- FEATURES BAR --- */
.sa-features-bar { background: #FFFFFF; border-top: 1px solid var(--sa-border); border-bottom: 1px solid var(--sa-border); padding: 28px 0; }
.sa-features-inner { display: flex; justify-content: space-between; align-items: center; gap: 0; }
.sa-feat { display: flex; align-items: center; gap: 12px; flex: 1; padding: 0 20px; position: relative; }
.sa-feat:not(:last-child)::after { content: ''; position: absolute; right: 0; top: 50%; transform: translateY(-50%); width: 1px; height: 36px; background: var(--sa-border); }
.sa-feat-icon { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.sa-feat-text h4 { font-size: 14px; font-weight: 800; margin: 0 0 2px 0; color: var(--sa-text); }
.sa-feat-text p { font-size: 12px; color: var(--sa-text2); margin: 0; font-weight: 500; }

/* --- CATEGORIES --- */
.sa-categories { background: var(--sa-gray); padding: 50px 0; }
.sa-cat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.sa-cat-header h2 { font-size: 24px; font-weight: 800; margin: 0; color: var(--sa-dark); }
.sa-cat-header a { color: var(--sa-orange); font-weight: 700; font-size: 14px; text-decoration: none; display: flex; align-items: center; gap: 6px; }
.sa-cat-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 20px; }
.sa-cat-card { background: #fff; border-radius: 16px; padding: 20px; text-decoration: none; color: inherit; display: flex; align-items: center; gap: 14px; transition: all 0.3s ease; border: 1px solid var(--sa-border); box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.sa-cat-card:hover { transform: translateY(-3px); box-shadow: 0 10px 28px rgba(0,0,0,0.08); border-color: var(--sa-orange); text-decoration: none; color: inherit; }
.sa-cat-img { width: 64px; height: 64px; flex-shrink: 0; }
.sa-cat-img img { width: 100%; height: 100%; object-fit: contain; }
.sa-cat-info h3 { font-size: 14px; font-weight: 800; margin: 0 0 3px 0; color: var(--sa-dark); }
.sa-cat-info span { font-size: 12px; color: var(--sa-text2); font-weight: 500; }

/* --- HEADER SEARCH OVERRIDE --- */
.header-search__form { border-radius: 8px !important; overflow: hidden; }
.header-search__btn.search-btn, .header-search__btn { background: var(--sa-orange) !important; border-color: var(--sa-orange) !important; color: #fff !important; border-radius: 0 8px 8px 0 !important; transition: background 0.2s !important; }
.header-search__btn.search-btn:hover, .header-search__btn:hover { background: var(--sa-orange-dark) !important; border-color: var(--sa-orange-dark) !important; }
.header-search__input { border-radius: 8px 0 0 8px !important; }
.header-search__category-btn { border-radius: 8px 0 0 8px !important; }

/* --- RESPONSIVE --- */
@media (max-width: 1200px) { .sa-cat-grid { grid-template-columns: repeat(3, 1fr); } .sa-slider-card { min-height: 380px; } }
@media (max-width: 992px) { .sa-cat-grid { grid-template-columns: repeat(2, 1fr); } .sa-features-inner { flex-wrap: wrap; } .sa-feat { min-width: 200px; padding: 10px; } .sa-feat:not(:last-child)::after { display: none; } .sa-slider-content h3 { font-size: 24px; } .sa-search-box { flex-wrap: wrap; } .sa-search-cat { border-right: none; border-bottom: 1px solid var(--sa-border); width: 100%; padding: 10px; } .sa-search-go { width: 100%; } }
@media (max-width: 768px) { .sa-slider-card { min-height: 320px; } .sa-slider-content { padding: 28px; } .sa-slider-logo { font-size: 40px; } .sa-calc-card { padding: 20px; } }
@media (max-width: 576px) { .sa-cat-grid { grid-template-columns: 1fr; } .sa-slider-content h3 { font-size: 20px; } .sa-slider-props { gap: 14px; } }
"""

# ===== 2. home.twig (Bootstrap grid) =====
twig = """{{ header }}

<link rel="stylesheet" href="catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css">

<div id="content" class="home-page">

<!-- HERO SECTION -->
<div class="sa-hero-wrap">
    <div class="container">
        <div class="row">
            <!-- Left: AI Calculator (col-md-3) -->
            <div class="col-md-3 col-sm-12">
                <div class="sa-calc-card">
                    <div class="sa-calc-header">
                        <h3><span>&#x2728;</span> AI Калькулятор</h3>
                        <span class="sa-badge">AI</span>
                    </div>
                    <p class="sa-calc-desc">Рассчитайте количество материалов для вашего проекта</p>
                    <div class="sa-calc-fields">
                        <div class="sa-field">
                            <div class="sa-field-icon">&#x1F527;</div>
                            <div class="sa-field-body">
                                <label>Тип работ</label>
                                <select><option>Стены</option><option>Пол</option><option>Потолок</option></select>
                            </div>
                        </div>
                        <div class="sa-field">
                            <div class="sa-field-icon">&#x1F4CB;</div>
                            <div class="sa-field-body">
                                <label>Материал</label>
                                <select><option>Гипсокартон KNAUF</option><option>Штукатурка</option><option>Шпаклёвка</option></select>
                            </div>
                        </div>
                        <div class="sa-field">
                            <div class="sa-field-icon">&#x1F4D0;</div>
                            <div class="sa-field-body">
                                <label>Площадь поверхности, м&#xB2;</label>
                                <input type="number" value="50">
                            </div>
                        </div>
                        <div class="sa-field">
                            <div class="sa-field-icon">&#x1F4CF;</div>
                            <div class="sa-field-body">
                                <label>Высота стен, м</label>
                                <input type="number" value="2.7">
                            </div>
                        </div>
                        <div class="sa-field">
                            <div class="sa-field-icon">&#x1F3E0;</div>
                            <div class="sa-field-body">
                                <label>Тип помещения</label>
                                <select><option>Жилое помещение</option><option>Ванная</option><option>Кухня</option></select>
                            </div>
                        </div>
                    </div>
                    <button type="button" class="sa-btn-calc">Рассчитать материалы <span>&#x2728;</span></button>
                    <p class="sa-calc-footer">&#x2705; Точность расчёта на основе AI</p>
                </div>
            </div>

            <!-- Right: Slider (col-md-9) -->
            <div class="col-md-9 col-sm-12">
                <div class="sa-slider-card">
                    <div class="sa-slider-img">
                        <img src="https://stroiapp.ru/image/cache/catalog/1-1-1-6_1_64c0f53d3d421_thumb_2264c0f53d3e1a7-800x400.jpg" alt="KNAUF">
                    </div>
                    <div class="sa-slider-overlay"></div>
                    <div class="sa-slider-content">
                        <div class="sa-slider-logo">KNAUF</div>
                        <h3>Немецкое качество<br>для вашего строительства</h3>
                        <div class="sa-slider-props">
                            <span><i>&#x2699;&#xFE0F;</i> Проверенные<br>технологии</span>
                            <span><i>&#x1F33F;</i> Экологичные<br>материалы</span>
                            <span><i>&#x1F6E1;&#xFE0F;</i> Надёжность<br>на годы</span>
                        </div>
                        <a href="index.php?route=product/category&amp;path=59" class="sa-btn-slider">Смотреть продукцию KNAUF</a>
                    </div>
                    <div class="sa-slider-nav">
                        <div class="sa-slider-dots"><span class="active"></span><span></span><span></span></div>
                        <div class="sa-slider-arrows"><button>&lsaquo;</button><button>&rsaquo;</button></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Search Bar -->
        <div class="sa-search-wrap">
            <div class="sa-search-box">
                <div class="sa-search-cat"><span>&#x2630;</span><select><option>Каталог товаров</option></select></div>
                <input type="text" placeholder="Поиск по товарам, брендам, категориям...">
                <button class="sa-search-go">Найти</button>
            </div>
            <div class="sa-search-tags">
                <a href="#">KNAUF</a>
                <a href="#">Гипсокартон</a>
                <a href="#">Утеплитель</a>
                <a href="#">Профиль</a>
            </div>
        </div>
    </div>
</div>

<!-- FEATURES BAR -->
<div class="sa-features-bar">
    <div class="container">
        <div class="sa-features-inner">
            <div class="sa-feat">
                <div class="sa-feat-icon" style="background:#FFF0E6;">&#x1F69A;</div>
                <div class="sa-feat-text"><h4>Быстрая доставка</h4><p>по всей России</p></div>
            </div>
            <div class="sa-feat">
                <div class="sa-feat-icon" style="background:#FFF8E6;">&#x1F3C5;</div>
                <div class="sa-feat-text"><h4>Гарантия качества</h4><p>на все товары</p></div>
            </div>
            <div class="sa-feat">
                <div class="sa-feat-icon" style="background:#E6F7FF;">&#x1F3F7;&#xFE0F;</div>
                <div class="sa-feat-text"><h4>Выгодные цены</h4><p>и акции</p></div>
            </div>
            <div class="sa-feat">
                <div class="sa-feat-icon" style="background:#E6FFF0;">&#x1F504;</div>
                <div class="sa-feat-text"><h4>Возврат товара</h4><p>в течение 14 дней</p></div>
            </div>
            <div class="sa-feat">
                <div class="sa-feat-icon" style="background:#F0E6FF;">&#x1F3A7;</div>
                <div class="sa-feat-text"><h4>Поддержка 24/7</h4><p>мы всегда на связи</p></div>
            </div>
        </div>
    </div>
</div>

<!-- POPULAR CATEGORIES -->
<div class="sa-categories">
    <div class="container">
        <div class="sa-cat-header">
            <h2>Популярные категории</h2>
            <a href="index.php?route=product/category">Смотреть все категории &#x2192;</a>
        </div>
        <div class="sa-cat-grid">
            {% for category in categories %}
            <a href="{{ category.href }}" class="sa-cat-card">
                <div class="sa-cat-info">
                    <h3>{{ category.name }}</h3>
                    <span>Более {{ category.total_items|default('100') }} товаров</span>
                </div>
                <div class="sa-cat-img">
                    <img src="{{ category.thumb|default('catalog/view/theme/unishop2/image/no_image.png') }}" alt="{{ category.name }}">
                </div>
            </a>
            {% endfor %}
        </div>
    </div>
</div>

</div>

{{ footer }}
"""

# ===== 3. header.twig patch =====
with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/template/common/header.twig', 'r', encoding='utf-8') as f:
    header = f.read()

# Add custom CSS link after styles loop if not already present
link_tag = '<link href="catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css" rel="stylesheet">'
if link_tag not in header:
    # Insert after the last style link
    header = header.replace(
        '{% for style in styles %}',
        link_tag + '\n\t{% for style in styles %}'
    )
    print('header patched')
else:
    print('header already has link')

# ===== SAVE LOCAL =====
with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css', 'w', encoding='utf-8') as f:
    f.write(css)

with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/template/common/home.twig', 'w', encoding='utf-8') as f:
    f.write(twig)

with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/template/common/header.twig', 'w', encoding='utf-8') as f:
    f.write(header)

print('Local files saved. CSS:', len(css), 'twig:', len(twig), 'header:', len(header))

# ===== UPLOAD =====
OPENCART_URL = 'https://stroiapp.ru'
TOKEN = 'change_this_ai_manager_token'

for path, content in [
    ('catalog/view/theme/unishop2/stylesheet/custom-stroyapp.css', css),
    ('catalog/view/theme/unishop2/template/common/home.twig', twig),
    ('catalog/view/theme/unishop2/template/common/header.twig', header),
]:
    url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=file/writeSafe&token={TOKEN}'
    r = requests.post(url, json={'path': path, 'content': content}, timeout=30)
    raw = r.content
    if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
    data = json.loads(raw.decode('utf-8'))
    print(path.split('/')[-1], ':', data.get('status'))

cache_url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=site/clearCache&token={TOKEN}'
r2 = requests.post(cache_url, timeout=30)
raw2 = r2.content
if raw2.startswith(b'\xef\xbb\xbf'): raw2 = raw2[3:]
data2 = json.loads(raw2.decode('utf-8'))
print('cache:', data2.get('deleted', 0))
