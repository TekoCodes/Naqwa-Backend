# create_tables.py
# Script to create database tables (users and otp_codes)

from sqlalchemy import create_engine, text
import logging

# Logging configuration
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Database connection
# postgres://TekoCodes:IQdi4eepCgtBKiBj7KVy8BYjq8SIgqweV1BMdkFMWuEfxpTlIODtcY6zc3MA5c6F@164.68.97.131:5432/academytest
db_user = "TekoCodes"
db_password = "IQdi4eepCgtBKiBj7KVy8BYjq8SIgqweV1BMdkFMWuEfxpTlIODtcY6zc3MA5c6F"
db_host = "164.68.97.131"
db_port = "5432"
db_name = "academytest"

# Use postgresql:// instead of postgresql+psycopg2:// for compatibility
database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(database_url)


def create_users_table():
    """Create users table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.users (
                    id SERIAL PRIMARY KEY,
                    first_name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create index on email for faster lookups
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON public.users(email)
            """))
            
        logging.info("Users table created or already exists")
        print("Users table created or already exists")
        return True
    except Exception as e:
        logging.error(f"Error creating users table: {e}")
        print(f"Error creating users table: {e}")
        return False


def create_otp_codes_table():
    """Create OTP codes table if it doesn't exist"""
    try:
        with engine.begin() as connection:
            # Create table if not exists
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS public.otp_codes (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    code VARCHAR(6) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used BOOLEAN DEFAULT FALSE
                )
            """))
            
            # Create indexes if not exist
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_otp_codes_email 
                ON public.otp_codes(email)
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_otp_codes_expires_at 
                ON public.otp_codes(expires_at)
            """))
            
        logging.info("OTP codes table created or already exists")
        print("OTP codes table created or already exists")
        return True
    except Exception as e:
        logging.error(f"Error creating OTP codes table: {e}")
        print(f"Error creating OTP codes table: {e}")
        return False


def create_all_tables():
    """Create all database tables"""
    print("Starting database tables creation...")
    users_success = create_users_table()
    otp_success = create_otp_codes_table()
    
    if users_success and otp_success:
        print("All tables created successfully!")
        return True
    else:
        print("Some tables failed to create. Check logs for details.")
        return False


if __name__ == "__main__":
    create_all_tables()

