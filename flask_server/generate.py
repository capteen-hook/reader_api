import jwt
import datetime
import os
from dotenv import load_dotenv

print(load_dotenv(dotenv_path='.env', override=True))
# Secret key for signing the token
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key") 
# Generate a token with a long expiration date
def generate_long_lasting_token():
    payload = {
        "user_id": 123,  # Example payload data
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=3650)  # 10 years expiration
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

print("Generating token: " + SECRET_KEY)
# Generate and print the token
token = generate_long_lasting_token()
print("Long-lasting token:", token)