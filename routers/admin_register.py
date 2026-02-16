# admin_register.py
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from datetime import datetime
import logging
from .users_common import engine, validate_phone_number, create_user_jwt_token, create_response, hash_password, verify_password

router = APIRouter()


class AdminLoginBody(BaseModel):
    phone_number: str
    password: str


@router.post("/admin/login")
def admin_login(body: AdminLoginBody):
    """تسجيل دخول الأدمن — يتحقق من جدول admins ويرجع توكن برول admin."""
    try:
        phone_number = body.phone_number
        password = body.password
        if not phone_number or not password:
            return create_response(False, "Phone number and password are required", status_code=400)
        try:
            phone_number = validate_phone_number(phone_number, "phone_number")
        except ValueError as e:
            return create_response(False, str(e), status_code=400)

        with engine.connect() as connection:
            admin = connection.execute(
                text("SELECT * FROM public.admins WHERE phone_number = :phone_number"),
                {"phone_number": phone_number}
            ).mappings().fetchone()

            if not admin:
                return create_response(False, "Invalid credentials", status_code=401)
            if not verify_password(password, admin["password"] or ""):
                return create_response(False, "Invalid credentials", status_code=401)

            admin_id = admin["id"]
            created_at = admin.get("created_at") or datetime.utcnow()
            role = admin.get("role") or "admin"
            token = create_user_jwt_token(admin_id, created_at, role=role)

        return create_response(True, "Login successful", {"token": token, "token_type": "bearer"}, status_code=200)
    except Exception as e:
        logging.error(f"Error in admin_login: {str(e)}")
        return create_response(False, str(e), status_code=500)

# @router.post("/admin_register")
# def admin_register(
#     name: str = None,
#     phone_number: str = None,
#     password: str = None,
#     role: str = "admin",
# ):
#     try:
#         # Validate required fields
#         missing_fields = []
#         if not name:
#             missing_fields.append("name")
#         if not phone_number:
#             missing_fields.append("phone_number")
#         if not password:
#             missing_fields.append("password")

#         if not role:
#             missing_fields.append("role")
#         if missing_fields:
#             return create_response(False, f"The following fields are required: {', '.join(missing_fields)}", status_code=400)

#         # Validate and normalize phone_number
#         try:
#             phone_number = validate_phone_number(phone_number, "phone_number")
#         except ValueError as e:
#             return create_response(False, str(e), status_code=400)

#         password = hash_password(password)

#         # Check if phone_number already exists in admins table
#         with engine.connect() as connection:

#             existing_admin = connection.execute(
#                 text("SELECT * FROM public.admins WHERE phone_number = :phone_number"),
#                 {"phone_number": phone_number}
#             ).mappings().fetchone()
#             if existing_admin:
#                 return create_response(False, "Phone number already registered for admin.", status_code=409)

#             created_at = datetime.utcnow()
#             with engine.begin() as conn:
#                 result = conn.execute(
#                     text("""
#                         INSERT INTO public.admins (name, phone_number, password, role, created_at)
#                         VALUES (:name, :phone_number, :password, :role, :created_at)
#                         RETURNING id
#                     """),
#                     {
#                         "name": name,
#                         "phone_number": phone_number,
#                         "password": password,
#                         "role": role,
#                         "created_at": created_at
#                     }
#                 )
#                 admin_id = result.scalar()
#                 token = create_user_jwt_token(admin_id, created_at, role=role)

#         logging.info(f"Admin registered: {phone_number}, admin_id: {admin_id}")
#         return create_response(True, "Admin registered successfully", {
#             "token": token,
#             "token_type": "bearer"
#         }, status_code=200)

#     except Exception as e:
#         logging.error(f"Error in admin_register: {str(e)}")
#         return create_response(False, f"An error occurred: {str(e)}", status_code=500)
