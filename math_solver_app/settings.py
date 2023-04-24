from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    SESSION_SECRET_KEY: str = 'secretkey'
    CORS_ORIGINS: str = '*'

    class Config:
        env_file = 'math_solver_app/.env'
        env_file_encoding = 'utf-8'


@lru_cache
def get_settings(**kwargs):
    return Settings(**kwargs)
