from fastapi import APIRouter, Body

from app.models.automation import BannerRequest
from app.services.site_doctor import site_doctor

router = APIRouter(prefix="/sitedoctor", tags=["sitedoctor"])


@router.get("/status")
def site_status():
    return {"status": "ok", "service": "sitedoctor"}


@router.post("/updateStyles")
def update_styles(css: str = Body(..., media_type="text/plain")):
    return site_doctor.update_styles(css)


@router.post("/updateLayout")
def update_layout(layout: dict):
    return site_doctor.update_layout(layout)


@router.post("/updateBanner")
def update_banner(payload: BannerRequest):
    return site_doctor.update_banner(payload)
