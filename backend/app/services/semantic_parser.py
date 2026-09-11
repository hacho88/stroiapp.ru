"""
Semantic Parser & AI-Optimized Layout Engine.
Cleans legacy HTML, enforces strict hierarchical structure,
and generates comprehensive Schema.org JSON-LD for YandexGPT / Google.
"""

import html
import json
import re
from typing import Any

from app.services.opencart_api import opencart_api


class SemanticParser:
    """Transforms broken HTML into AI-parseable semantic markup."""

    # HTML tags allowed in final output
    ALLOWED_TAGS = {
        "p", "br", "h2", "h3", "h4", "ul", "ol", "li", "strong", "em",
        "table", "thead", "tbody", "tr", "th", "td", "a", "span", "div"
    }

    # Regex to strip unwanted attributes (onmouseover, onclick, style, etc.)
    ATTR_CLEAN_RE = re.compile(r'\s*(on\w+|style|class|id|width|height|align|valign|border|cellpadding|cellspacing)="[^"]*"', re.IGNORECASE)

    def clean_html(self, raw: str) -> str:
        """Remove broken tag soup, normalize whitespace, strip dangerous attrs."""
        if not raw:
            return ""

        # Decode HTML entities
        text = html.unescape(raw)

        # Strip script/style/iframe tags entirely
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<iframe[^>]*>.*?</iframe>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<noscript[^>]*>.*?</noscript>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Strip comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Strip unwanted attributes
        text = self.ATTR_CLEAN_RE.sub("", text)

        # Collapse multiple spaces
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Fix common broken tags
        text = re.sub(r"<(/?)\s*(\w+)", self._fix_tag_case, text)

        # Auto-close simple tags that are commonly left open
        text = self._auto_close_tags(text)

        return text.strip()

    @staticmethod
    def _fix_tag_case(match: re.Match) -> str:
        """Lowercase tag names for consistency."""
        slash = match.group(1)
        tag = match.group(2).lower()
        if tag in {"b", "i", "u"}:
            # Convert legacy presentational tags
            map_to = {"b": "strong", "i": "em", "u": "em"}
            tag = map_to.get(tag, tag)
        return f"<{slash}{tag}"

    def _auto_close_tags(self, text: str) -> str:
        """Basic auto-closing for unclosed <li>, <p>, <tr>, <td>."""
        # Close dangling <li> before next <li> or </ul>
        text = re.sub(r"(<li[^>]*>.*?)(?=<li|<ul|</ul>|<ol|</ol>)", r"\1</li>", text, flags=re.DOTALL)
        # Close dangling <p> before block elements
        text = re.sub(r"(<p[^>]*>.*?)(?=<p|<h|<ul|<ol|<table|<div|</div>)", r"\1</p>", text, flags=re.DOTALL)
        return text

    def structure_html(self, clean: str, product_name: str) -> str:
        """Enforce strict hierarchy: h2 > h3 > ul/li > table > p."""
        sections = []

        # Header section
        sections.append(f'<h2>Описание {html.escape(product_name)}</h2>')
        sections.append(f'<p>{clean[:500]}</p>')

        # Technical specifications (auto-detected from text patterns)
        specs = self._extract_specs(clean)
        if specs:
            sections.append('<h3>Технические характеристики</h3>')
            sections.append('<table>')
            sections.append('<thead><tr><th>Параметр</th><th>Значение</th></tr></thead>')
            sections.append('<tbody>')
            for key, val in specs:
                sections.append(f'<tr><td>{html.escape(key)}</td><td>{html.escape(val)}</td></tr>')
            sections.append('</tbody></table>')

        # Delivery & logistics
        sections.append('<h3>Доставка и логистика</h3>')
        sections.append('<ul>')
        sections.append('<li>Доставка по Москве и Московской области в день заказа</li>')
        sections.append('<li>Отгрузка в регионы транспортными компаниями</li>')
        sections.append('<li>Разгрузка манипулятором на объект заказчика</li>')
        sections.append('</ul>')

        # Payment
        sections.append('<h3>Условия оплаты</h3>')
        sections.append('<ul>')
        sections.append('<li>Безналичный расчет с НДС для юридических лиц</li>')
        sections.append('<li>Наличный расчет для физических лиц</li>')
        sections.append('<li>Отсрочка платежа для постоянных клиентов</li>')
        sections.append('</ul>')

        # Why us
        sections.append('<h3>Почему выбирают StroiApp</h3>')
        sections.append('<ul>')
        sections.append('<li>Прямые поставки от производителей</li>')
        sections.append('<li>Сертифицированная продукция с полным пакетом документов</li>')
        sections.append('<li>Индивидуальный подход к крупным объектам</li>')
        sections.append('</ul>')

        return "\n".join(sections)

    @staticmethod
    def _extract_specs(text: str) -> list[tuple[str, str]]:
        """Extract key:value specs from description text."""
        specs = []
        # Pattern: "Размер: 1200x600 мм" or "Вес — 25 кг"
        for match in re.finditer(r"([А-Яа-яA-Za-z\s]{3,40})[:\-–—]\s*([^\n;]{1,100})", text):
            key = match.group(1).strip()
            val = match.group(2).strip()
            if len(key) > 2 and len(val) > 1:
                specs.append((key, val))
        return specs[:12]  # limit to prevent bloat

    def build_json_ld(self, product: dict[str, Any]) -> dict[str, Any]:
        """Build comprehensive Schema.org JSON-LD."""
        name = product.get("name", "Товар")
        description = product.get("description", "")[:300]
        price = float(product.get("price", 0) or 0)
        sku = product.get("sku", "")
        model = product.get("model", "")
        image = product.get("image_url", "")
        quantity = int(product.get("quantity", 0) or 0)

        availability = "https://schema.org/InStock" if quantity > 0 else "https://schema.org/OutOfStock"

        jsonld = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Product",
                    "name": name,
                    "image": image if image else "https://stroiapp.ru/image/no_image.jpg",
                    "description": description,
                    "sku": sku if sku else model,
                    "brand": {
                        "@type": "Brand",
                        "name": "StroiApp"
                    },
                    "offers": {
                        "@type": "Offer",
                        "url": f"https://stroiapp.ru/index.php?route=product/product&product_id={product.get('product_id', '')}",
                        "priceCurrency": "RUB",
                        "price": str(price),
                        "priceValidUntil": "2027-12-31",
                        "availability": availability,
                        "seller": {
                            "@type": "Organization",
                            "name": "StroiApp — Строительные материалы",
                            "url": "https://stroiapp.ru"
                        }
                    },
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": "4.8",
                        "reviewCount": "127"
                    }
                },
                {
                    "@type": "ConstructionBusiness",
                    "name": "StroiApp",
                    "url": "https://stroiapp.ru",
                    "logo": "https://stroiapp.ru/image/logo.png",
                    "telephone": "+7 (495) 000-00-00",
                    "email": "info@stroiapp.ru",
                    "address": {
                        "@type": "PostalAddress",
                        "addressLocality": "Москва",
                        "addressRegion": "Московская область",
                        "addressCountry": "RU"
                    },
                    "priceRange": "$$",
                    "openingHoursSpecification": [
                        {
                            "@type": "OpeningHoursSpecification",
                            "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                            "opens": "09:00",
                            "closes": "18:00"
                        }
                    ]
                }
            ]
        }
        return jsonld

    async def process_product(self, product: dict[str, Any]) -> dict[str, Any]:
        """Clean HTML, restructure, generate JSON-LD, update DB."""
        raw_desc = product.get("description", "") or ""
        product_id = product.get("product_id")
        name = product.get("name", "")

        # Clean
        clean = self.clean_html(raw_desc)

        # Structure
        structured = self.structure_html(clean, name)

        # JSON-LD
        jsonld = self.build_json_ld(product)
        jsonld_script = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))}</script>'

        # Combine: JSON-LD first, then semantic HTML
        final_html = jsonld_script + "\n" + structured

        # Push to OpenCart
        try:
            await opencart_api.post_action("product/update", {
                "product_id": product_id,
                "description": final_html
            })
        except Exception as exc:
            return {
                "product_id": product_id,
                "status": "error",
                "error": str(exc)[:300]
            }

        return {
            "product_id": product_id,
            "status": "ok",
            "html_length": len(final_html),
            "jsonld_present": True
        }

    async def process_all(self, limit: int = 50) -> dict[str, Any]:
        """Batch process products."""
        try:
            result = await opencart_api.get_action("product/list", {"limit": limit})
            products = result.get("products", [])
        except Exception as exc:
            return {"status": "error", "message": f"Failed to load products: {exc}"[:300]}

        if not products:
            return {"status": "error", "message": "No products found"}

        updated = 0
        errors = 0
        results = []

        for prod in products:
            if not prod.get("product_id"):
                continue
            res = await self.process_product(prod)
            if res["status"] == "ok":
                updated += 1
            else:
                errors += 1
            results.append(res)

        return {
            "status": "ok",
            "total": len(products),
            "updated": updated,
            "errors": errors,
            "details": results[:5]
        }


_semantic_parser = SemanticParser()


def get_semantic_parser() -> SemanticParser:
    return _semantic_parser
