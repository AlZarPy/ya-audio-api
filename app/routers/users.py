from app import services
from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException
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
async def refresh_token(token: str, db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    # Дополнительно проверяем активность пользователя
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    return {"access_token": create_access_token(data={"sub": user.id})}
