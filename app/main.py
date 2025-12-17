from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import engine, Base
from app.api import users, admin, auth
from app.config import settings
import os

# Создаем таблицы при старте
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VPN Billing System",
    description="Система биллинга и управления клиентами VPN-сервиса",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(auth.router)

# Статические файлы и шаблоны
if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("templates"):
    os.makedirs("templates")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    """Админ-панель"""
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/health")
def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "ok"}

