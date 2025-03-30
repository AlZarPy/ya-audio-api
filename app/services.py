import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import User
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
    """
    Создание пользователя в базе данных по данным из Yandex.
    """
    user_info = await get_yandex_user_info(token)

    stmt = select(User).where(User.email == user_info.get("email"))
    result = await db.execute(stmt)
    db_user = result.scalars().first()

    if not db_user:
        db_user = User(
            username=user_info.get("login", "unknown"),
            email=user_info.get("email", "unknown@noemail.com"),
            yandex_token=token
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

    return db_user
