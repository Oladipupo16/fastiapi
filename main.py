from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models
from database import engine, get_db
from auth import hash_password, verify_password, create_access_token
from auth import hash_password, verify_password, create_access_token, get_current_user_id

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class TaskCreate(BaseModel):
    title: str
    description: str
    completed: bool = False

class TaskUpdate(BaseModel):
    title: str = None
    description: str = None
    completed: bool = None
    
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

# ✅ Get all tasks
@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return db.query(models.Task).filter(models.Task.user_id == current_user_id).all()

# ✅ Get one task
@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# ✅ Create a task
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    db_task = models.Task(**task.dict(), user_id=current_user_id)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# ✅ Update a task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id, models.Task.user_id == current_user_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.title is not None:
        db_task.title = task.title
    if task.description is not None:
        db_task.description = task.description
    if task.completed is not None:
        db_task.completed = task.completed
    db.commit()
    db.refresh(db_task)
    return db_task

# ✅ Delete a task
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return
@app.post("/auth/signup", status_code=201)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # check if email already used
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created!", "user_id": new_user.id}
@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"user_id": db_user.id})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db), current_user_id: int = Depends(get_current_user_id)):
    return db.query(models.Task).all()