# forgot_password.py
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from datetime import datetime
import logging
from .users_common import engine, validate_phone_number, create_response, hash_password

router = APIRouter()


class ForgotPasswordBody(BaseModel):
    phone_number: str | None = None
    email: str | None = None
    otp: str
    new_password: str


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordBody):
    try:
        phone_number = body.phone_number
        email = body.email
        otp = body.otp
        new_password = body.new_password
        if not phone_number and not email:
            return create_response(False, "Either phone_number or email must be provided", status_code=400)
        
        if not otp:
            return create_response(False, "OTP is required", status_code=400)

        if not new_password:
            return create_response(False, "New password is required", status_code=400)
        
        # Validate and normalize phone_number if provided
        if phone_number:
            try:
                phone_number = validate_phone_number(phone_number, "phone_number")
            except ValueError as e:
                return create_response(False, str(e), status_code=400)
        
        logging.info(f"Forgot password attempt for phone: {phone_number} or email: {email}")
        
        # Check if user exists in database
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
                logging.warning(f"Forgot password failed: user not found for {identifier}")
                return create_response(False, "User not found. Please check your phone number or email address.", status_code=404)
            
            # Validate OTP if email is provided
            if email:
                otp_record = connection.execute(
                    text("""
                        SELECT * FROM public.otp_codes 
                        WHERE email = :email 
                        AND code = :otp 
                        AND used = FALSE
                        AND expires_at > :current_time
                    """),
                    {
                        "email": email,
                        "otp": otp,
                        "current_time": datetime.utcnow()
                    }
                ).mappings().fetchone()
                
                if not otp_record:
                    logging.warning(f"Invalid or expired OTP for forgot password: {email}")
                    return create_response(False, "Invalid or expired OTP code. Please request a new OTP.", status_code=400)
        
        # OTP is valid, hash and update password
        new_password_hashed = hash_password(new_password)
        with engine.begin() as connection:  # commit automatically
            # Mark OTP as used if email was provided
            if email:
                connection.execute(
                    text("""
                        UPDATE public.otp_codes 
                        SET used = TRUE 
                        WHERE email = :email 
                        AND code = :otp
                    """),
                    {
                        "email": email,
                        "otp": otp
                    }
                )
            
            # Update user password (مشفر)
            if phone_number:
                connection.execute(
                    text("""
                        UPDATE public.users 
                        SET password = :new_password
                        WHERE phone_number = :phone_number
                    """),
                    {
                        "phone_number": phone_number,
                        "new_password": new_password_hashed
                    }
                )
            else:
                connection.execute(
                    text("""
                        UPDATE public.users 
                        SET password = :new_password
                        WHERE email = :email
                    """),
                    {
                        "email": email,
                        "new_password": new_password_hashed
                    }
                )
        logging.info(f"Password updated successfully for {identifier}")
        return create_response(True, "Password updated successfully", status_code=200)
    
    except Exception as e:
        logging.error(f"Error in forgot_password: {str(e)}")
        return create_response(False, f"An error occurred: {str(e)}", status_code=500)

