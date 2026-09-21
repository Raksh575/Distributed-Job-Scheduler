import jwt
from app.core.config import settings
from app.core.security import create_access_token, decode_access_token

def test_jwt():
    print("Secret key:", settings.SECRET_KEY)
    print("Algorithm:", settings.ALGORITHM)
    token = create_access_token(subject="f2ee820a-b869-40a8-90db-f06a835d1387")
    print("Generated token:", token)
    
    try:
        payload = decode_access_token(token)
        print("Decoded payload:", payload)
        print("Success!")
    except Exception as e:
        print("Decode failed!")
        print(e)

if __name__ == "__main__":
    test_jwt()
