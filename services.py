import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, VacationRequest, Department


load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Создаём engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # проверяет соединение перед использованием
)

# Сессии
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# --- CRUD / сервисы ---

def get_user_by_login(login: str):
    session = SessionLocal()
    try:
        return session.query(User).filter(User.login == login).first()
    finally:
        session.close()

def get_user_requests(user_id: str):
    session = SessionLocal()
    try:
        return session.query(VacationRequest)\
                      .filter(VacationRequest.user_id == user_id)\
                      .order_by(VacationRequest.created_at.desc())\
                      .all()
    finally:
        session.close()

def get_all_requests():
    session = SessionLocal()
    try:
        return session.query(VacationRequest)\
                      .order_by(VacationRequest.created_at.desc())\
                      .all()
    finally:
        session.close()

def get_departments_dict():
    session = SessionLocal()
    try:
        departments = session.query(Department).all()
        return {d.id: d for d in departments}
    finally:
        session.close()

def get_user_by_id(user_id: str):
    session = SessionLocal()
    try:
        return session.query(User).filter(User.id == user_id).first()
    finally:
        session.close()