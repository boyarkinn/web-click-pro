"""
Клиент для работы с ИИ через облачный бэкенд
"""

from typing import Optional

from app.api.client import APIClient


class RemoteLLMClient:
    """Клиент для работы с ИИ через API бэкенда"""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.api = APIClient(base_url=base_url)

    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 500,
    ) -> Optional[str]:
        # max_tokens пока не поддерживается в API клиента, оставляем для совместимости
        _ = max_tokens
        return self.api.ai_chat(message=message, system_prompt=system_prompt)

    def is_available(self) -> bool:
        return self.api.health_check()
