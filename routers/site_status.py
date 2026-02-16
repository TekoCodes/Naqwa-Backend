# site_status.py — حالة الموقع (وضع تحت الإنشاء للطلبة)
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import text

from .users_common import create_response, engine, verify_user_jwt_token

router = APIRouter()
security = HTTPBearer(auto_error=False)


def _get_under_construction():
    """قراءة قيمة under_construction من الجدول."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT value FROM public.site_settings WHERE key = 'under_construction'")
        ).fetchone()
    if row:
        return (row[0] or "").strip().lower() in ("1", "true", "yes")
    return True  # افتراضي: تحت الإنشاء


@router.get("/site-status")
def get_site_status():
    """عام — لا يتطلب توكن. يستخدمه صفحة الطالب لمعرفة هل تعرض «تحت الإنشاء»."""
    under_construction = _get_under_construction()
    return create_response(True, "OK", {"under_construction": under_construction}, status_code=200)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        payload = verify_user_jwt_token(credentials.credentials)
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


class SiteStatusBody(BaseModel):
    under_construction: bool


@router.get("/admin/site-status")
def admin_get_site_status(payload: dict = Depends(get_current_admin)):
    """أدمن فقط — قراءة إعداد وضع تحت الإنشاء."""
    under_construction = _get_under_construction()
    return create_response(True, "OK", {"data": {"under_construction": under_construction}}, status_code=200)


@router.put("/admin/site-status")
def admin_set_site_status(body: SiteStatusBody, payload: dict = Depends(get_current_admin)):
    """أدمن فقط — تفعيل/إيقاف وضع تحت الإنشاء للطلبة."""
    value = "true" if body.under_construction else "false"
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO public.site_settings (key, value) VALUES ('under_construction', :v)
                ON CONFLICT (key) DO UPDATE SET value = :v
            """),
            {"v": value}
        )
    return create_response(True, "تم التحديث", {"data": {"under_construction": body.under_construction}}, status_code=200)
