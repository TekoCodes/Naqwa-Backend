# student_profile.py — جلب وتحديث بيانات الطالب
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from datetime import datetime
import logging
from .auth import get_current_user
from .users_common import (
    engine,
    create_response,
    validate_phone_number,
    validate_governorate,
)

router = APIRouter(prefix="/student", tags=["student"])

VALID_GRADES = ["S1", "S2", "S3"]
VALID_SECTIONS = ["علمي رياضه", "علمي علوم", "ادبي"]
VALID_LANG_TYPES = ["عربي", "لغات"]


class UpdateProfileBody(BaseModel):
    name: str | None = None
    phone_number: str | None = None
    parent_number: str | None = None
    birth_date: str | None = None
    governorate: str | None = None
    grade: str | None = None
    section: str | None = None
    lang_type: str | None = None


@router.get("/profile")
def get_student_profile(payload: dict = Depends(get_current_user)):
    """جلب بيانات الطالب المسجّل دخوله."""
    user_id = payload.get("user_id")
    if not user_id:
        return create_response(False, "User not found", status_code=401)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT name, phone_number, parent_number, birth_date, governorate,
                           grade, section, lang_type
                    FROM public.users
                    WHERE id = :user_id
                """),
                {"user_id": user_id},
            ).mappings().fetchone()
            if not row:
                return create_response(False, "User not found", status_code=404)
            # Convert date to string if needed
            data = dict(row)
            if data.get("birth_date"):
                data["birth_date"] = data["birth_date"].strftime("%Y-%m-%d")
            return create_response(
                True,
                "Profile retrieved",
                {"profile": data},
                status_code=200,
            )
    except Exception as e:
        logging.error(f"Error fetching student profile: {e}")
        return create_response(False, str(e), status_code=500)


@router.patch("/profile")
def update_student_profile(body: UpdateProfileBody, payload: dict = Depends(get_current_user)):
    """تحديث بيانات الطالب."""
    user_id = payload.get("user_id")
    if not user_id:
        return create_response(False, "User not found", status_code=401)
    try:
        updates = {}
        params = {"user_id": user_id}

        if body.name is not None and body.name.strip():
            updates["name"] = body.name.strip()
        if body.phone_number is not None:
            try:
                updates["phone_number"] = validate_phone_number(body.phone_number, "phone_number")
            except ValueError as e:
                return create_response(False, str(e), status_code=400)
        if body.parent_number is not None:
            try:
                updates["parent_number"] = validate_phone_number(body.parent_number, "parent_number")
            except ValueError as e:
                return create_response(False, str(e), status_code=400)
        if body.birth_date is not None:
            try:
                datetime.strptime(body.birth_date, "%Y-%m-%d").date()
                updates["birth_date"] = body.birth_date
            except ValueError:
                return create_response(False, "Invalid birth_date format. Use YYYY-MM-DD.", status_code=400)
        if body.governorate is not None and body.governorate.strip():
            try:
                updates["governorate"] = validate_governorate(body.governorate, "governorate")
            except ValueError as e:
                return create_response(False, str(e), status_code=400)
        if body.grade is not None:
            if body.grade not in VALID_GRADES:
                return create_response(False, f"grade must be one of {VALID_GRADES}", status_code=400)
            updates["grade"] = body.grade
        if body.section is not None:
            if body.section not in VALID_SECTIONS:
                return create_response(False, f"section must be one of {VALID_SECTIONS}", status_code=400)
            updates["section"] = body.section
        if body.lang_type is not None:
            if body.lang_type not in VALID_LANG_TYPES:
                return create_response(False, f"lang_type must be one of {VALID_LANG_TYPES}", status_code=400)
            updates["lang_type"] = body.lang_type

        if not updates:
            return create_response(False, "No fields to update", status_code=400)

        # Check phone_number uniqueness if changing (exclude current user)
        if "phone_number" in updates:
            with engine.connect() as conn:
                existing = conn.execute(
                    text("SELECT id FROM public.users WHERE phone_number = :pn AND id != :uid"),
                    {"pn": updates["phone_number"], "uid": user_id},
                ).fetchone()
                if existing:
                    return create_response(False, "رقم التليفون مستخدم لحساب آخر", status_code=409)

        # Build dynamic UPDATE
        set_clauses = [f"{k} = :{k}" for k in updates]
        params.update(updates)
        sql = f"""
            UPDATE public.users
            SET {', '.join(set_clauses)}
            WHERE id = :user_id
        """
        with engine.begin() as conn:
            conn.execute(text(sql), params)
        logging.info(f"Student profile updated: user_id={user_id}")
        return create_response(True, "تم تحديث البيانات بنجاح", status_code=200)
    except Exception as e:
        logging.error(f"Error updating student profile: {e}")
        return create_response(False, str(e), status_code=500)
