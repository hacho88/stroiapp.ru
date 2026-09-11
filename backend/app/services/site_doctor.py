from app.models.automation import BannerRequest


class SiteDoctor:
    def update_styles(self, css: str) -> dict[str, str | int]:
        return {"status": "accepted", "bytes": len(css)}

    def update_layout(self, layout: dict) -> dict[str, str | dict]:
        return {"status": "accepted", "layout": layout}

    def update_banner(self, request: BannerRequest) -> dict[str, str | None]:
        return {"status": "published", "title": request.title, "subtitle": request.subtitle, "url": request.url}


site_doctor = SiteDoctor()
