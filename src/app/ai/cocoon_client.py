"""
COCOON клиент для работы с децентрализованной сетью AI inference
Использует HTTP API COCOON для выполнения запросов к моделям

🎯 ДЛЯ РАЗРАБОТЧИКОВ:
Вы используете COCOON как клиент - отправляете запросы на удаленные GPU серверы,
чтобы вычисления происходили на их железе, а не на вашем.

НАСТРОЙКА:
1. Запустите COCOON клиент (C++ сервер, требует Linux/WSL):
   cd cocoon
   ./scripts/cocoon-launch scripts/client.conf
   
   Клиент автоматически подключится к публичным прокси через TON блокчейн
   и предоставит HTTP API на localhost:10000

2. Настройте переменные окружения:
   export COCOON_BASE_URL=http://localhost:10000
   export LLM_TYPE=cocoon

3. Подробная инструкция: см. COCOON_DEVELOPER_GUIDE.md

ПРИМЕЧАНИЕ: Если COCOON недоступен, приложение автоматически 
переключится на локальный LLM клиент.
"""

import os
import requests
from typing import Optional, List, Dict, Any
import json


class CocoonClient:
    """Клиент для работы с COCOON сетью AI inference"""
    
    def __init__(self, 
                 base_url: str = None,
                 model_name: str = "Qwen/Qwen3-0.6B",
                 api_key: Optional[str] = None):
        """
        Инициализация COCOON клиента
        
        Args:
            base_url: URL COCOON клиента (если None, берется из переменной окружения или используется дефолтный)
            model_name: Название модели (например, "Qwen/Qwen3-0.6B")
            api_key: API ключ для аутентификации (опционально)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("COCOON_API_KEY")
        
        # Дефолтный URL для локального COCOON клиента
        default_url = "http://localhost:10000"
        self.base_url = base_url or os.getenv("COCOON_BASE_URL", default_url)
        self.base_url = self.base_url.rstrip("/")
        
        # Проверяем доступность COCOON
        self._check_connection()
    
    def _check_connection(self):
        """Проверка доступности COCOON клиента"""
        try:
            # Пробуем получить список моделей
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5,
                headers=self._get_headers()
            )
            if response.status_code == 200:
                print(f"[OK] COCOON клиент доступен по адресу {self.base_url}")
            else:
                print(f"[WARNING] COCOON клиент отвечает с кодом {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[WARNING] Не удалось подключиться к COCOON клиенту: {e}")
            print(f"[INFO] Убедитесь, что COCOON клиент запущен на {self.base_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Получение заголовков для запросов"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def chat(self, 
             message: str, 
             system_prompt: Optional[str] = None, 
             max_tokens: int = 500,
             temperature: float = 0.7,
             stream: bool = False) -> Optional[str]:
        """
        Генерация ответа модели через COCOON
        
        Args:
            message: Сообщение пользователя
            system_prompt: Системный промпт (опционально)
            max_tokens: Максимальное количество токенов в ответе
            temperature: Температура генерации (0.0-1.0)
            stream: Использовать ли потоковую генерацию
            
        Returns:
            Ответ модели или None при ошибке
        """
        try:
            # Формируем сообщения в формате OpenAI
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            # Формируем запрос в формате OpenAI API
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream
            }
            
            # Отправляем запрос
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=self._get_headers(),
                timeout=300  # 5 минут для больших моделей
            )
            
            if response.status_code != 200:
                print(f"[ERROR] COCOON вернул ошибку: {response.status_code}")
                print(f"[ERROR] Ответ: {response.text}")
                return None
            
            result = response.json()
            
            # Извлекаем ответ из формата OpenAI
            if "choices" in result and len(result["choices"]) > 0:
                message_content = result["choices"][0]["message"]["content"]
                return message_content.strip()
            else:
                print(f"[ERROR] Неожиданный формат ответа от COCOON: {result}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"[ERROR] Таймаут при запросе к COCOON (превышено 5 минут)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Ошибка при запросе к COCOON: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[ERROR] Ошибка при парсинге JSON ответа от COCOON: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Неожиданная ошибка: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Проверка, настроен ли клиент"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5,
                headers=self._get_headers()
            )
            return response.status_code == 200
        except:
            return False
    
    def get_models(self) -> Optional[List[str]]:
        """
        Получение списка доступных моделей
        
        Returns:
            Список названий моделей или None при ошибке
        """
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result:
                    return [model["id"] for model in result["data"]]
                return []
            else:
                print(f"[ERROR] Не удалось получить список моделей: {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] Ошибка при получении списка моделей: {e}")
            return None


def create_cocoon_client(model_name: Optional[str] = None, 
                         base_url: Optional[str] = None) -> Optional[CocoonClient]:
    """
    Создание COCOON клиента
    
    Args:
        model_name: Название модели (если None, используется из переменной окружения или дефолтная)
        base_url: URL COCOON клиента (если None, используется из переменной окружения или дефолтный)
        
    Returns:
        CocoonClient или None при ошибке
    """
    try:
        model = model_name or os.getenv("COCOON_MODEL", "Qwen/Qwen3-0.6B")
        client = CocoonClient(model_name=model, base_url=base_url)
        return client
    except Exception as e:
        print(f"[ERROR] Не удалось создать COCOON клиент: {e}")
        return None
