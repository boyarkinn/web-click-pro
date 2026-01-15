"""
FastAPI сервер для VPS/самостоятельного хостинга
Пока использует in-memory хранилище (без MongoDB)
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import os
import uvicorn
import base64
import openai

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

# Временное in-memory хранилище (до подключения БД на VPS)
ACCOUNTS: dict[str, dict] = {}
TASKS: dict[str, dict] = {}

# Инициализация OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = None

if OPENAI_API_KEY:
    import openai
    openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("[OK] OpenAI клиент инициализирован")
else:
    print("[WARNING] OPENAI_API_KEY не установлен - AI функции недоступны")


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
    accounts = list(ACCOUNTS.values())[skip: skip + limit]
    return [format_account(acc) for acc in accounts]


@app.get("/api/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: str):
    """Получить аккаунт по ID"""
    account = ACCOUNTS.get(account_id)
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
    account_dict["id"] = str(uuid4())
    ACCOUNTS[account_dict["id"]] = account_dict

    return format_account(account_dict)


@app.put("/api/accounts/{account_id}", response_model=AccountResponse)
def update_account(account_id: str, account: AccountCreate):
    """Обновить аккаунт"""
    existing = ACCOUNTS.get(account_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    account_dict = account.dict()
    account_dict["updated_at"] = datetime.utcnow()
    updated = {**existing, **account_dict}
    ACCOUNTS[account_id] = updated
    return format_account(updated)


@app.delete("/api/accounts/{account_id}")
def delete_account(account_id: str):
    """Удалить аккаунт"""
    if account_id not in ACCOUNTS:
        raise HTTPException(status_code=404, detail="Account not found")
    ACCOUNTS.pop(account_id, None)
    return {"message": "Account deleted"}


# ========== TASKS ==========

@app.get("/api/tasks", response_model=List[TaskResponse])
def get_tasks(skip: int = 0, limit: int = 100):
    """Получить список задач"""
    tasks = list(TASKS.values())[skip: skip + limit]
    return [format_task(task) for task in tasks]


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    """Получить задачу по ID"""
    task = TASKS.get(task_id)
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
    task_dict["id"] = str(uuid4())
    TASKS[task_dict["id"]] = task_dict

    return format_task(task_dict)


@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task: TaskCreate):
    """Обновить задачу"""
    existing = TASKS.get(task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    task_dict = task.dict()
    task_dict["updated_at"] = datetime.utcnow()
    updated = {**existing, **task_dict}
    TASKS[task_id] = updated
    return format_task(updated)


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Удалить задачу"""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    TASKS.pop(task_id, None)
    return {"message": "Task deleted"}


# ========== HELPER FUNCTIONS ==========

def format_account(account: dict) -> dict:
    """Форматирование аккаунта для ответа"""
    return {
        "id": str(account["id"]),
        "name": account["name"],
        "login": account["login"],
        "website": account["website"],
        "is_active": account.get("is_active", True),
        "created_at": account.get("created_at", datetime.utcnow())
    }


def format_task(task: dict) -> dict:
    """Форматирование задачи для ответа"""
    return {
        "id": str(task["id"]),
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
    return {
        "status": "ok",
        "version": "1.0.0",
        "database": "in_memory",
        "openai_configured": bool(openai_client)
    }


# ========== AI ENDPOINTS ==========

class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    success: bool


@app.post("/api/ai/chat", response_model=ChatResponse)
def ai_chat(request: ChatRequest):
    """Чат с GPT"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI не настроен. Проверьте OPENAI_API_KEY")
    
    try:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.message})
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1000
        )
        
        return ChatResponse(
            response=response.choices[0].message.content,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при запросе к GPT: {str(e)}")


class AnalyzeImageRequest(BaseModel):
    image_base64: str
    prompt: Optional[str] = "Опиши что изображено на этом изображении"


@app.post("/api/ai/analyze-image", response_model=ChatResponse)
def ai_analyze_image(request: AnalyzeImageRequest):
    """Анализ изображения через GPT-4 Vision"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI не настроен. Проверьте OPENAI_API_KEY")
    
    try:
        import base64
        import traceback
        
        # Определяем тип изображения
        if request.image_base64.startswith("data:image/png"):
            mime_type = "image/png"
            image_data = request.image_base64.split(",", 1)[1]  # Используем split с maxsplit=1
        elif request.image_base64.startswith("data:image/jpeg") or request.image_base64.startswith("data:image/jpg"):
            mime_type = "image/jpeg"
            image_data = request.image_base64.split(",", 1)[1]
        else:
            # Предполагаем base64 без префикса
            mime_type = "image/png"
            image_data = request.image_base64
        
        prompt = request.prompt or "Опиши что изображено на этом изображении"
        
        # Проверяем длину изображения (для отладки)
        print(f"[DEBUG] Image data length: {len(image_data)}")
        print(f"[DEBUG] MIME type: {mime_type}")
        
        # Пробуем использовать актуальную модель
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # Используем gpt-4o вместо gpt-4-vision-preview
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
        except Exception as model_error:
            # Если gpt-4o не работает, пробуем gpt-4-vision-preview
            print(f"[WARNING] gpt-4o failed, trying gpt-4-vision-preview: {model_error}")
            response = openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
        
        return ChatResponse(
            response=response.choices[0].message.content,
            success=True
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"[ERROR] Full error trace:\n{error_trace}")
        error_msg = f"Ошибка при анализе изображения: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
