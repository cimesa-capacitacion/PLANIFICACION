from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    bucket: str
    priority: str
    user: str
    month_filter: str
    due_date: Optional[str] = None
    reference_links: Optional[str] = None

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
    reference_links: Optional[str] = None
    is_deleted: Optional[bool] = None

class Task(TaskBase):
    id: int
    is_deleted: bool

    class Config:
        from_attributes = True

class ActivityLogBase(BaseModel):
    action: str
    user: str
    task_title: str

class ActivityLogCreate(ActivityLogBase):
    pass

class ActivityLog(ActivityLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
