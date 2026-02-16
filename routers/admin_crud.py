# admin_crud.py — CRUD للأدمن (Grades, Subjects, Chapters, Sources, Users)
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import text
from typing import Optional

from .users_common import verify_user_jwt_token, create_response, engine


def _serialize_row(r) -> dict:
    """تحويل صف (mapping) إلى dict مع تحويل التواريخ."""
    d = dict(r)
    for k, v in list(d.items()):
        if isinstance(v, (date, datetime)):
            d[k] = v.isoformat()
    return d


def _serialize_rows(rows) -> list:
    return [_serialize_row(r) for r in rows]

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """يتحقق من التوكن ويرجع payload فقط إذا كان role = admin."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        payload = verify_user_jwt_token(credentials.credentials)
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin only")
        return payload
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# --- Grades ---
class GradeCreate(BaseModel):
    name: str

class GradeUpdate(BaseModel):
    name: str

@router.get("/grades")
def list_grades(payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT g.id, g.name, g.created_at, g.created_by, a.name as created_by_name
                FROM public.grades g
                LEFT JOIN public.admins a ON g.created_by = a.id
                ORDER BY g.id
            """)
        ).mappings().fetchall()
    return create_response(True, "OK", {"data": _serialize_rows(rows)}, status_code=200)

@router.post("/grades")
def create_grade(body: GradeCreate, payload: dict = Depends(get_current_admin)):
    admin_id = payload.get("user_id")
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO public.grades (name, created_by) VALUES (:name, :created_by)
            """),
            {"name": body.name.strip(), "created_by": admin_id}
        )
        row = conn.execute(text("SELECT id, name, created_at, created_by FROM public.grades WHERE name = :name"), {"name": body.name.strip()}).mappings().fetchone()
    return create_response(True, "تم الإنشاء", {"data": _serialize_row(row)}, status_code=201)

@router.put("/grades/{grade_id}")
def update_grade(grade_id: int, body: GradeUpdate, payload: dict = Depends(get_current_admin)):
    with engine.begin() as conn:
        r = conn.execute(
            text("UPDATE public.grades SET name = :name WHERE id = :id"),
            {"name": body.name.strip(), "id": grade_id}
        )
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="Grade not found")
        row = conn.execute(text("SELECT id, name, created_at, created_by FROM public.grades WHERE id = :id"), {"id": grade_id}).mappings().fetchone()
    return create_response(True, "تم التحديث", {"data": _serialize_row(row)}, status_code=200)

@router.delete("/grades/{grade_id}")
def delete_grade(grade_id: int, payload: dict = Depends(get_current_admin)):
    with engine.begin() as conn:
        r = conn.execute(text("DELETE FROM public.grades WHERE id = :id"), {"id": grade_id})
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="Grade not found")
    return create_response(True, "تم الحذف", None, status_code=200)


# --- Subjects ---
class SubjectCreate(BaseModel):
    name: str
    grade: Optional[str] = None
    stream: Optional[str] = None

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    stream: Optional[str] = None

@router.get("/subjects")
def list_subjects(payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT s.id, s.name, s.grade, s.stream, s.created_at, s.created_by, a.name as created_by_name
            FROM public.subjects s LEFT JOIN public.admins a ON s.created_by = a.id ORDER BY s.id
        """)).mappings().fetchall()
    return create_response(True, "OK", {"data": _serialize_rows(rows)}, status_code=200)

@router.post("/subjects")
def create_subject(body: SubjectCreate, payload: dict = Depends(get_current_admin)):
    admin_id = payload.get("user_id")
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO public.subjects (name, grade, stream, created_by) VALUES (:name, :grade, :stream, :created_by)"),
            {"name": body.name or "", "grade": body.grade or "", "stream": body.stream or "", "created_by": admin_id}
        )
        row = conn.execute(text("""
            SELECT s.id, s.name, s.grade, s.stream, s.created_at, s.created_by, a.name as created_by_name
            FROM public.subjects s LEFT JOIN public.admins a ON s.created_by = a.id ORDER BY s.id DESC LIMIT 1
        """)).mappings().fetchone()
    return create_response(True, "تم الإنشاء", {"data": _serialize_row(row)}, status_code=201)

@router.put("/subjects/{subject_id}")
def update_subject(subject_id: int, body: SubjectUpdate, payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        cur = conn.execute(text("SELECT id, name, grade, stream FROM public.subjects WHERE id = :id"), {"id": subject_id}).mappings().fetchone()
        if not cur:
            raise HTTPException(status_code=404, detail="Subject not found")
        cur = dict(cur)
    name = body.name if body.name is not None else cur["name"]
    grade = body.grade if body.grade is not None else cur["grade"]
    stream = body.stream if body.stream is not None else cur["stream"]
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE public.subjects SET name = :name, grade = :grade, stream = :stream WHERE id = :id"),
            {"name": name, "grade": grade or "", "stream": stream or "", "id": subject_id}
        )
        row = conn.execute(text("""
            SELECT s.id, s.name, s.grade, s.stream, s.created_at, s.created_by, a.name as created_by_name
            FROM public.subjects s LEFT JOIN public.admins a ON s.created_by = a.id WHERE s.id = :id
        """), {"id": subject_id}).mappings().fetchone()
    return create_response(True, "تم التحديث", {"data": _serialize_row(row)}, status_code=200)

@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, payload: dict = Depends(get_current_admin)):
    with engine.begin() as conn:
        r = conn.execute(text("DELETE FROM public.subjects WHERE id = :id"), {"id": subject_id})
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="Subject not found")
    return create_response(True, "تم الحذف", None, status_code=200)


# --- Chapters ---
class ChapterCreate(BaseModel):
    subject_id: int
    name: str
    order_index: Optional[int] = None

class ChapterUpdate(BaseModel):
    subject_id: Optional[int] = None
    name: Optional[str] = None
    order_index: Optional[int] = None

@router.get("/chapters")
def list_chapters(payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT c.id, c.subject_id, c.name, c.order_index, c.created_at, c.created_by,
                s.name as subject_name, a.name as created_by_name
                FROM public.chapters c
                LEFT JOIN public.subjects s ON c.subject_id = s.id
                LEFT JOIN public.admins a ON c.created_by = a.id
                ORDER BY c.id
            """)
        ).mappings().fetchall()
    return create_response(True, "OK", {"data": _serialize_rows(rows)}, status_code=200)

@router.post("/chapters")
def create_chapter(body: ChapterCreate, payload: dict = Depends(get_current_admin)):
    admin_id = payload.get("user_id")
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO public.chapters (subject_id, name, order_index, created_by) VALUES (:subject_id, :name, :order_index, :created_by)"),
            {"subject_id": body.subject_id, "name": body.name or "", "order_index": body.order_index, "created_by": admin_id}
        )
        row = conn.execute(text("""
            SELECT c.id, c.subject_id, c.name, c.order_index, c.created_at, c.created_by, a.name as created_by_name
            FROM public.chapters c LEFT JOIN public.admins a ON c.created_by = a.id ORDER BY c.id DESC LIMIT 1
        """)).mappings().fetchone()
    return create_response(True, "تم الإنشاء", {"data": _serialize_row(row)}, status_code=201)

@router.put("/chapters/{chapter_id}")
def update_chapter(chapter_id: int, body: ChapterUpdate, payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        cur = conn.execute(text("SELECT id, subject_id, name, order_index FROM public.chapters WHERE id = :id"), {"id": chapter_id}).mappings().fetchone()
        if not cur:
            raise HTTPException(status_code=404, detail="Chapter not found")
        cur = dict(cur)
    subject_id = body.subject_id if body.subject_id is not None else cur["subject_id"]
    name = body.name if body.name is not None else cur["name"]
    order_index = body.order_index if body.order_index is not None else cur["order_index"]
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE public.chapters SET subject_id = :subject_id, name = :name, order_index = :order_index WHERE id = :id"),
            {"subject_id": subject_id, "name": name or "", "order_index": order_index, "id": chapter_id}
        )
        row = conn.execute(text("""
            SELECT c.id, c.subject_id, c.name, c.order_index, c.created_at, c.created_by, a.name as created_by_name
            FROM public.chapters c LEFT JOIN public.admins a ON c.created_by = a.id WHERE c.id = :id
        """), {"id": chapter_id}).mappings().fetchone()
    return create_response(True, "تم التحديث", {"data": _serialize_row(row)}, status_code=200)

@router.delete("/chapters/{chapter_id}")
def delete_chapter(chapter_id: int, payload: dict = Depends(get_current_admin)):
    with engine.begin() as conn:
        r = conn.execute(text("DELETE FROM public.chapters WHERE id = :id"), {"id": chapter_id})
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="Chapter not found")
    return create_response(True, "تم الحذف", None, status_code=200)


# --- Sources ---
class SourceCreate(BaseModel):
    name: str
    source_type: str
    year: Optional[int] = None
    grade: Optional[str] = None
    author_name: Optional[str] = None
    published_at: Optional[str] = None
    notes: Optional[str] = None
    created_by: int  # user id حسب الجدول الحالي

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    year: Optional[int] = None
    grade: Optional[str] = None
    author_name: Optional[str] = None
    published_at: Optional[str] = None
    notes: Optional[str] = None

@router.get("/sources")
def list_sources(payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT s.id, s.name, s.source_type, s.year, s.grade, s.author_name, s.published_at,
                s.created_by, s.notes, s.created_at, u.name as created_by_name
                FROM public.sources s LEFT JOIN public.users u ON s.created_by = u.id ORDER BY s.id
            """)
        ).mappings().fetchall()
    return create_response(True, "OK", {"data": _serialize_rows(rows)}, status_code=200)

@router.post("/sources")
def create_source(body: SourceCreate, payload: dict = Depends(get_current_admin)):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO public.sources (name, source_type, year, grade, author_name, published_at, created_by, notes)
                VALUES (:name, :source_type, :year, :grade, :author_name, :published_at::date, :created_by, :notes)
            """),
            {
                "name": body.name, "source_type": body.source_type,
                "year": body.year, "grade": body.grade or "", "author_name": body.author_name or "",
                "published_at": body.published_at or None, "created_by": body.created_by, "notes": body.notes or ""
            }
        )
        row = conn.execute(text("""
            SELECT s.id, s.name, s.source_type, s.year, s.grade, s.author_name, s.published_at, s.created_by, s.notes, s.created_at, u.name as created_by_name
            FROM public.sources s LEFT JOIN public.users u ON s.created_by = u.id ORDER BY s.id DESC LIMIT 1
        """)).mappings().fetchone()
    return create_response(True, "تم الإنشاء", {"data": _serialize_row(row)}, status_code=201)

@router.put("/sources/{source_id}")
def update_source(source_id: int, body: SourceUpdate, payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        cur = conn.execute(text("SELECT * FROM public.sources WHERE id = :id"), {"id": source_id}).mappings().fetchone()
        if not cur:
            raise HTTPException(status_code=404, detail="Source not found")
        cur = dict(cur)
    def v(key, val):
        return val if val is not None else cur.get(key)
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE public.sources SET name = :name, source_type = :source_type, year = :year, grade = :grade,
                author_name = :author_name, published_at = :published_at::date, notes = :notes WHERE id = :id
            """),
            {
                "name": v("name", body.name), "source_type": v("source_type", body.source_type),
                "year": v("year", body.year), "grade": v("grade", body.grade) or "", "author_name": v("author_name", body.author_name) or "",
                "published_at": v("published_at", body.published_at), "notes": v("notes", body.notes) or "", "id": source_id
            }
        )
        row = conn.execute(text("""
            SELECT s.id, s.name, s.source_type, s.year, s.grade, s.author_name, s.published_at, s.created_by, s.notes, s.created_at, u.name as created_by_name
            FROM public.sources s LEFT JOIN public.users u ON s.created_by = u.id WHERE s.id = :id
        """), {"id": source_id}).mappings().fetchone()
    return create_response(True, "تم التحديث", {"data": _serialize_row(row)}, status_code=200)

@router.delete("/sources/{source_id}")
def delete_source(source_id: int, payload: dict = Depends(get_current_admin)):
    with engine.begin() as conn:
        r = conn.execute(text("DELETE FROM public.sources WHERE id = :id"), {"id": source_id})
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="Source not found")
    return create_response(True, "تم الحذف", None, status_code=200)


# --- Users (الطلبة) ---
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    parent_number: Optional[str] = None
    birth_date: Optional[str] = None
    governorate: Optional[str] = None
    grade: Optional[str] = None
    section: Optional[str] = None
    lang_type: Optional[str] = None
    account_status: Optional[str] = None
    points: Optional[int] = None
    subscription_plan: Optional[str] = None
    role: Optional[str] = None

@router.get("/users")
def list_users(payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT id, name, phone_number, parent_number, birth_date, governorate, grade, section, lang_type,
                account_status, points, early_access, subscription_plan, role, created_at
                FROM public.users ORDER BY id
            """)
        ).mappings().fetchall()
    return create_response(True, "OK", {"data": _serialize_rows(rows)}, status_code=200)

@router.get("/users/{user_id}")
def get_user(user_id: int, payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id, name, phone_number, parent_number, birth_date, governorate, grade, section, lang_type, account_status, points, early_access, subscription_plan, role, created_at FROM public.users WHERE id = :id"),
            {"id": user_id}
        ).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return create_response(True, "OK", {"data": _serialize_row(row)}, status_code=200)

@router.put("/users/{user_id}")
def update_user(user_id: int, body: UserUpdate, payload: dict = Depends(get_current_admin)):
    with engine.connect() as conn:
        cur = conn.execute(text("SELECT * FROM public.users WHERE id = :id"), {"id": user_id}).mappings().fetchone()
        if not cur:
            raise HTTPException(status_code=404, detail="User not found")
        cur = dict(cur)
    def v(key):
        val = getattr(body, key, None)
        return val if val is not None else cur.get(key)
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE public.users SET name = :name, phone_number = :phone_number, parent_number = :parent_number,
                birth_date = :birth_date::date, governorate = :governorate, grade = :grade, section = :section,
                lang_type = :lang_type, account_status = :account_status, points = :points, subscription_plan = :subscription_plan, role = :role
                WHERE id = :id
            """),
            {
                "name": v("name"), "phone_number": v("phone_number"), "parent_number": v("parent_number") or "",
                "birth_date": v("birth_date"), "governorate": v("governorate") or "", "grade": v("grade") or "",
                "section": v("section") or "", "lang_type": v("lang_type") or "", "account_status": v("account_status") or "active",
                "points": v("points") if v("points") is not None else 0, "subscription_plan": v("subscription_plan") or "free",
                "role": v("role") or "student", "id": user_id
            }
        )
        row = conn.execute(text("SELECT id, name, phone_number, grade, account_status, role, created_at FROM public.users WHERE id = :id"), {"id": user_id}).mappings().fetchone()
    return create_response(True, "تم التحديث", {"data": _serialize_row(row)}, status_code=200)

@router.delete("/users/{user_id}")
def delete_user(user_id: int, payload: dict = Depends(get_current_admin)):
    with engine.begin() as conn:
        r = conn.execute(text("DELETE FROM public.users WHERE id = :id"), {"id": user_id})
        if r.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
    return create_response(True, "تم الحذف", None, status_code=200)
