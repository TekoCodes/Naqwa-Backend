import requests


# params = {"email": "ramez@example.com", "password": "hashedpassword123"}
params = {"email": "2694stormi@tiffincrane.com"}
# response = requests.post('http://127.0.0.1:8000/api/v1/users/login',params=params)
# response = requests.post('http://127.0.0.1:8000/api/v1/otp/send-otp',params=params)
response = requests.post('http://51.68.21.151:8079/api/v1/otp/send-otp',params=params)
print(response.json())