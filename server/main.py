"""
FastAPI сервер для Railway
Подключается к MongoDB
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.database import Database
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uvicorn

# Инициализация приложения
app = FastAPI(title="Web Clicker API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "clicker_db")

client = MongoClient(MONGODB_URL)
db: Database = client[DATABASE_NAME]


# Pydantic модели
class AccountCreate(BaseModel):
    name: str
    login: str
    password: str
    website: str
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    id: str
    name: str
    login: str
    website: str
    is_active: bool
    created_at: datetime


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    account_id: Optional[str] = None
    url: str
    actions: dict


class TaskResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    account_id: Optional[str]
    url: str
    actions: dict
    is_active: bool
    run_count: int
    created_at: datetime


# ========== ACCOUNTS ==========

@app.get("/api/accounts", response_model=List[AccountResponse])
def get_accounts(skip: int = 0, limit: int = 100):
    """Получить список аккаунтов"""
    accounts = list(db.accounts.find().skip(skip).limit(limit))
    return [format_account(acc) for acc in accounts]


@app.get("/api/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: str):
    """Получить аккаунт по ID"""
    account = db.accounts.find_one({"_id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return format_account(account)


@app.post("/api/accounts", response_model=AccountResponse)
def create_account(account: AccountCreate):
    """Создать новый аккаунт"""
    account_dict = account.dict()
    account_dict["is_active"] = True
    account_dict["created_at"] = datetime.utcnow()
    account_dict["updated_at"] = datetime.utcnow()
    
    result = db.accounts.insert_one(account_dict)
    account_dict["_id"] = result.inserted_id
    
    return format_account(account_dict)


@app.put("/api/accounts/{account_id}", response_model=AccountResponse)
def update_account(account_id: str, account: AccountCreate):
    """Обновить аккаунт"""
    account_dict = account.dict()
    account_dict["updated_at"] = datetime.utcnow()
    
    result = db.accounts.update_one(
        {"_id": account_id},
        {"$set": account_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    
    updated = db.accounts.find_one({"_id": account_id})
    return format_account(updated)


@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: str):
    """Удалить аккаунт"""
    result = db.accounts.delete_one({"_id": account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted"}


# ========== TASKS ==========

@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks(skip: int = 0, limit: int = 100):
    """Получить список задач"""
    tasks = list(db.tasks.find().skip(skip).limit(limit))
    return [format_task(task) for task in tasks]


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    """Получить задачу по ID"""
    task = db.tasks.find_one({"_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return format_task(task)


@app.post("/api/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate):
    """Создать новую задачу"""
    task_dict = task.dict()
    task_dict["is_active"] = True
    task_dict["run_count"] = 0
    task_dict["created_at"] = datetime.utcnow()
    task_dict["updated_at"] = datetime.utcnow()
    
    result = db.tasks.insert_one(task_dict)
    task_dict["_id"] = result.inserted_id
    
    return format_task(task_dict)


@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task: TaskCreate):
    """Обновить задачу"""
    task_dict = task.dict()
    task_dict["updated_at"] = datetime.utcnow()
    
    result = db.tasks.update_one(
        {"_id": task_id},
        {"$set": task_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated = db.tasks.find_one({"_id": task_id})
    return format_task(updated)


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Удалить задачу"""
    result = db.tasks.delete_one({"_id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}


# ========== HELPER FUNCTIONS ==========

def format_account(account: dict) -> dict:
    """Форматирование аккаунта для ответа"""
    return {
        "id": str(account["_id"]),
        "name": account["name"],
        "login": account["login"],
        "website": account["website"],
        "is_active": account.get("is_active", True),
        "created_at": account.get("created_at", datetime.utcnow())
    }


def format_task(task: dict) -> dict:
    """Форматирование задачи для ответа"""
    return {
        "id": str(task["_id"]),
        "name": task["name"],
        "description": task.get("description"),
        "account_id": str(task["account_id"]) if task.get("account_id") else None,
        "url": task["url"],
        "actions": task["actions"],
        "is_active": task.get("is_active", True),
        "run_count": task.get("run_count", 0),
        "created_at": task.get("created_at", datetime.utcnow())
    }


# ========== HEALTH CHECK ==========

@app.get("/api/health")
def health_check():
    """Проверка работоспособности API"""
    try:
        # Проверка подключения к MongoDB
        client.admin.command('ping')
        return {
            "status": "ok",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "error",
            "version": "1.0.0",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
