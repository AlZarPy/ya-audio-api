import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
from app.token import create_access_token, verify_access_token
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные окружения

YANDEX_OAUTH_URL = "https://login.yandex.ru/oauth/token"


async def get_yandex_user_info(token: str):
    """
    Получение информации о пользователе через Yandex OAuth 2.0.
    """
    headers = {"Authorization": f"OAuth {token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://login.yandex.ru/info", headers=headers)
            response.raise_for_status()  # Проверяем статус ответа
            user_info = response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Ошибка запроса к Yandex API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный JSON-ответ от Yandex")

    return user_info


async def create_user_from_yandex(token: str, db: AsyncSession):
    user_info = await get_yandex_user_info(token)

    stmt = select(User).where(User.username == user_info['login'])
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    if existing_user:
        # Пользователь с таким username уже существует
        return existing_user

    # Создаем нового пользователя, если его еще нет
    db_user = User(
        username=user_info['login'],
        email=user_info["default_email"],
        yandex_token=token
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user

async def get_user_by_token(token: str | None, db: AsyncSession) -> User:
    if token is None:
        raise HTTPException(status_code=401, detail="Token not found")
    payload = verify_access_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    # Дополнительно проверяем активность пользователя
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return user