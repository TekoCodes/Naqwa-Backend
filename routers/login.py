# login.py
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from datetime import datetime
import logging
from .users_common import engine, create_user_jwt_token, validate_phone_number, create_response, verify_password, hash_password

router = APIRouter()


class LoginBody(BaseModel):
    phone_number: str | None = None
    email: str | None = None
    password: str


@router.post("/login")
def login(body: LoginBody):
    try:
        phone_number = body.phone_number
        email = body.email
        password = body.password
        if not phone_number and not email:
            return create_response(False, "Either phone_number or email must be provided", status_code=400)
        
        if not password:
            return create_response(False, "Password is required", status_code=400)

        # Validate and normalize phone_number if provided
        if phone_number:
            try:
                phone_number = validate_phone_number(phone_number, "phone_number")
            except ValueError as e:
                return create_response(False, str(e), status_code=400)
        
        logging.info(f"Login attempt for phone: {phone_number} or email: {email}")

        with engine.connect() as connection:
            if phone_number:
                user = connection.execute(
                    text("SELECT * FROM public.users WHERE phone_number = :phone_number"),
                    {"phone_number": phone_number}
                ).mappings().fetchone()
                identifier = phone_number
            else:
                user = connection.execute(
                    text("SELECT * FROM public.users WHERE email = :email"),
                    {"email": email}
                ).mappings().fetchone()
                identifier = email

            if not user:
                logging.warning(f"Login failed: user not found for {identifier}")
                return create_response(False, "Invalid credentials", status_code=401)

            stored_password = user["password"] or ""
            if not verify_password(password, stored_password):
                logging.warning(f"Login failed: incorrect password for {identifier}")
                return create_response(False, "Invalid credentials", status_code=401)

            # ترقية كلمة مرور قديمة (نص عادي) إلى هاش عند أول دخول ناجح
            if not (stored_password.startswith("$2") or stored_password.startswith("$b$")):
                with engine.begin() as upgrade_conn:
                    if phone_number:
                        upgrade_conn.execute(
                            text("UPDATE public.users SET password = :hashed WHERE id = :user_id"),
                            {"hashed": hash_password(password), "user_id": user["id"]}
                        )
                    else:
                        upgrade_conn.execute(
                            text("UPDATE public.users SET password = :hashed WHERE id = :user_id"),
                            {"hashed": hash_password(password), "user_id": user["id"]}
                        )

            # Get user_id and created_at from user
            user_id = user["id"]
            created_at = user.get("created_at")
            
            # If created_at is None, use current time (shouldn't happen but safety check)
            if not created_at:
                created_at = datetime.utcnow()
            
            # Create JWT token with user_id, created_at, and role (same as register)
            token = create_user_jwt_token(user_id, created_at, "user")
            
            # Insert session into sessions table
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO public.sessions (user_id, session, created_at, active)
                        VALUES (:user_id, :session, :created_at, :active)
                    """),
                    {
                        "user_id": user_id,
                        "session": token,
                        "created_at": datetime.utcnow(),
                        "active": True
                    }
                )
            
            logging.info(f"Login successful for {identifier}, user_id: {user_id}")

            return create_response(True, "Login successful", {
                "token": token,
                "token_type": "bearer"
            }, status_code=200)
    
    except Exception as e:
        logging.error(f"Error in login: {str(e)}")
        return create_response(False, f"An error occurred: {str(e)}", status_code=500)

