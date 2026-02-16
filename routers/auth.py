# auth.py — التحقق من التوكن والـ authentication
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from .users_common import verify_user_jwt_token, create_response, engine

router = APIRouter()
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """يستخرج التوكن من Authorization: Bearer <token> ويفحصه ويرجع الـ payload (user_id, role, ...)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = credentials.credentials
    try:
        payload = verify_user_jwt_token(token)
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/verify")
def verify_token(payload: dict = Depends(get_current_user)):
    """
    يتحقق من صلاحية التوكن.
    يتوقع: Authorization: Bearer <token>
    يرجع: success, message, user_id, role, name
    """
    user_id = payload.get("user_id")
    name = None
    if user_id:
        with engine.connect() as connection:
            row = connection.execute(
                text("SELECT name FROM public.users WHERE id = :user_id"),
                {"user_id": user_id},
            ).fetchone()
            if row:
                name = row[0]
    return create_response(
        True,
        "Token is valid",
        {
            "user_id": user_id,
            "role": payload.get("role"),
            "created_at": payload.get("created_at"),
            "name": name,
        },
        status_code=200,
    )
