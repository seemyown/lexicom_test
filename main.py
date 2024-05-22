from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from redis.asyncio import Redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Функция для инициализации компонентов приложения"""
    app.state.redis = Redis.from_url(
        f"redis://{os.getenv('REDIS_HOST')}/0",
        decode_responses=True
    )
    yield


app = FastAPI(
    title="Lexicom Test",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return RedirectResponse("/docs")


@app.get("/check_data")
async def check_data(phone: str = Query(min_length=11, pattern="^[8,7][0-9]{10}$")):
    """
    Проверка данных по номеру телефона
    :param phone: str - номер телефона
    :return: dict: Адрес по номеру телефона
    :raises HTTPException: 404 - Нет данных по номеру телефона
    """
    address = await app.state.redis.get(phone)
    if address is not None:
        return {"address": address}
    raise HTTPException(status_code=404, detail="No address found")


class WriteDataRequest(BaseModel):
    """Класс для добавления/обновления адреса по номеру телефона"""
    phone: str = Field(min_length=11, pattern="^[8,7][0-9]{10}$")
    address: str


@app.post("/write_data")
async def write_data(body: WriteDataRequest):
    """
    Добавление/обновление адреса по номеру телефона
    :param body: WriteDataRequest - данные для добавления/обновления
    :return: dict: Адрес по номеру телефона
    :raises HTTPException: 500 - Ошибка при записи/обновлении адреса
    """
    try:
        await app.state.redis.set(body.phone, body.address)
        return {"success": True}
    except Exception as e:
        err_name = type(e).__name__
        raise HTTPException(status_code=500, detail={
            "error": err_name,
            "message": str(e)
        })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
