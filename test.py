import requests


params = {"email": "ramez@example.com", "password": "hashedpassword123"}
response = requests.post('http://127.0.0.1:8000/api/v1/users/login',params=params)
print(response.json())