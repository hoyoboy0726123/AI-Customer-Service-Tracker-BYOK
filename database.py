from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User

# 使用 SQLite 資料庫
DATABASE_URL = "sqlite:///./issues.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # 初始化預設客服人員
    db = SessionLocal()
    if db.query(User).count() == 0:
        default_users = [
            User(name="客服小明", email="ming@company.com"),
            User(name="客服小華", email="hua@company.com"),
            User(name="主管大壯", email="strong@company.com"),
        ]
        db.add_all(default_users)
        db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
