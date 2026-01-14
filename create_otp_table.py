# create_otp_table.py
# Script to create OTP codes table in the database

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
database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(database_url)


def create_otp_table_if_not_exists():
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
            
        logging.info("OTP table created or already exists")
        print("OTP table created or already exists")
        return True
    except Exception as e:
        logging.error(f"Error creating OTP table: {e}")
        print(f"Error creating OTP table: {e}")
        return False


if __name__ == "__main__":
    create_otp_table_if_not_exists()

