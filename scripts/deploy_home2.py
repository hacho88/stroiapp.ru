"""Deploy home.twig with exact Manus AI design"""
import requests, json

css = """/* AI HOME - Manus AI Exact */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.home-page {
    --orange: #FF6B00; --orange-h: #E55A00; --dark: #1A1A2E;
    --gray: #F5F5F5; --border: #E5E5E5; --text: #333; --text2: #666;
    font-family: 'Inter', sans-serif;
}

.ai-hero-wrap, .ai-features-wrap, .ai-cat-wrap {
    position: relative;
    width: 100vw;
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
}

.ai-hero-wrap { background: var(--gray); padding: 30px 0 20px; }

.ai-hero-inner, .ai-search-wrap, .ai-features-inner, .ai-cat-inner {
    max-width: 1320px;
    margin: 0 auto;
    padding: 0 24px;
}

.ai-hero-inner {
    display: grid;
    grid-template-columns: 380px 1fr;
    gap: 30px;
}

.ai-calc-card {
    background: #fff;
    border-radius: 24px;
    padding: 28px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    height: 100%;
    box-sizing: border-box;
}

.ai-calc-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.ai-calc-top h2 {
    font-size: 22px;
    font-weight: 800;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--dark);
    font-family: 'Inter', sans-serif;
}

.ai-sparkle { font-size: 24px; }

.ai-badge {
    background: var(--orange);
    color: #fff;
    font-size: 11px;
    font-weight: 800;
    padding: 4px 12px;
    border-radius: 14px;
    letter-spacing: 0.5px;
}

.ai-calc-desc {
    font-size: 13px;
    color: var(--text2);
    margin: 0 0 20px 0;
    font-family: 'Inter', sans-serif;
}

.ai-calc-fields { display: flex; flex-direction: column; gap: 10px; }

.ai-field {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 16px;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: #FAFAFA;
}

.ai-field-icon {
    width: 40px;
    height: 40px;
    background: #fff;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

.ai-field-body { flex: 1; }

.ai-field-body label {
    display: block;
    font-size: 10px;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 3px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
}

.ai-field-body select,
.ai-field-body input {
    width: 100%;
    border: none;
    background: transparent;
    font-size: 14px;
    font-weight: 700;
    color: var(--text);
    outline: none;
    padding: 0;
    font-family: 'Inter', sans-serif;
}

.ai-field-body input { font-size: 16px; }

.ai-btn-calc {
    background: var(--orange);
    color: #fff;
    border: none;
    padding: 18px;
    border-radius: 14px;
    font-size: 16px;
    font-weight: 800;
    cursor: pointer;
    margin-top: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    width: 100%;
    transition: background 0.2s;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 4px 12px rgba(255,107,0,0.3);
}

.ai-btn-calc:hover { background: var(--orange-h); }

.ai-calc-note {
    text-align: center;
    font-size: 12px;
    color: #28A745;
    margin: 14px 0 0 0;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

.ai-slider-wrap { position: relative; }

.ai-slider-card {
    position: relative;
    border-radius: 24px;
    overflow: hidden;
    min-height: 460px;
    display: flex;
    align-items: flex-end;
}

.ai-slider-img {
    position: absolute;
    inset: 0;
    z-index: 1;
}

.ai-slider-img img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.ai-slider-overlay {
    position: absolute;
    inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.05) 100%);
    z-index: 2;
}

.ai-slider-content {
    position: relative;
    z-index: 3;
    padding: 50px;
    color: #fff;
    width: 100%;
}

.ai-slider-logo {
    color: #4DA6D9;
    font-size: 64px;
    font-weight: 900;
    font-style: italic;
    margin-bottom: 14px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.4);
    font-family: 'Inter', sans-serif;
    letter-spacing: -2px;
}

.ai-slider-content h3 {
    font-size: 32px;
    font-weight: 800;
    margin: 0 0 24px 0;
    line-height: 1.25;
    text-shadow: 0 2px 6px rgba(0,0,0,0.4);
    font-family: 'Inter', sans-serif;
}

.ai-slider-props {
    display: flex;
    gap: 28px;
    margin-bottom: 28px;
    flex-wrap: wrap;
}

.ai-slider-props span {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    line-height: 1.5;
    text-shadow: 0 1px 3px rgba(0,0,0,0.4);
    font-family: 'Inter', sans-serif;
}

.ai-slider-props span i {
    font-style: normal;
    width: 36px;
    height: 36px;
    background: rgba(255,255,255,0.12);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
    border: 1px solid rgba(255,255,255,0.2);
}

.ai-btn-slider {
    display: inline-block;
    background: var(--orange);
    color: #fff;
    padding: 16px 36px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 15px;
    text-decoration: none;
    transition: background 0.2s;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 4px 12px rgba(255,107,0,0.3);
}

.ai-btn-slider:hover { background: var(--orange-h); }

.ai-slider-dots {
    position: absolute;
    bottom: 24px;
    left: 50px;
    z-index: 4;
    display: flex;
    gap: 10px;
}

.ai-slider-dots span {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: rgba(255,255,255,0.3);
    cursor: pointer;
}

.ai-slider-dots span.active { background: var(--orange); }

.ai-slider-arrows {
    position: absolute;
    bottom: 16px;
    right: 24px;
    z-index: 4;
    display: flex;
    gap: 10px;
}

.ai-slider-arrows button {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,0.25);
    background: rgba(255,255,255,0.85);
    cursor: pointer;
    font-size: 22px;
    color: #333;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.ai-slider-arrows button:hover { background: #fff; }

.ai-search-wrap { margin-top: 30px; }

.ai-search-box {
    display: flex;
    align-items: center;
    background: #fff;
    border-radius: 16px;
    padding: 8px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    border: 1px solid var(--border);
}

.ai-search-cat {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 20px;
    border-right: 1px solid var(--border);
    color: var(--text2);
    font-size: 14px;
    flex-shrink: 0;
    white-space: nowrap;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

.ai-search-cat select {
    border: none;
    background: transparent;
    font-size: 14px;
    color: var(--text);
    outline: none;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

.ai-search-box input {
    flex: 1;
    border: none;
    padding: 16px 20px;
    font-size: 15px;
    outline: none;
    min-width: 250px;
    font-family: 'Inter', sans-serif;
}

.ai-search-go {
    background: var(--orange);
    color: #fff;
    border: none;
    padding: 16px 40px;
    border-radius: 12px;
    font-weight: 800;
    font-size: 15px;
    cursor: pointer;
    flex-shrink: 0;
    font-family: 'Inter', sans-serif;
    transition: background 0.2s;
}

.ai-search-go:hover { background: var(--orange-h); }

.ai-search-tags {
    display: flex;
    gap: 12px;
    margin-top: 14px;
    flex-wrap: wrap;
}

.ai-search-tags a {
    color: var(--text2);
    font-size: 13px;
    text-decoration: none;
    padding: 8px 16px;
    background: #fff;
    border-radius: 20px;
    border: 1px solid var(--border);
    transition: all 0.2s;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

.ai-search-tags a:hover {
    background: var(--orange);
    color: #fff;
    border-color: var(--orange);
}

.ai-features-wrap {
    background: #fff;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 32px 0;
}

.ai-features-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0;
}

.ai-feat {
    display: flex;
    align-items: center;
    gap: 14px;
    flex: 1;
    padding: 0 20px;
    position: relative;
}

.ai-feat:not(:last-child)::after {
    content: '';
    position: absolute;
    right: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 1px;
    height: 40px;
    background: var(--border);
}

.ai-feat-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    flex-shrink: 0;
}

.ai-feat-text h4 {
    font-size: 14px;
    font-weight: 800;
    margin: 0 0 3px 0;
    color: var(--text);
    font-family: 'Inter', sans-serif;
}

.ai-feat-text p {
    font-size: 12px;
    color: var(--text2);
    margin: 0;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

.ai-cat-wrap { background: var(--gray); padding: 60px 0; }

.ai-cat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 36px;
}

.ai-cat-header h2 {
    font-size: 26px;
    font-weight: 800;
    margin: 0;
    color: var(--dark);
    font-family: 'Inter', sans-serif;
}

.ai-cat-header a {
    color: var(--orange);
    font-weight: 700;
    font-size: 14px;
    text-decoration: none;
    font-family: 'Inter', sans-serif;
    display: flex;
    align-items: center;
    gap: 6px;
}

.ai-cat-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 24px;
}

.ai-cat-card {
    background: #fff;
    border-radius: 20px;
    padding: 20px;
    text-decoration: none;
    color: inherit;
    display: flex;
    align-items: center;
    gap: 16px;
    transition: all 0.3s ease;
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
}

.ai-cat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.1);
    border-color: var(--orange);
}

.ai-cat-img {
    width: 70px;
    height: 70px;
    flex-shrink: 0;
}

.ai-cat-img img {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

.ai-cat-info h3 {
    font-size: 15px;
    font-weight: 800;
    margin: 0 0 4px 0;
    color: var(--dark);
    font-family: 'Inter', sans-serif;
}

.ai-cat-info span {
    font-size: 12px;
    color: var(--text2);
    font-family: 'Inter', sans-serif;
    font-weight: 500;
}

@media (max-width: 1200px) {
    .ai-hero-inner { grid-template-columns: 340px 1fr; gap: 24px; }
    .ai-cat-grid { grid-template-columns: repeat(3, 1fr); }
    .ai-slider-card { min-height: 380px; }
}

@media (max-width: 992px) {
    .ai-hero-inner { grid-template-columns: 1fr; }
    .ai-cat-grid { grid-template-columns: repeat(2, 1fr); }
    .ai-features-inner { flex-wrap: wrap; }
    .ai-feat { min-width: 200px; padding: 10px; }
    .ai-feat:not(:last-child)::after { display: none; }
    .ai-slider-content h3 { font-size: 26px; }
    .ai-search-box { flex-wrap: wrap; }
    .ai-search-cat { border-right: none; border-bottom: 1px solid var(--border); width: 100%; padding: 12px; }
    .ai-search-go { width: 100%; }
}

@media (max-width: 576px) {
    .ai-cat-grid { grid-template-columns: 1fr; }
    .ai-calc-card { padding: 20px; }
    .ai-slider-content { padding: 30px; }
    .ai-slider-logo { font-size: 42px; }
    .ai-slider-content h3 { font-size: 22px; }
}
"""

twig = """{{ header }}

<style>
""" + css + """
</style>

<div id="content" class="home-page">

<div class="ai-hero-wrap">
    <div class="ai-hero-inner">
        <div class="ai-calc">
            <div class="ai-calc-card">
                <div class="ai-calc-top">
                    <h2><span class="ai-sparkle">&#x2728;</span> AI Калькулятор</h2>
                    <span class="ai-badge">AI</span>
                </div>
                <p class="ai-calc-desc">Рассчитайте количество материалов для вашего проекта</p>
                <div class="ai-calc-fields">
                    <div class="ai-field"><div class="ai-field-icon">&#x1F527;</div><div class="ai-field-body"><label>Тип работ</label><select><option>Стены</option><option>Пол</option><option>Потолок</option></select></div></div>
                    <div class="ai-field"><div class="ai-field-icon">&#x1F4CB;</div><div class="ai-field-body"><label>Материал</label><select><option>Гипсокартон KNAUF</option><option>Штукатурка</option><option>Шпаклёвка</option></select></div></div>
                    <div class="ai-field"><div class="ai-field-icon">&#x1F4D0;</div><div class="ai-field-body"><label>Площадь поверхности, м&#xB2;</label><input type="number" value="50"></div></div>
                    <div class="ai-field"><div class="ai-field-icon">&#x1F4CF;</div><div class="ai-field-body"><label>Высота стен, м</label><input type="number" value="2.7"></div></div>
                    <div class="ai-field"><div class="ai-field-icon">&#x1F3E0;</div><div class="ai-field-body"><label>Тип помещения</label><select><option>Жилое помещение</option><option>Ванная</option><option>Кухня</option></select></div></div>
                </div>
                <button type="button" class="ai-btn-calc">Рассчитать материалы <span class="ai-sparkle">&#x2728;</span></button>
                <p class="ai-calc-note">&#x2705; Точность расчёта на основе AI</p>
            </div>
        </div>
        <div class="ai-slider-wrap">
            <div class="ai-slider-card">
                <div class="ai-slider-img"><img src="https://stroiapp.ru/image/cache/catalog/1-1-1-6_1_64c0f53d3d421_thumb_2264c0f53d3e1a7-800x400.jpg" alt="KNAUF"></div>
                <div class="ai-slider-overlay"></div>
                <div class="ai-slider-content">
                    <div class="ai-slider-logo">KNAUF</div>
                    <h3>Немецкое качество<br>для вашего строительства</h3>
                    <div class="ai-slider-props">
                        <span><i>&#x2699;&#xFE0F;</i> Проверенные<br>технологии</span>
                        <span><i>&#x1F33F;</i> Экологичные<br>материалы</span>
                        <span><i>&#x1F6E1;&#xFE0F;</i> Надёжность<br>на годы</span>
                    </div>
                    <a href="index.php?route=product/category&amp;path=59" class="ai-btn-slider">Смотреть продукцию KNAUF</a>
                </div>
                <div class="ai-slider-dots"><span class="active"></span><span></span><span></span></div>
                <div class="ai-slider-arrows"><button>&lsaquo;</button><button>&rsaquo;</button></div>
            </div>
        </div>
    </div>
    <div class="ai-search-wrap">
        <div class="ai-search-box">
            <div class="ai-search-cat"><span>&#x2630;</span><select><option>Каталог товаров</option></select></div>
            <input type="text" placeholder="Поиск по товарам, брендам, категориям...">
            <button class="ai-search-go">Найти</button>
        </div>
        <div class="ai-search-tags">
            <a href="#">KNAUF</a>
            <a href="#">Гипсокартон</a>
            <a href="#">Утеплитель</a>
            <a href="#">Профиль</a>
        </div>
    </div>
</div>

<div class="ai-features-wrap">
    <div class="ai-features-inner">
        <div class="ai-feat"><div class="ai-feat-icon" style="background:#FFF0E6;">&#x1F69A;</div><div class="ai-feat-text"><h4>Быстрая доставка</h4><p>по всей России</p></div></div>
        <div class="ai-feat"><div class="ai-feat-icon" style="background:#FFF8E6;">&#x1F3C5;</div><div class="ai-feat-text"><h4>Гарантия качества</h4><p>на все товары</p></div></div>
        <div class="ai-feat"><div class="ai-feat-icon" style="background:#E6F7FF;">&#x1F3F7;&#xFE0F;</div><div class="ai-feat-text"><h4>Выгодные цены</h4><p>и акции</p></div></div>
        <div class="ai-feat"><div class="ai-feat-icon" style="background:#E6FFF0;">&#x1F504;</div><div class="ai-feat-text"><h4>Возврат товара</h4><p>в течение 14 дней</p></div></div>
        <div class="ai-feat"><div class="ai-feat-icon" style="background:#F0E6FF;">&#x1F3A7;</div><div class="ai-feat-text"><h4>Поддержка 24/7</h4><p>мы всегда на связи</p></div></div>
    </div>
</div>

<div class="ai-cat-wrap">
    <div class="ai-cat-inner">
        <div class="ai-cat-header"><h2>Популярные категории</h2><a href="index.php?route=product/category">Смотреть все категории &#x2192;</a></div>
        <div class="ai-cat-grid">
            {% for category in categories %}
            <a href="{{ category.href }}" class="ai-cat-card"><div class="ai-cat-info"><h3>{{ category.name }}</h3><span>Более {{ category.total_items|default('100') }} товаров</span></div><div class="ai-cat-img"><img src="{{ category.thumb|default('catalog/view/theme/unishop2/image/no_image.png') }}" alt="{{ category.name }}"></div></a>
            {% endfor %}
        </div>
    </div>
</div>

</div>

{{ footer }}
"""

# Save local
with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/template/common/home.twig', 'w', encoding='utf-8') as f:
    f.write(twig)

with open('D:/Projects/ai.stroiapp.ru/stroiapp.ru/public_html/catalog/view/theme/unishop2/stylesheet/ai_home.css', 'w', encoding='utf-8') as f:
    f.write(css)

print('Local saved:', len(twig), len(css))

# Upload
OPENCART_URL = 'https://stroiapp.ru'
TOKEN = 'change_this_ai_manager_token'

url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=file/writeSafe&token={TOKEN}'
r = requests.post(url, json={'path': 'catalog/view/theme/unishop2/template/common/home.twig', 'content': twig}, timeout=30)
raw = r.content
if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
data = json.loads(raw.decode('utf-8'))
print('twig:', data.get('status'))

cache_url = f'{OPENCART_URL}/index.php?route=api/ai_manager&action=site/clearCache&token={TOKEN}'
r2 = requests.post(cache_url, timeout=30)
raw2 = r2.content
if raw2.startswith(b'\xef\xbb\xbf'): raw2 = raw2[3:]
data2 = json.loads(raw2.decode('utf-8'))
print('cache:', data2.get('deleted', 0))
