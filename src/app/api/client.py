"""
HTTP клиент для связи с облачным бэкендом на Railway
"""

import requests
from typing import Optional, List, Dict, Any
import os


class APIClient:
    """Клиент для работы с API на Railway"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            base_url: URL бэкенда (если None, берется из переменной окружения)
        """
        self.base_url = base_url or os.getenv(
            "API_BASE_URL",
            "http://localhost:8000"  # По умолчанию локальный сервер для разработки
        )
        self.base_url = self.base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
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
    
    # ========== HEALTH CHECK ==========
    
    def health_check(self) -> bool:
        """Проверка подключения к API"""
        result = self._request("GET", "/api/health")
        return result is not None and result.get("status") == "ok"
