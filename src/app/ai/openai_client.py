"""
Клиент для работы с OpenAI API
"""

import os
from typing import Optional, Dict, Any, List
import openai


class OpenAIClient:
    """Клиент для работы с OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация OpenAI клиента
        
        Args:
            api_key: API ключ OpenAI (если None, берется из переменной окружения)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set! "
                "Please set OPENAI_API_KEY in your environment variables."
            )
        
        # Инициализация OpenAI клиента
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        
        print("[OK] OpenAI клиент инициализирован")
    
    def analyze_image(self, image_path: str, prompt: str = "Опиши что изображено на этом изображении") -> Optional[str]:
        """
        Анализ изображения через GPT-4 Vision
        
        Args:
            image_path: Путь к изображению
            prompt: Текст запроса для анализа
        
        Returns:
            Описание изображения или None при ошибке
        """
        try:
            import base64
            
            # Читаем и кодируем изображение в base64
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Определяем тип изображения
            image_ext = os.path.splitext(image_path)[1].lower()
            mime_type = "image/jpeg" if image_ext in [".jpg", ".jpeg"] else "image/png"
            
            response = self.client.chat.completions.create(
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
                max_tokens=300
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] Ошибка при анализе изображения: {e}")
            return None
    
    def analyze_text(self, text: str, prompt: str = "Проанализируй этот текст") -> Optional[str]:
        """
        Анализ текста через GPT
        
        Args:
            text: Текст для анализа
            prompt: Текст запроса для анализа
        
        Returns:
            Результат анализа или None при ошибке
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] Ошибка при анализе текста: {e}")
            return None
    
    def chat(self, message: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Обычный чат с GPT
        
        Args:
            message: Сообщение пользователя
            system_prompt: Системный промпт (опционально)
        
        Returns:
            Ответ GPT или None при ошибке
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] Ошибка при запросе к GPT: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Проверка, настроен ли клиент"""
        return self.api_key is not None


# Пример использования
if __name__ == "__main__":
    try:
        client = OpenAIClient()
        print("[OK] OpenAI клиент создан успешно")
        
        # Тестовый запрос
        response = client.chat("Привет! Как дела?")
        if response:
            print(f"Ответ GPT: {response}")
    except ValueError as e:
        print(f"[ERROR] {e}")
