# login.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import logging
from .users_common import engine, create_user_jwt_token, validate_phone_number, create_response

router = APIRouter()

@router.post("/login")
def login(phone_number: str = None, email: str = None, password: str = None):
    try:
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

            if password != user["password"]:
                logging.warning(f"Login failed: incorrect password for {identifier}")
                return create_response(False, "Invalid credentials", status_code=401)

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

