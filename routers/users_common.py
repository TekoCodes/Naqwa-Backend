# users_common.py
# Shared configuration and utilities for user endpoints
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from fastapi import HTTPException
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
db_user = "postgres"
db_password = "x4IQEBxzpSwDSUIcYxqNfsuEY40jzdrTP5AMKWiDppbAY4kevp0KeL3odvWHqhfE"
db_host = "37.60.236.213"
db_port = "5432"
db_name = "naqwa"
database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(database_url)

# JWT settings
SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Function to create JWT
def create_jwt_token(email):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logging.info(f"JWT token created for user: {email}")
    return token

# Function to create JWT token with user_id, created_at, and role
def create_user_jwt_token(user_id: int, created_at: datetime, role: str = "user"):
    """
    Create JWT token containing user_id, created_at, and role
    
    Args:
        user_id: User ID
        created_at: Account creation timestamp
        role: User role (default: "user")
    
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "created_at": created_at.isoformat(),
        "role": role,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logging.info(f"JWT token created for user_id: {user_id}, role: {role}")
    return token

# Function to create standardized response with status code
def create_response(success: bool, message: str, data: dict = None, status_code: int = 200):
    """
    Create standardized API response format with status code.
    
    Args:
        success: Boolean indicating if the operation was successful
        message: Response message
        data: Optional additional data to include in response
        status_code: HTTP status code (default: 200)
    
    Returns:
        Response object with status code and JSON body
    """
    from fastapi import Response
    from fastapi.responses import JSONResponse
    
    response_body = {
        "success": success,
        "message": message
    }
    if data:
        response_body.update(data)
    
    return JSONResponse(content=response_body, status_code=status_code)

# List of all Egyptian governorates
EGYPTIAN_GOVERNORATES = [
    "القاهرة",
    "الجيزة",
    "الإسكندرية",
    "الدقهلية",
    "البحر الأحمر",
    "البحيرة",
    "الفيوم",
    "الغربية",
    "الإسماعيلية",
    "المنوفية",
    "المنيا",
    "القليوبية",
    "الوادي الجديد",
    "السويس",
    "أسوان",
    "أسيوط",
    "بني سويف",
    "بورسعيد",
    "دمياط",
    "الشرقية",
    "جنوب سيناء",
    "كفر الشيخ",
    "مطروح",
    "الأقصر",
    "قنا",
    "شمال سيناء",
    "سوهاج",
    # English names as well (if used)
    "Cairo",
    "Giza",
    "Alexandria",
    "Dakahlia",
    "Red Sea",
    "Beheira",
    "Faiyum",
    "Gharbia",
    "Ismailia",
    "Monufia",
    "Minya",
    "Qalyubia",
    "New Valley",
    "Suez",
    "Aswan",
    "Asyut",
    "Beni Suef",
    "Port Said",
    "Damietta",
    "Sharqia",
    "South Sinai",
    "Kafr El Sheikh",
    "Matruh",
    "Luxor",
    "Qena",
    "North Sinai",
    "Sohag"
]

def validate_governorate(governorate: str, field_name: str = "governorate") -> str:
    """
    Validate that governorate is a valid Egyptian governorate.
    
    Args:
        governorate: Governorate name to validate
        field_name: Name of the field for error messages
    
    Returns:
        Validated governorate name
        
    Raises:
        ValueError: If governorate is not in the list of valid Egyptian governorates
    """
    if not governorate:
        raise ValueError(f"{field_name} is required")
    
    if not isinstance(governorate, str):
        governorate = str(governorate)
    
    # Normalize: strip whitespace
    governorate_normalized = governorate.strip()
    
    # Check if governorate is in the valid list
    # First try exact match
    if governorate_normalized in EGYPTIAN_GOVERNORATES:
        return governorate_normalized
    
    # If not found, try case-insensitive match (for English names)
    for valid_gov in EGYPTIAN_GOVERNORATES:
        if governorate_normalized.lower() == valid_gov.lower():
            return valid_gov  # Return the canonical form from the list
    
    # If still not found, raise error
    raise ValueError(f"{field_name} must be a valid Egyptian governorate")

# Function to validate and normalize phone number
def validate_phone_number(phone_number: str, field_name: str = "phone_number") -> str:
    """
    Validate and normalize phone number.
    - Remove spaces from start and end
    - Must be exactly 11 digits
    - Must start with 011, 010, 012, or 015
    
    Returns normalized phone number or raises ValueError with message
    """
    if not phone_number:
        raise ValueError(f"{field_name} is required")
    
    # Remove spaces from start and end
    phone_number = phone_number.strip()
    
    # Remove all spaces (in case there are spaces in the middle)
    phone_number = phone_number.replace(" ", "")
    
    # Check if it's exactly 11 digits
    if not phone_number.isdigit():
        raise ValueError(f"{field_name} must contain only digits")
    
    if len(phone_number) != 11:
        raise ValueError(f"{field_name} must be exactly 11 digits")
    
    # Check if it starts with valid prefix
    valid_prefixes = ["011", "010", "012", "015"]
    if not any(phone_number.startswith(prefix) for prefix in valid_prefixes):
        raise ValueError(f"{field_name} must start with 011, 010, 012, or 015")
    
    return phone_number

