from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from math_solver_app.routes import router
from math_solver_app.settings import get_settings
from math_solver_app.utils import setup_logger


import logging


logger = logging.getLogger(__name__)

app = FastAPI()
settings = get_settings()


@app.on_event("startup")
async def on_startup():

    app.include_router(router)
    setup_logger()
    logger.error(settings)

app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
