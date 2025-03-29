import os
import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from dotenv import load_dotenv
from app.database import Base, engine

# Загрузка переменных окружения
load_dotenv()

# Константы из .env
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Инициализация FastAPI
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Асинхронная инициализация БД
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Инициализация БД при старте
@app.on_event("startup")
async def startup():
    await init_db()

# Страница с кнопкой авторизации
@app.get("/login")
async def login(request: Request):
    auth_url = f"https://oauth.yandex.ru/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    return templates.TemplateResponse("login.html", {"request": request, "auth_url": auth_url})

# Коллбек от Яндекса
@app.get("/auth/yandex/callback")
async def auth_yandex_callback(code: str):
    token_url = "https://oauth.yandex.ru/token"

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        })

    if response.status_code == 200:
        data = await response.json()  # Добавили await
        return {"access_token": data.get("access_token")}

    raise HTTPException(status_code=400, detail="Failed to get token")
