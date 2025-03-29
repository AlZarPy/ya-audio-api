from fastapi import FastAPI
from app.database import engine
from app import models

# Инициализация базы данных
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

