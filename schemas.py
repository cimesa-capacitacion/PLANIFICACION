from pydantic import BaseModel
from typing import Optional

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    bucket: str
    priority: str
    user: str
    month_filter: str
    due_date: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    bucket: Optional[str] = None
    priority: Optional[str] = None
    user: Optional[str] = None
    month_filter: Optional[str] = None
    due_date: Optional[str] = None

class Task(TaskBase):
    id: int

    class Config:
        from_attributes = True
