import jwt
import sqlite3
import os

from fastapi import APIRouter
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta

from math_solver_app.settings import get_settings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "../database/users.db")


settings = get_settings()

router = APIRouter()

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/register/")
def register(username: str, password: str):
    hashed_password = get_password_hash(password)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user (username, password) VALUES (?,?)", (username, hashed_password))
    conn.commit()
    cursor.execute("SELECT id FROM user WHERE username=?", (username,))
    user_id = cursor.fetchone()[0]

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires
    )

    cursor.execute("INSERT INTO session (user_id, token) VALUES (?,?)", (user_id, access_token))
    conn.commit()

    return {"access_token": access_token, "token_type": "bearer"}
