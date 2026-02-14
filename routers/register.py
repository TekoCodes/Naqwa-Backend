# register.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from datetime import datetime
import logging
from .users_common import engine, validate_phone_number, validate_governorate, create_user_jwt_token, create_response

router = APIRouter()

@router.post("/register")
def add_user(
    name: str = None,
    phone_number: str = None,
    password: str = None,
    parent_number: str = None,
    birth_date: str = None,
    governorate: str = None,
    grade: str = None,
    section: str = None,
    account_status: str = "active",
    points: int = 0,
    early_access: bool = False,
    subscription_plan: str = None,
):
    try:
        # Validate required fields - collect all missing fields
        missing_fields = []
        if not name:
            missing_fields.append("name")
        if not phone_number:
            missing_fields.append("phone_number")
        if not password:
            missing_fields.append("password")
        if not parent_number:
            missing_fields.append("parent_number")
        if not birth_date:
            missing_fields.append("birth_date")
        if not governorate:
            missing_fields.append("governorate")
        if not grade or grade not in ["third secondary"]:
            missing_fields.append("grade")
        if not section:
            missing_fields.append("section")
        
        # Return error with all missing fields
        if missing_fields:
            fields_str = ", ".join(missing_fields)
            return create_response(False, f"The following fields are required: {fields_str}", status_code=400)
        
        # Validate and normalize phone_number
        try:
            phone_number = validate_phone_number(phone_number, "phone_number")
        except ValueError as e:
            return create_response(False, str(e), status_code=400)
        
        # Validate and normalize parent_number
        try:
            parent_number = validate_phone_number(parent_number, "parent_number")
        except ValueError as e:
            return create_response(False, str(e), status_code=400)
        
        # Validate governorate
        try:
            governorate = validate_governorate(governorate, "governorate")
        except ValueError as e:
            return create_response(False, str(e), status_code=400)
        
        # Parse birth_date
        try:
            birth_date_parsed = datetime.strptime(birth_date, "%Y-%m-%d").date()
        except ValueError:
            return create_response(False, "Invalid birth_date format. Use YYYY-MM-DD format.", status_code=400)
        
        logging.info(f"Add user attempt: {phone_number}")
        
        # Check if phone_number already exists in database
        with engine.connect() as connection:
            existing_user = connection.execute(
                text("SELECT * FROM public.users WHERE phone_number = :phone_number"),
                {"phone_number": phone_number}
            ).mappings().fetchone()
            
            if existing_user:
                logging.warning(f"Registration failed: phone number already exists: {phone_number}")
                return create_response(False, "Phone number already registered. Please use a different phone number or login.", status_code=409)
            
            # Create user account and session
            created_at = datetime.utcnow()
            with engine.begin() as conn:
                # Insert user and get the user_id
                result = conn.execute(
                    text("""
                        INSERT INTO public.users (
                            name, phone_number, parent_number, birth_date, governorate,
                            password, grade, section, account_status, points,
                            early_access, subscription_plan, created_at
                        )
                        VALUES (
                            :name, :phone_number, :parent_number, :birth_date, :governorate,
                            :password, :grade, :section, :account_status, :points,
                            :early_access, :subscription_plan, :created_at
                        )
                        RETURNING id
                    """),
                    {
                        "name": name,
                        "phone_number": phone_number,
                        "parent_number": parent_number,
                        "birth_date": birth_date_parsed,
                        "governorate": governorate,
                        "password": password,
                        "grade": grade,
                        "section": section,
                        "account_status": account_status,
                        "points": points,
                        "early_access": early_access,
                        "subscription_plan": subscription_plan,
                        "created_at": created_at
                    }
                )
                user_id = result.scalar()
                
                # Create JWT token with user_id, created_at, and role
                token = create_user_jwt_token(user_id, created_at, "user")
                
                # Insert session into sessions table
                conn.execute(
                    text("""
                        INSERT INTO public.sessions (user_id, session, created_at, active)
                        VALUES (:user_id, :session, :created_at, :active)
                    """),
                    {
                        "user_id": user_id,
                        "session": token,
                        "created_at": created_at,
                        "active": True
                    }
                )
        logging.info(f"User added successfully: {phone_number}, user_id: {user_id}")
        return create_response(True, "User registered successfully", {
            "token": token,
            "token_type": "bearer"
        }, status_code=200)
    
    except Exception as e:
        logging.error(f"Error in register: {str(e)}")
        return create_response(False, f"An error occurred: {str(e)}", status_code=500)

