import httpx
from fastapi import HTTPException
from app.models import User
from app.schemas import UserCreate
from app.database import SessionLocal
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения

YANDEX_OAUTH_URL = "https://login.yandex.ru/oauth/token"


async def get_yandex_user_info(token: str):
    """
    Функция для получения информации о пользователе через OAuth 2.0.
    """
    headers = {"Authorization": f"OAuth {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.get("https://login.yandex.ru/info", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Yandex token")

    user_info = response.json()
    return user_info


async def create_user_from_yandex(token: str, db: Session):
    """
    Создание пользователя из данных Яндекса.
    """
    user_info = await get_yandex_user_info(token)

    db_user = db.query(User).filter(User.email == user_info["email"]).first()

    if not db_user:
        db_user = User(
            username=user_info["login"],
            email=user_info["email"],
            yandex_token=token
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

    return db_user
