import requests


# params = {"email": "ramez@example.com", "password": "hashedpassword123"}
# params = {"email": "2694stormi@tiffincrane.com"}
params = {
        "first_name": "ramez",
        "last_name": "ashraf",
        "email": "2694stormi@tiffincrane.com",
        "password_hash": "hashedpassword123",
        }

# response = requests.post('http://127.0.0.1:8000/api/v1/users/login',params=params)
# response = requests.post('http://127.0.0.1:8000/api/v1/otp/send-otp',params=params)
response = requests.post('http://51.68.21.151:8000/api/v1/otp/send-otp',params=params)
response = requests.post('http://51.68.21.151:8000/api/v1/users/register',params=params)
print(response.json())