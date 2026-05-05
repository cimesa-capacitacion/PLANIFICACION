from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
import datetime

import models
import schemas
from database import SessionLocal, engine

# Create the database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Kanban Board API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Helper function to log activity
def log_activity(db: Session, action: str, user: str, task_title: str):
    user_name = user if user else "Usuario Desconocido"
    log = models.ActivityLog(action=action, user=user_name, task_title=task_title)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

# REST API ENDPOINTS

@app.get("/api/tasks/", response_model=List[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = db.query(models.Task).filter(models.Task.is_deleted == False).offset(skip).limit(limit).all()
    return tasks

@app.get("/api/tasks/deleted", response_model=List[schemas.Task])
def read_deleted_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = db.query(models.Task).filter(models.Task.is_deleted == True).offset(skip).limit(limit).all()
    return tasks

@app.post("/api/tasks/", response_model=schemas.Task)
async def create_task(task: schemas.TaskCreate, actor: Optional[str] = None, db: Session = Depends(get_db)):
    db_task = models.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    acting_user = actor or task.user
    log = log_activity(db, "Creada", acting_user, db_task.title)
    
    # Broadcast changes
    await manager.broadcast(json.dumps({"type": "TASK_ADDED", "task": schemas.Task.model_validate(db_task).model_dump()}))
    await manager.broadcast(json.dumps({"type": "HISTORY_UPDATED"}))
    
    return db_task

@app.put("/api/tasks/{task_id}", response_model=schemas.Task)
async def update_task(task_id: int, task: schemas.TaskUpdate, actor: Optional[str] = None, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check what changed to log appropriately
    update_data = task.model_dump(exclude_unset=True)
    
    action = "Editada"
    if "bucket" in update_data and update_data["bucket"] != db_task.bucket:
        action = f"Movida a {update_data['bucket']}"
    if "is_deleted" in update_data:
        if update_data["is_deleted"] == False and db_task.is_deleted == True:
            action = "Restaurada de papelera"
        elif update_data["is_deleted"] == True and db_task.is_deleted == False:
            action = "Enviada a papelera"
            
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    
    acting_user = actor or db_task.user
    log_activity(db, action, acting_user, db_task.title)
    
    # Broadcast change
    await manager.broadcast(json.dumps({"type": "TASK_UPDATED", "task": schemas.Task.model_validate(db_task).model_dump()}))
    await manager.broadcast(json.dumps({"type": "HISTORY_UPDATED"}))
    
    return db_task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, actor: Optional[str] = None, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Soft delete
    db_task.is_deleted = True
    db.commit()
    
    acting_user = actor or db_task.user
    log_activity(db, "Enviada a papelera", acting_user, db_task.title)
    
    # Broadcast change
    await manager.broadcast(json.dumps({"type": "TASK_DELETED", "task_id": task_id}))
    await manager.broadcast(json.dumps({"type": "HISTORY_UPDATED"}))
    
    return {"message": "Task moved to trash successfully"}

@app.get("/api/history/", response_model=List[schemas.ActivityLog])
def read_history(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(models.ActivityLog).order_by(models.ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs

# Static files and frontend hosting
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))
