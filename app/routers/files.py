from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models import AudioFile, User
from app.database import get_db
from app.token import verify_access_token
import os

UPLOAD_DIR = "app/uploads"
ALLOWED_EXTENSIONS = {"mp3", "wav"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

router = APIRouter()

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@router.post("/upload/")
async def upload_file(file: UploadFile = File(...), token: str = Depends(verify_access_token),
                      db: Session = Depends(get_db)):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Invalid file type. Only mp3 and wav allowed.")

    if file.content_type not in ["audio/mpeg", "audio/wav"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files allowed.")

    file_size = len(await file.read())  # Получаем размер файла для проверки
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds limit (10 MB).")

    # Перемещаем курсор в начало после чтения
    await file.seek(0)

    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1 MB за раз
            f.write(chunk)

    # Сохраняем информацию о файле в базе данных
    user_id = token["sub"]
    db_file = AudioFile(filename=file.filename, file_path=file_location, owner_id=user_id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return {"filename": file.filename, "file_path": file_location}


@router.get("/files/")
async def get_files(token: str, db: Session = Depends(get_db)):
    payload = verify_access_token(token)
    user_id = payload["sub"]
    files = db.query(AudioFile).filter(AudioFile.owner_id == user_id).all()

    if not files:
        raise HTTPException(status_code=404, detail="No files found")

    return {"files": [{"filename": file.filename, "file_path": file.file_path} for file in files]}
