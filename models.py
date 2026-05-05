from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from database import Base
import datetime

class Task(Base):
    __tablename__ = "tasks_v3"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    bucket = Column(String, index=True)
    priority = Column(String)
    user = Column(String)
    month_filter = Column(String)
    due_date = Column(String, nullable=True)
    reference_links = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String) # 'Creada', 'Editada', 'Movida', 'Eliminada', 'Restaurada'
    user = Column(String) # Quien lo hizo
    task_title = Column(String) # Titulo de la tarea afectada
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
