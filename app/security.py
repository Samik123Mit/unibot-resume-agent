import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET = os.getenv("JWT_SECRET", "development-only-change-me")
ALGORITHM = "HS256"
# PBKDF2 avoids bcrypt's 72-byte input ceiling and is broadly supported on Python 3.14.
pwd = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str: return pwd.hash(password)
def verify_password(password: str, encoded: str) -> bool: return pwd.verify(password, encoded)
def create_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")))}, SECRET, algorithm=ALGORITHM)
def decode_token(token: str) -> int:
    try: return int(jwt.decode(token, SECRET, algorithms=[ALGORITHM])["sub"])
    except (JWTError, KeyError, ValueError): raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
