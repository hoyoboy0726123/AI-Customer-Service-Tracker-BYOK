from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    
    # 關聯案件
    issues = relationship("Issue", back_populates="agent")

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100))
    product_id = Column(String(50))
    summary = Column(Text)
    raw_content = Column(Text)
    status = Column(String(20), default="待處理")  # 待處理, 處理中, 已解決
    priority = Column(String(20), default="中")    # 高, 中, 低
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.now)
    
    # 外鍵與關聯
    agent_id = Column(Integer, ForeignKey("users.id"))
    agent = relationship("User", back_populates="issues")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "product_id": self.product_id,
            "summary": self.summary,
            "status": self.status,
            "priority": self.priority,
            "agent": self.agent.name if self.agent else "未指派",
            "due_date": self.due_date.strftime("%Y-%m-%d") if self.due_date else "無",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }
