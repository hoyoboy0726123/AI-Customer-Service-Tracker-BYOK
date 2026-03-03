from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User
import os

def get_user_db_path(username: str):
    # 為每個使用者建立獨立的 .db 檔案
    return f"sqlite:///./user_{username}.db"

def init_user_db(username: str):
    db_path = get_user_db_path(username)
    engine = create_engine(db_path, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    # 為新使用者初始化預設客服人員
    Session = sessionmaker(bind=engine)
    db = Session()
    if db.query(User).count() == 0:
        default_users = [
            User(name="客服小明", email=f"ming_{username}@company.com"),
            User(name="客服小華", email=f"hua_{username}@company.com"),
            User(name="主管大壯", email=f"strong_{username}@company.com"),
        ]
        db.add_all(default_users)
        db.commit()
    db.close()
    return engine, Session
