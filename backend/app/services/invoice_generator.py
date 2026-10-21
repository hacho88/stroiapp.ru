"""PDF-счёт на оплату в стандарте 1С для витрин (moscow.stroiapp.ru и др.).

Макет: банковская сетка получателя → заголовок → блок сторон → таблица
товаров → итоги с НДС 20% → сумма прописью → условия → подписи с
факсимиле (подпись + круглая печать на прозрачных PNG-слоях).

Если в backend/assets/ лежат настоящие stamp.png / signature.png —
используются они; иначе генерируются программные факсимиле через PIL.
"""

import io
import math
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ASSETS = Path(__file__).resolve().parents[2] / "assets"

# Реквизиты поставщика — из карточки счёта СберБизнес (ПАО Сбербанк).
SUPPLIER = {
    "name": 'ООО "МИКС СТРОЙ"',
    "inn": "5029246038",
    "kpp": "502901001",
    "ogrn": "1195081039890",
    "address": "141013, Московская обл, г. Мытищи, ул. Силикатная, дом 42, офис 2",
    "bank": "ПАО Сбербанк",
    "bik": "044525225",
    "corr": "30101810400000000225",   # корреспондентский счёт
    "account": "40702810038000073174", # расчётный счёт получателя
}

DIRECTOR = "Калмуратов Т. К."
ACCOUNTANT = "Калмуратов Т. К."


# ---------- Шрифты с кириллицей ----------

def _register_fonts() -> tuple[str, str]:
    """Возвращает (regular, bold) имена зарегистрированных шрифтов."""
    candidates = [
        ("/var/www/ai-manager/assets/arial.ttf", "/var/www/ai-manager/assets/arialbd.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    try:
        import reportlab
        base = Path(reportlab.__file__).parent / "fonts"
        candidates.append((str(base / "Vera.ttf"), str(base / "VeraBd.ttf")))
    except Exception:
        pass
    for reg, bold in candidates:
        try:
            pdfmetrics.registerFont(TTFont("InvSans", reg))
            try:
                pdfmetrics.registerFont(TTFont("InvSansB", bold))
            except Exception:
                pdfmetrics.registerFont(TTFont("InvSansB", reg))
            return "InvSans", "InvSansB"
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold"


# ---------- Сумма прописью (рус.) ----------

_U1_M = ["", "один", "два", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
_U1_F = ["", "одна", "две", "три", "четыре", "пять", "шесть", "семь", "восемь", "девять"]
_TEEN = ["десять", "одиннадцать", "двенадцать", "тринадцать", "четырнадцать",
         "пятнадцать", "шестнадцать", "семнадцать", "восемнадцать", "девятнадцать"]
_TENS = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят",
         "шестьдесят", "семьдесят", "восемьдесят", "девяносто"]
_HUND = ["", "сто", "двести", "триста", "четыреста", "пятьсот",
         "шестьсот", "семьсот", "восемьсот", "девятьсот"]
_GROUP = [  # (единственное, 2-4, множественное), женский род
    ("", "", "", False),
    ("тысяча", "тысячи", "тысяч", True),
    ("миллион", "миллиона", "миллионов", False),
    ("миллиард", "миллиарда", "миллиардов", False),
]


def _plural(n: int, forms: tuple[str, str, str]) -> str:
    n10, n100 = n % 10, n % 100
    if 11 <= n100 <= 19 or n10 == 0 or n10 >= 5:
        return forms[2]
    return forms[0] if n10 == 1 else forms[1]


def _num3(n: int, feminine: bool) -> str:
    parts = [_HUND[n // 100]]
    r = n % 100
    if r >= 20:
        parts.append(_TENS[r // 10])
        parts.append((_U1_F if feminine else _U1_M)[r % 10])
    elif r >= 10:
        parts.append(_TEEN[r - 10])
    else:
        parts.append((_U1_F if feminine else _U1_M)[r])
    return " ".join(p for p in parts if p)


def num_to_words(n: int) -> str:
    """Целое число → русские слова (строчными), до миллиардов."""
    if n == 0:
        return "ноль"
    groups = []
    i = 0
    while n > 0:
        g, n = n % 1000, n // 1000
        groups.append((g, i))
        i += 1
    parts = []
    for g, i in reversed(groups):
        if g == 0:
            continue
        name, fem = _GROUP[i], _GROUP[i][3]
        parts.append(_num3(g, fem))
        if i:
            parts.append(_plural(g, name[:3]))
    return " ".join(parts)


def money_words(total: float) -> str:
    """'Триста семьдесят тысяч пятьсот рублей 00 копеек'."""
    rub, kop = int(total), round((total - int(total)) * 100)
    if kop >= 100:
        rub, kop = rub + 1, 0
    w = num_to_words(rub).capitalize()
    return f"{w} {_plural(rub, ('рубль', 'рубля', 'рублей'))} {kop:02d} копеек"


# ---------- Факсимиле: печать и подпись (генерируются при отсутствии PNG) ----------

def _font_for_pil(size: int, bold: bool = False):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""),
              "/var/www/ai-manager/assets/arial%s.ttf" % ("bd" if bold else "")):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _ring_text(img, cx: int, cy: int, radius: int, text: str, size: int,
               start_deg: float, end_deg: float, blue) -> None:
    """Рисует текст по дуге окружности (штамп)."""
    from PIL import Image, ImageDraw
    font = _font_for_pil(size, bold=True)
    n = max(len(text) - 1, 1)
    for i, ch in enumerate(text):
        ang = math.radians(start_deg + (end_deg - start_deg) * i / n)
        tile = Image.new("RGBA", (size * 3, size * 3), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text((size, size), ch, font=font, fill=blue)
        # поворот тайла: буква «читает» по касательной к окружности
        deg = -math.degrees(ang) - 90
        tile = tile.rotate(deg, resample=Image.BICUBIC, center=(size * 1.5, size * 1.5))
        x = cx + radius * math.cos(ang) - tile.width / 2
        y = cy + radius * math.sin(ang) - tile.height / 2
        img.paste(tile, (int(x), int(y)), tile)


def _gen_stamp(path: Path) -> None:
    """Синяя круглая печать ООО «МИКС СТРОЙ» — прозрачный PNG."""
    from PIL import Image, ImageDraw
    S, cx = 420, 210
    blue = (27, 61, 165, 170)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([14, 14, S - 14, S - 14], outline=blue, width=5)
    d.ellipse([64, 64, S - 64, S - 64], outline=blue, width=2)
    _ring_text(img, cx, cx, 148, 'ООО «МИКС СТРОЙ»', 34, -160, -20, blue)
    _ring_text(img, cx, cx, 148, "РОССИЯ", 30, 155, 25, blue)
    f = _font_for_pil(30, bold=True)
    d.text((cx, cx - 52), "ИНН", font=f, fill=blue, anchor="mm")
    d.text((cx, cx - 12), SUPPLIER["inn"], font=f, fill=blue, anchor="mm")
    d.text((cx, cx + 28), "ОГРН", font=_font_for_pil(26, bold=True), fill=blue, anchor="mm")
    d.text((cx, cx + 62), SUPPLIER["ogrn"], font=_font_for_pil(22, bold=True), fill=blue, anchor="mm")
    img = img.rotate(-14, resample=Image.BICUBIC)
    img.save(path)


def _gen_signature(path: Path) -> None:
    """Рукописная подпись-факсимиле: синие плавные штрихи, прозрачный PNG."""
    from PIL import Image, ImageDraw
    W, H = 640, 170
    blue = (20, 40, 170, 210)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def cubic(p0, p1, p2, p3, steps=60):
        pts = []
        for i in range(steps + 1):
            t = i / steps
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + \
                3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + \
                3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
            pts.append((x, y))
        return pts

    strokes = [
        ([(30, 120), (60, 30), (110, 140), (140, 45)], 4),     # заглавный росчерк
        ([(140, 45), (170, 130), (210, 30), (235, 110)], 3),   # петля
        ([(235, 110), (260, 40), (300, 120), (330, 60)], 3),   # вторая петля
        ([(330, 60), (360, 130), (420, 55), (450, 95)], 3),    # волнистый хвост
        ([(450, 95), (480, 125), (530, 90), (600, 115)], 3),   # длинный мах
        ([(90, 150), (300, 155), (480, 145), (610, 150)], 2),  # подчёркивание
    ]
    for pts, w in strokes:
        line = cubic(*pts)
        d.line(line, fill=blue, width=w, joint="curve")
    img = img.rotate(-6, resample=Image.BICUBIC)
    img.save(path)


def _ensure_facsimile() -> tuple[Path | None, Path | None]:
    """Возвращает (stamp.png, signature.png), генерируя при отсутствии."""
    try:
        ASSETS.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    stamp, sign = ASSETS / "stamp.png", ASSETS / "signature.png"
    try:
        if not stamp.exists():
            _gen_stamp(stamp)
        if not sign.exists():
            _gen_signature(sign)
    except Exception:
        return (stamp if stamp.exists() else None,
                sign if sign.exists() else None)
    return stamp, sign


# ---------- Отрисовка ----------

def _money(v: float) -> str:
    return f"{v:,.2f}".replace(",", " ")


def _wrap(c, text: str, font: str, size: float, width: float) -> list[str]:
    """Грубый перенос по словам по ширине в пунктах."""
    out, cur = [], ""
    for word in str(text).split():
        trial = f"{cur} {word}".strip()
        if c.stringWidth(trial, font, size) <= width:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out or [""]


def render_invoice_pdf(req, items) -> bytes:
    """req — объект с полями inn/kpp/name/address/phone; items — CartItem[].

    Полный 1C-макет счёта на оплату.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    F, FB = _register_fonts()
    x0, x1 = 40, W - 40
    TW = x1 - x0
    now = datetime.now()

    # ============ 1. Банковская сетка получателя ============
    gy = H - 40                      # верх сетки
    L_W, R_W = 360, TW - 360         # левая (получатель) / правая (счета)
    MID_W = 52                        # колонка «БИК» / «Сч. №»
    r1h, r2h, r3h = 30, 15, 42       # правые строки: БИК / корсчёт / р/с
    grid_h = r1h + r2h + r3h

    c.setLineWidth(0.8)
    # левый блок: банк (r1h+r2h) + получатель (r3h)
    c.rect(x0, gy - r1h - r2h, L_W, r1h + r2h)
    c.rect(x0, gy - grid_h, L_W, r3h)
    # правый блок: 3 строки
    c.rect(x0 + L_W, gy - r1h, R_W, r1h)
    c.rect(x0 + L_W, gy - r1h - r2h, R_W, r2h)
    c.rect(x0 + L_W, gy - grid_h, R_W, r3h)
    # внутренняя колонка меток в правом блоке
    mx = x0 + L_W + MID_W
    c.line(mx, gy, mx, gy - grid_h)

    pad = 4
    # банк получателя
    c.setFont(FB, 9)
    c.drawString(x0 + pad, gy - 13, SUPPLIER["bank"] or " ")
    c.setFont(F, 7)
    c.setFillGray(0.35)
    c.drawString(x0 + pad, gy - r1h - r2h + 4, "Банк получателя")
    c.setFillGray(0)
    # БИК + корсчёт
    c.setFont(F, 8.5)
    c.drawString(x0 + L_W + pad, gy - r1h + 6, "БИК")
    c.drawString(x0 + L_W + pad, gy - r1h - r2h + 4, "Сч. №")
    c.setFont(FB, 9)
    c.drawString(mx + pad, gy - r1h + 6, SUPPLIER["bik"] or " ")
    c.drawString(mx + pad, gy - r1h - r2h + 4, SUPPLIER["corr"] or " ")
    # получатель: ИНН+КПП → название → подпись «Получатель» внизу ячейки
    c.setFont(FB, 8.5)
    c.drawString(x0 + pad, gy - r1h - r2h - 14,
                 f'ИНН {SUPPLIER["inn"]}  КПП {SUPPLIER["kpp"]}')
    c.drawString(x0 + pad, gy - r1h - r2h - 27, SUPPLIER["name"])
    c.setFont(F, 7)
    c.setFillGray(0.35)
    c.drawString(x0 + pad, gy - grid_h + 4, "Получатель")
    c.setFillGray(0)
    c.setFont(F, 8.5)
    c.drawString(x0 + L_W + pad, gy - grid_h + 20, "Сч. №")
    c.setFont(FB, 9)
    c.drawString(mx + pad, gy - grid_h + 20, SUPPLIER["account"] or " ")

    y = gy - grid_h - 40

    # ============ 2. Заголовок ============
    num = f"МСК-{now:%d%m%Y}-{now:%H%M}"
    c.setFont(FB, 15)
    c.drawString(x0, y, f"Счет на оплату № {num} от {now:%d.%m.%Y} г.")
    y -= 8
    c.setLineWidth(1.2)
    c.line(x0, y, x1, y)
    y -= 20

    # ============ 3. Блок сторон ============
    c.setFont(FB, 8.5)
    c.drawString(x0, y, "Поставщик (Исполнитель):")
    c.setFont(F, 8.5)
    sup = (f'ИНН {SUPPLIER["inn"]}, КПП {SUPPLIER["kpp"]}, {SUPPLIER["name"]}, '
           f'{SUPPLIER["address"]}')
    for line in _wrap(c, sup, F, 8.5, TW - 150):
        c.drawString(x0 + 150, y, line)
        y -= 11
    y -= 4
    c.setFont(FB, 8.5)
    c.drawString(x0, y, "Покупатель (Заказчик):")
    c.setFont(F, 8.5)
    bparts = [f"ИНН {req.inn}"]
    if getattr(req, "kpp", ""):
        bparts.append(f"КПП {req.kpp}")
    if req.name:
        bparts.append(req.name)
    if getattr(req, "address", ""):
        bparts.append(req.address)
    if req.phone:
        bparts.append(f"тел. {req.phone}")
    for line in _wrap(c, ", ".join(bparts), F, 8.5, TW - 150):
        c.drawString(x0 + 150, y, line)
        y -= 11
    y -= 4
    c.setFont(FB, 8.5)
    c.drawString(x0, y, "Основание:")
    c.setFont(F, 8.5)
    c.drawString(x0 + 150, y, "Заказ покупателя")
    y -= 26

    # ============ 4. Таблица товаров ============
    cols = [25, TW - 25 - 55 - 40 - 80 - 80, 55, 40, 80, 80]
    heads = ["№", "Товары (работы, услуги)", "Кол-во", "Ед.", "Цена", "Сумма"]
    hh, rh = 18, 13

    def table_header(y_top):
        c.setFillGray(0.92)
        c.rect(x0, y_top - hh, TW, hh, stroke=0, fill=1)
        c.setFillGray(0)
        c.setStrokeGray(0)
        c.setLineWidth(0.7)
        c.rect(x0, y_top - hh, TW, hh)
        cx = x0
        c.setFont(FB, 8)
        for w, htxt in zip(cols, heads):
            c.rect(cx, y_top - hh, w, hh)
            c.drawCentredString(cx + w / 2, y_top - hh + 5, htxt)
            cx += w
        return y_top - hh

    y = table_header(y)
    c.setFont(F, 8.5)
    total = 0.0
    for i, it in enumerate(items, 1):
        s = it.qty * it.price
        total += s
        lines = _wrap(c, it.name, F, 8.5, cols[1] - 8)
        rh_cur = max(rh, 4 + 10 * len(lines))
        if y - rh_cur < 110:                       # новая страница
            c.showPage()
            c.setFont(F, 8.5)
            y = table_header(H - 40)
        cx = x0
        c.setLineWidth(0.5)
        for w in cols:
            c.rect(cx, y - rh_cur, w, rh_cur)
            cx += w
        c.drawCentredString(x0 + cols[0] / 2, y - rh_cur + 4, str(i))
        ty = y - 10
        for line in lines:
            c.drawString(x0 + cols[0] + 4, ty, line)
            ty -= 10
        cx = x0 + cols[0] + cols[1]
        c.drawRightString(cx + cols[2] - 5, y - rh_cur + 4, str(it.qty))
        cx += cols[2]
        c.drawCentredString(cx + cols[3] / 2, y - rh_cur + 4, "шт")
        cx += cols[3]
        c.drawRightString(cx + cols[4] - 5, y - rh_cur + 4, _money(it.price))
        cx += cols[4]
        c.drawRightString(cx + cols[5] - 5, y - rh_cur + 4, _money(s))
        y -= rh_cur

    # ============ 5. Итоги (правый край) ============
    y -= 12
    vat = round(total / 120 * 20, 2)
    c.setFont(FB, 9)
    for label, val in (("Итого:", _money(total)),
                       ("В том числе НДС 20%:", _money(vat)),
                       ("Всего к оплате:", _money(total))):
        c.drawString(x1 - 190, y, label)
        c.drawRightString(x1, y, val)
        y -= 13
    y -= 10

    # ============ 6. Сумма прописью ============
    c.setFont(F, 8.5)
    c.drawString(x0, y,
                 f"Всего наименований {len(items)}, на сумму {_money(total)} руб.")
    y -= 12
    c.setFont(FB, 8.5)
    for line in _wrap(c, money_words(total), FB, 8.5, TW):
        c.drawString(x0, y, line)
        y -= 11
    y -= 8
    c.setLineWidth(0.7)
    c.line(x0, y, x1, y)
    y -= 16

    # ============ 7. Условия ============
    c.setFont(F, 7)
    c.setFillGray(0.3)
    terms = [
        "Оплата данного счета означает согласие с условиями поставки товара.",
        "Уведомление об оплате обязательно, в противном случае не гарантируется",
        "наличие товара на складе. Товар отпускается по факту прихода денег",
        "на р/с Поставщика, самовывозом, при наличии доверенности и паспорта.",
        "Счёт действителен 5 банковских дней.",
    ]
    for t in terms:
        c.drawString(x0, y, t)
        y -= 9
    c.setFillGray(0)
    y -= 24

    # ============ 8. Подписи + факсимиле ============
    stamp_png, sign_png = _ensure_facsimile()
    if y < 130:                      # подписям нужно ~90pt вниз
        c.showPage()
        y = H - 60
    c.setFont(F, 9)
    sig_rows = []
    for role, person in (("Руководитель", DIRECTOR), ("Бухгалтер", ACCOUNTANT)):
        c.drawString(x0, y, role)
        c.line(x0 + 78, y - 2, x0 + 240, y - 2)
        c.drawString(x0 + 244, y, f"({person})")
        sig_rows.append(y)
        y -= 30
    # прозрачные оверлеи: росчерк поверх линий + круглая печать поверх зоны подписей
    try:
        if sign_png and sign_png.exists():
            for sy in sig_rows:
                c.drawImage(str(sign_png), x0 + 76, sy - 20, width=150, height=38,
                            mask="auto")
        if stamp_png and stamp_png.exists():
            c.drawImage(str(stamp_png), x0 + 170, y - 60, width=120, height=120,
                        mask="auto")
    except Exception as exc:
        print(f"[invoice] facsimile overlay failed: {exc}")

    c.showPage()
    c.save()
    return buf.getvalue()
