# users.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import jwt
import logging

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


# JWT settings
SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# APIRouter for users
router = APIRouter()

# Function to create JWT
def create_jwt_token(email):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logging.info(f"JWT token created for user: {email}")
    return token

# Login endpoint
@router.post("/login")
def login(email: str, password: str):
    logging.info(f"Login attempt for email: {email}")

    with engine.connect() as connection:
        user = connection.execute(
            text("SELECT * FROM public.users WHERE email = :email"),
            {"email": email}
        ).mappings().fetchone()   

        if not user:
            logging.warning(f"Login failed: user not found for email {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if password != user["password_hash"]:
            logging.warning(f"Login failed: incorrect password for email {email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_jwt_token(email)
        logging.info(f"Login successful for email: {email}")

        return {
            "access_token": token,
            "token_type": "bearer"
        }

# # -----------------------------
# # Add new user endpoint
# # -----------------------------
# @router.post("/register")
# def add_user(first_name: str, last_name: str, email: str, password: str):
#     logging.info(f"Add user attempt: {email}")
#     with engine.begin() as connection:  # commit automatically
#         connection.execute(
#             text("""
#                 INSERT INTO public.users (first_name, last_name, email, password_hash, created_at)
#                 VALUES (:first_name, :last_name, :email, :password_hash, :created_at)
#             """),
#             {
#                 "first_name": first_name,
#                 "last_name": last_name,
#                 "email": email,
#                 "password_hash": password,
#                 "created_at": datetime.utcnow()
#             }
#         )
#     logging.info(f"User added successfully: {email}")
#     return {"message": "User added successfully"}
