import jwt
import sqlite3
import os

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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


def get_user(username: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM user WHERE username=?", (username,))
    user = cursor.fetchone()
    if user:
        return {"id": user[0], "username": user[1], "hashed_password": user[2]}


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user


@router.post("/register/")
async def register(username: str, password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password should be at least 8 characters long")

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

    return {"message": "Пользователь зарегистрирован", "access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload["sub"]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT token FROM session WHERE user_id=?", (user_id,))
        user_token = cursor.fetchone()
        if not user_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if token != user_token[0]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login/")
async def login(username: str, password: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM user WHERE username=?", (username,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(password, user[1]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user_id = user[0]
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires
    )
    cursor.execute("INSERT INTO session (user_id, token) VALUES (?,?)", (user_id, access_token))
    conn.commit()
    return {"access_token": access_token, "token_type": "bearer"}


# TODO: Добавить доступ только авторизованному пользователю
@router.post("/solve_linear_system/")
async def solve_linear_system(A: List[List[float]], b: List[float]):
    """
        Решение системы линейных уравнений с помощью метода Гаусса.
        Уравнение, которое решается, представлено в виде матричного уравнения Ax = b,
        где A - матрица коэффициентов, x - вектор неизвестных, b - вектор правых частей.

        Пример заполнения данных для уравнения
        {
          "A": [[1, 2, -1],
                [2, 1, -2],
                [-3, 1, 1]],
          "b":  [3, 3, -6]
        }

        Результат решения:
        {
          "solution": [    3,    0.9999999999999998,    1.9999999999999996  ]
        }
        """
    if len(A) != len(b):
        raise HTTPException(status_code=400, detail="The dimensions of the matrix and vector do not match.")
    n = len(A)
    for i in range(n):
        max_row = i
        for j in range(i+1, n):
            if abs(A[j][i]) > abs(A[max_row][i]):
                max_row = j

        A[i], A[max_row] = A[max_row], A[i]
        b[i], b[max_row] = b[max_row], b[i]

        for j in range(i+1, n):
            factor = A[j][i] / A[i][i]
            for k in range(i, n):
                A[j][k] -= factor * A[i][k]
            b[j] -= factor * b[i]

    x = [0] * n
    for i in range(n-1, -1, -1):
        x[i] = b[i] / A[i][i]
        for j in range(i):
            b[j] -= A[j][i] * x[i]

    return {"solution": x}
