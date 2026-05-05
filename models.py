from sqlalchemy import Column, Integer, String, Text
from database import Base

class Task(Base):
    __tablename__ = "tasks_v2"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    bucket = Column(String, index=True)
    priority = Column(String)
    user = Column(String)
    month_filter = Column(String)
    due_date = Column(String, nullable=True)
