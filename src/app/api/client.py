"""
HTTP клиент для связи с облачным бэкендом
"""

import requests
from typing import Optional, List, Dict, Any
import os
import base64


class APIClient:
    """Клиент для работы с API бэкенда"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            base_url: URL бэкенда (если None, берется из переменной окружения)
        """
        self.base_url = base_url or os.getenv(
            "API_BASE_URL",
            "http://90.156.225.111:8000"
        )
        self.base_url = self.base_url.rstrip("/")
        
        # Добавляем https:// если протокол не указан
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = "https://" + self.base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        self.auth_token = os.getenv("API_AUTH_TOKEN")
        if self.auth_token:
            self.set_auth_token(self.auth_token)

    def set_auth_token(self, token: str) -> None:
        """Установить токен авторизации"""
        self.auth_token = token
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })

    def clear_auth_token(self) -> None:
        """Сбросить токен авторизации"""
        self.auth_token = None
        self.session.headers.pop("Authorization", None)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        Выполнение HTTP запроса
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE)
            endpoint: Путь API
            **kwargs: Дополнительные параметры для requests
        
        Returns:
            Ответ в виде словаря или None при ошибке
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка запроса к {url}: {e}")
            return None
    
    # ========== ACCOUNTS ==========
    
    def get_accounts(self) -> List[Dict]:
        """Получить список аккаунтов"""
        result = self._request("GET", "/api/accounts")
        return result if result else []
    
    def get_account(self, account_id: str) -> Optional[Dict]:
        """Получить аккаунт по ID"""
        return self._request("GET", f"/api/accounts/{account_id}")
    
    def create_account(self, name: str, login: str, password: str, 
                      website: str, notes: Optional[str] = None) -> Optional[Dict]:
        """Создать новый аккаунт"""
        data = {
            "name": name,
            "login": login,
            "password": password,
            "website": website,
            "notes": notes
        }
        return self._request("POST", "/api/accounts", json=data)
    
    def update_account(self, account_id: str, name: str, login: str, 
                      password: str, website: str, notes: Optional[str] = None) -> Optional[Dict]:
        """Обновить аккаунт"""
        data = {
            "name": name,
            "login": login,
            "password": password,
            "website": website,
            "notes": notes
        }
        return self._request("PUT", f"/api/accounts/{account_id}", json=data)
    
    def delete_account(self, account_id: str) -> bool:
        """Удалить аккаунт"""
        result = self._request("DELETE", f"/api/accounts/{account_id}")
        return result is not None
    
    # ========== TASKS ==========
    
    def get_tasks(self) -> List[Dict]:
        """Получить список задач"""
        result = self._request("GET", "/api/tasks")
        return result if result else []
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Получить задачу по ID"""
        return self._request("GET", f"/api/tasks/{task_id}")
    
    def create_task(self, name: str, url: str, actions: Dict, 
                   description: Optional[str] = None, 
                   account_id: Optional[str] = None) -> Optional[Dict]:
        """Создать новую задачу"""
        data = {
            "name": name,
            "url": url,
            "actions": actions,
            "description": description,
            "account_id": account_id
        }
        return self._request("POST", "/api/tasks", json=data)
    
    def update_task(self, task_id: str, name: str, url: str, actions: Dict,
                   description: Optional[str] = None,
                   account_id: Optional[str] = None) -> Optional[Dict]:
        """Обновить задачу"""
        data = {
            "name": name,
            "url": url,
            "actions": actions,
            "description": description,
            "account_id": account_id
        }
        return self._request("PUT", f"/api/tasks/{task_id}", json=data)
    
    def delete_task(self, task_id: str) -> bool:
        """Удалить задачу"""
        result = self._request("DELETE", f"/api/tasks/{task_id}")
        return result is not None

    # ========== AUTH ==========

    def register_user(
        self,
        login: str,
        email: str,
        password: str,
        confirm_password: str,
    ) -> Optional[Dict]:
        """Регистрация нового пользователя"""
        data = {
            "login": login,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
        }
        result = self._request("POST", "/api/auth/register", json=data)
        if result and result.get("token"):
            self.set_auth_token(result["token"])
        return result

    def login_user(self, identifier: str, password: str) -> Optional[Dict]:
        """Вход по логину или почте"""
        data = {
            "identifier": identifier,
            "password": password,
        }
        result = self._request("POST", "/api/auth/login", json=data)
        if result and result.get("token"):
            self.set_auth_token(result["token"])
        return result

    def get_profile(self) -> Optional[Dict]:
        """Получить профиль текущего пользователя"""
        return self._request("GET", "/api/auth/me")
    
    # ========== HEALTH CHECK ==========
    
    def health_check(self) -> bool:
        """Проверка подключения к API"""
        result = self._request("GET", "/api/health")
        return result is not None and result.get("status") == "ok"
    
    # ========== AI ==========
    
    def ai_chat(self, message: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Чат с GPT через API"""
        data = {
            "message": message,
            "system_prompt": system_prompt
        }
        result = self._request("POST", "/api/ai/chat", json=data)
        return result.get("response") if result and result.get("success") else None
    
    def ai_analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Optional[str]:
        """Анализ изображения через GPT-4 Vision через API"""
        try:
            import base64
            
            # Читаем и кодируем изображение в base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Определяем тип изображения
            image_ext = os.path.splitext(image_path)[1].lower()
            mime_type = "image/jpeg" if image_ext in [".jpg", ".jpeg"] else "image/png"
            
            # Формируем base64 URL
            image_base64 = f"data:{mime_type};base64,{image_data}"
            
            data = {
                "image_base64": image_base64,
                "prompt": prompt or "Опиши что изображено на этом изображении"
            }
            
            result = self._request("POST", "/api/ai/analyze-image", json=data)
            return result.get("response") if result and result.get("success") else None
        except Exception as e:
            print(f"[ERROR] Ошибка при анализе изображения: {e}")
            return None