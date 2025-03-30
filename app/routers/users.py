from app import services
from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response

from app.services import get_user_by_token
from app.token import create_access_token, verify_access_token
from app.models import User
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/auth/yandex")
async def yandex_auth(token: str, db: Session = Depends(get_db)):
    """
    Получаем информацию о пользователе через Яндекс токен
    и создаем пользователя в БД
    """
    user = await services.create_user_from_yandex(token, db)

    return {"username": user.username, "email": user.email}


@router.post("/token/refresh")
async def refresh_token(response: Response, token: str = Cookie(None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Token is required")

    user = await get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_token = create_access_token({"sub": user.id})
    response.set_cookie(key="token", value=new_token, httponly=True)

    return {"access_token": new_token}
