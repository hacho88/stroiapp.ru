import urllib.request, ssl, json, socket, time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    ip = socket.gethostbyname("stroiapp.ru")
except:
    ip = "188.225.23.151"

h = {"Content-Type": "application/json", "X-AI-Token": "change_this_ai_manager_token", "Host": "stroiapp.ru"}

def post(action, payload, timeout=30):
    d = json.dumps(payload).encode()
    req = urllib.request.Request(f"https://{ip}/index.php?route=api/ai_manager&action={action}", data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

def post_direct(route, payload, timeout=30):
    d = json.dumps(payload).encode()
    url = f"https://{ip}/index.php?route={route}"
    req = urllib.request.Request(url, data=d, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        return json.loads(r.read().decode("utf-8-sig"))

# First, get all articles via PHP controller
list_php = r"""<?php
class ControllerApiBlogListAll extends Controller {
    public function index() {
        $articles = $this->db->query("SELECT article_id, title, slug, intro, meta_title, meta_description FROM `" . DB_PREFIX . "blog_article` ORDER BY article_id");
        echo json_encode(array("status" => "ok", "articles" => $articles->rows));
        exit;
    }
}
"""

print("=== Writing list controller ===")
r1 = post("file/writeSafe", {"path": "catalog/controller/api/blog_list_all.php", "content": list_php})
print(f"  {r1}")

time.sleep(1)
print("\n=== Getting all articles ===")
req = urllib.request.Request(f"https://{ip}/index.php?route=api/blog_list_all", headers={"Host": "stroiapp.ru"})
try:
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        body = r.read().decode('utf-8', errors='replace')
        data = json.loads(body)
        articles = data.get("articles", [])
        print(f"  Found {len(articles)} articles:")
        for a in articles:
            print(f"    id={a['article_id']} slug={a['slug']} title={a['title'][:50]}")
except Exception as e:
    print(f"  Error: {e}")
    articles = []

# Full content for each article
full_articles = {
    1: {
        "title": "Как выбрать штукатурку: гипс, цемент или полимер — реальный опыт",
        "slug": "kak-vybrat-shtukaturku",
        "intro": "15 лет ставлю штукатурку на объектах в Москве. Разбираю, когда брать Ротбанд, когда цементную, и почему новички ошибаются на ровном месте.",
        "meta_title": "Как выбрать штукатурку: гипс или цемент — советы строителя | Блог",
        "meta_description": "Реальный опыт выбора штукатурки: Ротбанд vs цементная vs полимерная. Расход, цены, частые ошибки. Купить с НДС на StroiApp.ru.",
        "content": (
            "<h2>Гипсовая штукатурка: когда брать Ротбанд</h2>"
            "<p>На моём опыте — Ротбанд это действительно золотой стандарт для сухих помещений. "
            "За 15 лет ставил его на квартиры, офисы, склады. Расход — около 8.5 кг/м2 при слое 10 мм. "
            "Мешок 30 кг стоит 450-500 рублей. На комнату 20 м2 со стенами 2.7 м уходит 15-18 мешков.</p>"
            "<h3>Плюсы Ротбанда</h3>"
            "<ul><li><strong>Лёгкий</strong> — гипс легче цемента, меньше нагрузка на стены</li>"
            "<li><strong>Пластичный</strong> — легко тянуть, не рвётся</li>"
            "<li><strong>Быстро сохнет</strong> — 5-7 дней против 28 дней у цементной</li>"
            "<li><strong>Белый</strong> — под светлую краску не нужно дополнительно шпаклевать</li></ul>"
            "<h3>Минусы</h3>"
            "<ul><li>Только сухие помещения — в ванной, туалете, на балконе нельзя</li>"
            "<li>Боится влаги — если затопят соседи, штукатурка разбухнет</li>"
            "<li>Дороже цементной на 20-30%</li></ul>"
            "<h2>Цементная штукатурка: для влажных зон и фасадов</h2>"
            "<p>Цементно-песчаная смесь — классика для фасадов, подвалов, санузлов. "
            "Weber-Vetonit TT, Litokol Litoplaster, Knauf Diamant — все работают по одному принципу. "
            "Расход — 12-17 кг/м2 при слое 10 мм. Мешок 25 кг стоит 350-450 рублей.</p>"
            "<h3>Когда выбирать цементную</h3>"
            "<ul><li>Ванные, душевые, туалеты — повышенная влажность</li>"
            "<li>Фасады, балконы, лоджии — перепады температур</li>"
            "<li>Подвалы, гаражи — бетонные стены, нужна прочность</li>"
            "<li>Под плитку в мокрых зонах — цементная основа лучше для клея</li></ul>"
            "<p>Был случай: делал квартиру в новостройке на Юго-Западной. Заказчик настоял на Ротбанде во всём, включая ванную. Через год плитка в душевой начала отходить — гипс впитал влагу через швы. Переделывали на цементную. Урок: не экономьте на правильном материале для мокрых зон.</p>"
            "<h2>Полимерная и декоративная штукатурка</h2>"
            "<p>Если нужен декор — короед, барашек, венецианка — это полимерные или силиконовые смеси. "
            "Ceresit CT60, Weber.pas silikon — для фасадов. Расход 2-4 кг/м2, цена от 1500 рублей за мешок. "
            "Это финишный слой, не для выравнивания.</p>"
            "<h2>Как рассчитать количество</h2>"
            "<p>Формула простая: площадь стен × толщина слоя в мм × расход/м2/10. "
            "Пример: комната 4×3 м, высота 2.7 м, стены 33 м2, слой 15 мм, Ротбанд 8.5 кг/м2. "
            "Расход: 33 × 15 × 0.85 = 420 кг = 14 мешков по 30 кг. Берите с запасом 10% — 16 мешков.</p>"
            "<h2>Частые ошибки при выборе</h2>"
            "<ul><li><strong>Берут гипсовую в ванную</strong> — самая частая ошибка новичков</li>"
            "<li><strong>Не грунтуют перед штукатуркой</strong> — адгезия падает, через год отваливается</li>"
            "<li><strong>Экономят на смеси</strong> — берут ноунейм за 200 рублей, потом переделывают</li>"
            "<li><strong>Не учитывают кривизну стен</strong> — в старом фонде слой может быть 30-40 мм, не 10</li></ul>"
            "<p>Заказать штукатурку Knauf, Weber, Ceresit с безналом и НДС можно на StroiApp.ru — доставка по Москве и МО, оптовые цены.</p>"
        ),
    },
    2: {
        "title": "Грунтовка Ceresit CT99: когда глубокое проникновение решает",
        "slug": "gruntovka-ceresit-ct99-glubokoe-proniknovenie",
        "intro": "Разбираю, когда Ceresit CT99 реально нужен, а когда это лишняя трата. Личный опыт на объектах в Москве.",
        "meta_title": "Ceresit CT99: когда нужна грунтовка глубокого проникновения | Блог",
        "meta_description": "Личный опыт применения Ceresit CT99 на объектах в Москве: когда работает, когда лишняя, расход, цена, частые ошибки.",
        "content": (
            "<h2>Зачем вообще нужна грунтовка глубокого проникновения</h2>"
            "<p>На моём опыте — процентов 70 проблем с отделкой возникают из-за плохой подготовки основания. "
            "Ceresit CT99 — это не универсальная грунтовка, у неё конкретная задача: связать рыхлое, "
            "пылящее основание и укрепить его перед нанесением штукатурки, шпаклёвки или плиточного клея.</p>"
            "<h3>Когда CT99 реально работает</h3>"
            "<ul><li><strong>Рыхлые, пылящие основания</strong> — старая штукатурка, которая держится, но осыпается</li>"
            "<li><strong>Газобетон и пенобетон</strong> — грунт заходит в поры и связывает поверхность</li>"
            "<li><strong>Гипсолитые перегородки</strong> — в новостройках часто крошатся, CT99 решает</li>"
            "<li><strong>Перед штукатуркой по старой краске</strong> — после зачистки, для адгезии</li></ul>"
            "<h3>Когда это лишняя трата</h3>"
            "<p>Если основание плотное — монолитный бетон, кирпич клинкерный — обычный контактный грунт "
            "(тот же Ceresit CT16 или Betonkontakt) работает лучше и дешевле. CT99 на плотной поверхности "
            "просто лежит поверх и не впитывается. Вы платите за глубокое проникновение, которого не происходит.</p>"
            "<h2>Расход и цена</h2>"
            "<p>Расход — 0.1-0.2 л/м2 в зависимости от впитываемости основания. "
            "Цена около 400-500 рублей за 10 литров концентрата. "
            "На квартиру 60 м2 (стены + потолок) уходит 2-3 канистры. "
            "Разводится водой 1:1 для первого слоя, 1:2 для второго — читайте инструкцию на канистре.</p>"
            "<h2>История из практики</h2>"
            "<p>Делал ремонт в хрущёвке на Люблинской линии. Стены — старая цементная штукатурка, "
            "местами рыхлая, пальцем ковыряешь — крошится. Заказчик хотел сэкономить: «да зачем грунтовать, "
            "и так сойдёт». Я настоял. После CT99 поверхность стала твёрдой, штукатурка держится уже 4 года. "
            "А в соседней квартире, где не грунтовали — через год пошли трещины и отслоения.</p>"
            "<h2>Как правильно грунтовать</h2>"
            "<ul><li><strong>Шаг 1</strong> — очистить поверхность от пыли и грязи. Пылесосом, не веником</li>"
            "<li><strong>Шаг 2</strong> — развести CT99 по инструкции (1:1 для впитывающих оснований)</li>"
            "<li><strong>Шаг 3</strong> — нанести валиком или кистью в один слой, не лить лужами</li>"
            "<li><strong>Шаг 4</strong> — дождаться полного высыхания (2-4 часа, лучше сутки)</li>"
            "<li><strong>Шаг 5</strong> — если основание очень впитывающее, повторить вторым слоем</li></ul>"
            "<h2>Частые ошибки</h2>"
            "<ul><li><strong>Грунтовать по грязи</strong> — сначала убрать пыль, потом грунтовать</li>"
            "<li><strong>Разводить водой на глаз</strong> — нарушается концентрация полимеров</li>"
            "<li><strong>Не ждать высыхания</strong> — штукатурка по мокрой грунтовке не держится</li>"
            "<li><strong>Лить, а не наносить</strong> — грунт должен впитаться, не стоять лужами</li>"
            "<li><strong>Использовать CT99 вместо контактного грунта</strong> — для плотных оснований нужен Betonkontakt</li></ul>"
            "<h2>Чем заменить</h2>"
            "<p>Аналоги CT99: Caparol Deep Grund, Weber.prim 801, Litokol Primer-F. "
            "По характеристикам похожи, цена в том же диапазоне. Если нужен бюджетный вариант — "
            "Оlympic Грунт глубокого проникновения, но качество ниже.</p>"
            "<p>Заказать Ceresit CT99 и другие грунтовки с безналом и НДС можно на StroiApp.ru — "
            "доставка по Москве и МО, оптовые цены.</p>"
        ),
    },
}

# Update each article
for article in articles:
    aid = int(article["article_id"])
    if aid in full_articles:
        print(f"\n=== Updating article_id={aid} ===")
        payload = full_articles[aid]
        payload["article_id"] = aid
        r2 = post_direct("api/blog_update", payload)
        print(f"  {r2}")
    else:
        print(f"\n=== Skipping article_id={aid} (no content prepared) ===")

# Clear cache
print("\n=== Clear cache ===")
r3 = post("site/clearCache", {})
print(f"  {r3}")

time.sleep(3)

# Test all articles
for article in articles:
    aid = int(article["article_id"])
    slug = article["slug"]
    print(f"\n=== Test /blog/{slug} ===")
    req = urllib.request.Request(f"https://{ip}/blog/{slug}", headers={"Host": "stroiapp.ru"})
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
            body = r.read().decode('utf-8', errors='replace')
            import re
            article_match = re.search(r'<article>(.*?)</article>', body, re.DOTALL)
            if article_match:
                article_text = re.sub(r'<[^>]+>', '', article_match.group(1))
                char_count = len(article_text.strip())
                print(f"  HTTP {r.status}, {len(body)} bytes, text: {char_count} chars")
                if char_count > 2000:
                    print(f"  ✓ Good length!")
                else:
                    print(f"  ⚠ Short: {char_count} chars")
            if 'application/ld+json' in body:
                print(f"  ✓ JSON-LD present!")
    except Exception as e:
        print(f"  Error: {e}")

print("\nDONE")
