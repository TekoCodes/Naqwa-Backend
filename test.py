# import requests

# # Base URL - change this to your server URL
# BASE_URL = "http://127.0.0.1:8000"
# # BASE_URL = "http://51.68.21.151:8000"

# # Register endpoint test
# def test_register():
#     """Test register endpoint with all required fields"""
#     url = f"{BASE_URL}/api/v1/register"
    
#     params = {
#         "name": "Ahmed Mohamed",
#         "phone_number": "01123456789",
#         "password": "password123",
#         "parent_number": "01098765432",
#         "birth_date": "2005-05-15",
#         "governorate": "Cairo",
#         "grade": "third secondary",
#         "section": "A",
#         "subscription_plan": "premium"  # Optional
#     }
    
#     print("Testing Register Endpoint...")
#     print(f"URL: {url}")
#     print(f"Params: {params}")
#     print("-" * 50)
    
#     try:
#         # Use data instead of params for form-urlencoded data
#         response = requests.post(url, params=params)
#         print(f"Status Code: {response.status_code}")
#         print(f"Response: {response.json()}")
#         print("-" * 50)
        
#         if response.status_code == 200:
#             result = response.json()
#             if result.get("success"):
#                 print("✓ Registration successful!")
#             else:
#                 print(f"✗ Registration failed: {result.get('message')}")
#         else:
#             print(f"✗ Request failed with status code: {response.status_code}")
            
#     except Exception as e:
#         print(f"✗ Error occurred: {str(e)}")

# # Test register with missing required fields
# def test_register_missing_fields():
#     """Test register endpoint with missing required fields"""
#     url = f"{BASE_URL}/api/v1/register"
    
#     params = {
#         "name": "Ahmed Mohamed",
#         "phone_number": "01123456789",
#         # Missing: password, parent_number, birth_date, governorate, grade, section
#     }
    
#     print("\nTesting Register Endpoint (Missing Required Fields)...")
#     print(f"URL: {url}")
#     print(f"Params: {params}")
#     print("-" * 50)
    
#     try:
#         # Use data instead of params for form-urlencoded data
#         response = requests.post(url, params=params)
#         print(f"Status Code: {response.status_code}")
#         print(f"Response: {response.json()}")
#         print("-" * 50)
#     except Exception as e:
#         print(f"✗ Error occurred: {str(e)}")

# # Test register with invalid phone number
# def test_register_invalid_phone():
#     """Test register endpoint with invalid phone number"""
#     url = f"{BASE_URL}/api/v1/register"
    
#     params = {
#         "name": "Ahmed Mohamed",
#         "phone_number": "12345678900",  # Invalid: not 11 digits
#         "password": "password123",
#         "parent_number": "01098765432",
#         "birth_date": "2005-05-15",
#         "governorate": "Cairo",
#         "grade": "10",
#         "section": "A"
#     }
    
#     print("\nTesting Register Endpoint (Invalid Phone Number)...")
#     print(f"URL: {url}")
#     print(f"Params: {params}")
#     print("-" * 50)
    
#     try:
#         # Use data instead of params for form-urlencoded data
#         response = requests.post(url, params=params)
#         print(f"Status Code: {response.status_code}")
#         print(f"Response: {response.json()}")
#         print("-" * 50)
#     except Exception as e:
#         print(f"✗ Error occurred: {str(e)}")

# # Test register with invalid birth date format
# def test_register_invalid_birth_date():
#     """Test register endpoint with invalid birth date format"""
#     url = f"{BASE_URL}/api/v1/register"
    
#     params = {
#         "name": "Ahmed Mohamed",
#         "phone_number": "01123456789",
#         "password": "password123",
#         "parent_number": "01098765432",
#         "birth_date": "15-05-2005",  # Invalid format (should be YYYY-MM-DD)
#         "governorate": "Cairo",
#         "grade": "10",
#         "section": "A"
#     }
    
#     print("\nTesting Register Endpoint (Invalid Birth Date Format)...")
#     print(f"URL: {url}")
#     print(f"Params: {params}")
#     print("-" * 50)
    
#     try:
#         # Use data instead of params for form-urlencoded data
#         response = requests.post(url, params=params)
#         print(f"Status Code: {response.status_code}")
#         print(f"Response: {response.json()}")
#         print("-" * 50)
#     except Exception as e:
#         print(f"✗ Error occurred: {str(e)}")

# if __name__ == "__main__":
#     # Run all tests
#     test_register()
# #     test_register_missing_fields()
# #     test_register_invalid_phone()
# #     test_register_invalid_birth_date()


# from sqlalchemy import create_engine, text

# db_user = "postgres"
# db_password = "x4IQEBxzpSwDSUIcYxqNfsuEY40jzdrTP5AMKWiDppbAY4kevp0KeL3odvWHqhfE"
# db_host = "37.60.236.213"
# db_port = "5432"
# db_name = "naqwa"

# database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# engine = create_engine(database_url)

# with engine.connect() as conn:
#     conn.execute(text("DROP EXTENSION IF EXISTS pgcrypto CASCADE;"))
#     conn.commit()

# print("pgcrypto extension and all dependent functions have been removed.")

from sqlalchemy import create_engine, text

db_user = "postgres"
db_password = "x4IQEBxzpSwDSUIcYxqNfsuEY40jzdrTP5AMKWiDppbAY4kevp0KeL3odvWHqhfE"
db_host = "37.60.236.213"
db_port = "5432"
db_name = "naqwa"

database_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(database_url)

drop_all_tables_sql = """
DO $$
DECLARE
    r RECORD;
BEGIN
    -- حذف كل التابلز في schema public
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;
"""

with engine.connect() as conn:
    conn.execute(text(drop_all_tables_sql))
    conn.commit()

print("All tables have been dropped successfully.")
