# otp.py
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from email.mime.text import MIMEText
import logging
import smtplib
import random
import jwt


def send_verification_email(receiver_email: str, verification_code: str):
    sender = "info@mezoscan.online"
    smtp_host = "127.0.0.1"
    smtp_port = 25
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Dermalyze | Email Verification Code"
    msg["From"] = f"Dermalyze <{sender}>"
    msg["To"] = receiver_email

    # HTML Email Body
    html_body = f"""
    <html>
      <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,Helvetica,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td align="center">
              <table width="500" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;padding:30px;">
                
                <tr>
                  <td align="center" style="font-size:26px;font-weight:bold;color:#111;">
                    Dermalyze
                  </td>
                </tr>

                <tr><td height="20"></td></tr>

                <tr>
                  <td style="font-size:16px;color:#333;text-align:center;">
                    Your email verification code is
                  </td>
                </tr>

                <tr><td height="20"></td></tr>

                <tr>
                  <td align="center">
                    <div style="
                      font-size:36px;
                      font-weight:bold;
                      letter-spacing:6px;
                      color:#ffffff;
                      background:#111;
                      padding:15px 25px;
                      border-radius:6px;
                      display:inline-block;
                    ">
                      {verification_code}
                    </div>
                  </td>
                </tr>

                <tr><td height="20"></td></tr>

                <tr>
                  <td style="font-size:14px;color:#666;text-align:center;">
                    This code will expire in <b>5 minutes</b>.<br>
                    If you didn't request this, please ignore this email.
                  </td>
                </tr>

                <tr><td height="30"></td></tr>

                <tr>
                  <td style="font-size:12px;color:#999;text-align:center;">
                    © 2026 Dermalyze. All rights reserved.
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        # if email authentication is enabled
        # server.login(sender, "PASSWORD")
        server.sendmail(sender, receiver_email, msg.as_string())
        logging.info(f"Verification email sent successfully to {receiver_email}")
        return True
    except Exception as e:
        logging.error(f"Error sending email to {receiver_email}: {e}")
        return False
    finally:
        server.quit()
# -----------------------------
# Logging configuration
# -----------------------------
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------
# Database connection
# -----------------------------
# postgres://TekoCodes:IQdi4eepCgtBKiBj7KVy8BYjq8SIgqweV1BMdkFMWuEfxpTlIODtcY6zc3MA5c6F@164.68.97.131:5432/academytest
db_user = "TekoCodes"
db_password = "IQdi4eepCgtBKiBj7KVy8BYjq8SIgqweV1BMdkFMWuEfxpTlIODtcY6zc3MA5c6F"
db_host = "164.68.97.131"
db_port = "5432"
db_name = "ramez"
database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(database_url)


# OTP settings
OTP_EXPIRE_MINUTES = 5

# JWT settings
SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# APIRouter for OTP
router = APIRouter()

# Function to create JWT
def create_jwt_token(email):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logging.info(f"JWT token created for user: {email}")
    return token

# Send OTP endpoint
@router.post("/send-otp")
def send_otp(email: str):
    logging.info(f"Send OTP attempt for email: {email}")
    
    # Generate 6-digit OTP code
    code = str(random.randint(100000, 999999))
    
    # Calculate expiration time (5 minutes from now)
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    
    try:
        # Save OTP code to database
        with engine.begin() as connection:
            # Mark old OTP codes as used for this email
            connection.execute(
                text("UPDATE public.otp_codes SET used = TRUE WHERE email = :email AND used = FALSE"),
                {"email": email}
            )
            
            # Insert new OTP code
            connection.execute(
                text("""
                    INSERT INTO public.otp_codes (email, code, expires_at, created_at, used)
                    VALUES (:email, :code, :expires_at, :created_at, FALSE)
                """),
                {
                    "email": email,
                    "code": code,
                    "expires_at": expires_at,
                    "created_at": datetime.utcnow()
                }
            )
        
        # Send verification email
        code_status = send_verification_email(email, code)
        
        if code_status:
            logging.info(f"OTP code sent successfully to email: {email}")
            return {
                "success": True,
                "message": "OTP code sent to email"
            }
        else:
            logging.error(f"Error sending OTP code to email: {email}")
            raise HTTPException(status_code=500, detail="Error sending OTP code to email")
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing OTP request for email {email}: {e}")
        raise HTTPException(status_code=500, detail="Error processing OTP request")


