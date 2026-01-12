"""
Локальный LLM клиент для работы с моделями через transformers
Поддерживает Qwen2.5-0.5B-Instruct и другие модели с Hugging Face
"""

import os
from typing import Optional, List, Dict, Any
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


class LocalLLMClient:
    """Клиент для работы с локальными LLM моделями"""
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-0.5B-Instruct", device: str = None):
        """
        Инициализация локального LLM клиента
        
        Args:
            model_name: Название модели с Hugging Face (например, "Qwen/Qwen2.5-0.5B-Instruct")
            device: Устройство для выполнения ("cpu", "cuda", или None для автоматического выбора)
        """
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self._load_model()
    
    def _load_model(self):
        """Загрузка модели и токенизатора"""
        try:
            print(f"[INFO] Загрузка модели {self.model_name} на устройство {self.device}...")
            
            # Загружаем токенизатор
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Загружаем модель
            # Используем torch_dtype=torch.float16 для CPU (меньше памяти) или float32
            # Для CPU используем float32 или bfloat16 если поддерживается
            torch_dtype = torch.float32 if self.device == "cpu" else torch.float16
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch_dtype,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # Перемещаем модель на CPU если нужно
            if self.device == "cpu":
                self.model = self.model.to("cpu")
            
            # Создаем pipeline для генерации
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,  # -1 для CPU
                torch_dtype=torch_dtype
            )
            
            print(f"[OK] Модель {self.model_name} загружена успешно")
            
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке модели: {e}")
            raise
    
    def chat(self, message: str, system_prompt: Optional[str] = None, max_tokens: int = 500) -> Optional[str]:
        """
        Генерация ответа модели
        
        Args:
            message: Сообщение пользователя
            system_prompt: Системный промпт (опционально)
            max_tokens: Максимальное количество токенов в ответе
            
        Returns:
            Ответ модели или None при ошибке
        """
        if not self.pipeline:
            print("[ERROR] Модель не загружена")
            return None
        
        try:
            # Формируем промпт для Qwen2.5
            # Qwen использует стандартный chat template через apply_chat_template
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})
            
            # Применяем chat template для форматирования промпта
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Генерируем ответ
            outputs = self.pipeline(
                prompt,
                max_new_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                return_full_text=False
            )
            
            # Извлекаем сгенерированный текст
            generated_text = outputs[0]["generated_text"]
            
            # Очищаем ответ
            generated_text = generated_text.strip()
            
            return generated_text
            
        except Exception as e:
            print(f"[ERROR] Ошибка при генерации ответа: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Проверка, настроена ли модель"""
        return self.pipeline is not None


def create_local_llm_client(model_name: Optional[str] = None) -> Optional[LocalLLMClient]:
    """
    Создание локального LLM клиента
    
    Args:
        model_name: Название модели (если None, используется Qwen2.5-0.5B-Instruct)
        
    Returns:
        LocalLLMClient или None при ошибке
    """
    try:
        # Проверяем переменную окружения для модели
        model = model_name or os.getenv("LOCAL_LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
        client = LocalLLMClient(model_name=model)
        return client
    except Exception as e:
        print(f"[ERROR] Не удалось создать локальный LLM клиент: {e}")
        return None
