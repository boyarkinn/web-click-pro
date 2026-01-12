"""
Контроллер для общения с ИИ и получения команд
Управляет диалогом с ИИ для генерации команд автоматизации
"""

from typing import Optional, Dict, Any, List
import json

from .commands import ActionType
from .validator import CommandValidator
from .executor import CommandExecutor
from ..core.clicker import WebClicker
from ..api.client import APIClient


class AIController:
    """Контроллер для работы с ИИ и выполнения команд"""
    
    def __init__(self, clicker: WebClicker, api_client: APIClient):
        """
        Инициализация контроллера
        
        Args:
            clicker: Экземпляр WebClicker
            api_client: Клиент для работы с API на Railway
        """
        self.clicker = clicker
        self.api_client = api_client
        self.executor = CommandExecutor(clicker)
        self.validator = CommandValidator()
        self.context_needed = True  # Нужен ли контекст страницы для следующей команды
    
    def get_page_context(self) -> str:
        """
        Получение контекста текущей страницы
        
        Returns:
            Строка с описанием страницы для ИИ
        """
        if not self.clicker.driver:
            return "Браузер не запущен"
        
        try:
            content = self.clicker.read_page_content()
            
            context = f"""Текущая страница:
URL: {content.get('url', 'Неизвестно')}
Заголовок: {content.get('title', 'Неизвестно')}

Доступные элементы:
- Кнопки: {', '.join(content.get('buttons', [])[:10]) if content.get('buttons') else 'Не найдено'}
- Ссылки: {len(content.get('links', []))} ссылок
- Поля ввода: {content.get('inputs', 0)} полей

Текст страницы (первые 300 символов): {content.get('text', '')[:300]}"""
            
            return context
        except Exception as e:
            return f"Ошибка при получении контекста: {str(e)}"
    
    def generate_command(self, user_message: str, include_context: bool = None) -> Dict[str, Any]:
        """
        Генерация команды через ИИ
        
        Args:
            user_message: Сообщение пользователя с инструкцией
            include_context: Включать ли контекст страницы (если None, используется self.context_needed)
            
        Returns:
            Словарь с командой или None при ошибке
        """
        if include_context is None:
            include_context = self.context_needed
        
        # Формируем промпт для ИИ
        system_prompt = """Ты часть системы автоматизации веб-сайтов. Твоя задача - преобразовывать инструкции пользователя в JSON команды для выполнения действий на сайте.

ВАЖНО: 
- Когда пользователь просит выполнить действие (нажать кнопку, ввести текст, перейти и т.д.) - верни ТОЛЬКО JSON команду
- Если действие невозможно выполнить или есть проблема (элемент не найден, неясная инструкция) - верни JSON с полем "error" и объяснением проблемы: {"error": "объяснение проблемы"}
- НЕ пиши объяснения вне JSON - только команда или ошибка в формате JSON

Доступные команды:
1. click - клик по элементу
   {"action": "click", "selector": "селектор", "method": "css|xpath|id|name|class|tag|text"}

2. type - ввод текста
   {"action": "type", "selector": "селектор", "value": "текст для ввода", "method": "css|xpath|id|name|class|tag", "clear_first": true, "press_enter": false}

3. scroll - прокрутка страницы
   {"action": "scroll", "direction": "up|down|top|bottom|to_element", "selector": "селектор (если to_element)", "pixels": число (опционально)}

4. wait - ожидание
   {"action": "wait", "seconds": число} или {"action": "wait", "wait_for_element": true, "selector": "селектор"}

5. navigate - переход по URL
   {"action": "navigate", "url": "https://example.com"}

6. get_text - получение текста элемента
   {"action": "get_text", "selector": "селектор", "method": "css|xpath|id|name|class|tag"}

7. get_attribute - получение атрибута элемента
   {"action": "get_attribute", "selector": "селектор", "value": "название атрибута", "method": "css|xpath|id|name|class|tag"}

8. screenshot - скриншот страницы
   {"action": "screenshot", "filename": "screenshot.png"}

ФОРМАТ ОТВЕТА:
- Успешная команда: {"action": "...", "selector": "...", ...} - только JSON, без текста
- Ошибка: {"error": "подробное объяснение проблемы"} - если элемент не найден, инструкция неясна и т.д.

ПРАВИЛА:
- Для метода селектора используй: css, xpath, id, name, class, tag, text
- Для поиска по тексту используй method: "text" и в selector укажи текст элемента
- Будь точным в селекторах - используй ID или уникальные классы когда возможно
- Если текст кнопки/элемента указан в инструкции - используй method: "text" и в selector укажи этот текст"""

        user_prompt = user_message
        
        if include_context:
            context = self.get_page_context()
            user_prompt = f"{context}\n\nИнструкция пользователя: {user_message}"
            self.context_needed = False  # Контекст больше не нужен до следующего изменения страницы
        
        try:
            response = self.api_client.ai_chat(user_prompt, system_prompt)
            if not response:
                return {"error": "ИИ не вернул ответ"}
            
            # Пытаемся извлечь JSON из ответа
            command_dict = self._extract_json(response)
            
            if not command_dict:
                return {"error": f"Не удалось извлечь JSON из ответа ИИ: {response}", "raw_response": response}
            
            # Проверяем, это ошибка или команда
            if "error" in command_dict:
                return {"error": command_dict["error"], "raw_response": response}
            
            # Валидируем команду
            is_valid, error = self.validator.validate(command_dict)
            if not is_valid:
                return {"error": f"Команда не прошла валидацию: {error}", "raw_response": response}
            
            return {"command": command_dict, "raw_response": response}
        except Exception as e:
            return {"error": f"Ошибка при генерации команды: {str(e)}"}
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Извлечение JSON из текста ответа ИИ
        
        Args:
            text: Текст ответа
            
        Returns:
            Словарь с командой или None
        """
        # Пытаемся найти JSON в тексте
        text = text.strip()
        
        # Если весь текст - JSON
        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except:
                pass
        
        # Ищем JSON внутри текста
        start = text.find("{")
        end = text.rfind("}") + 1
        
        if start >= 0 and end > start:
            json_str = text[start:end]
            try:
                return json.loads(json_str)
            except:
                pass
        
        # Попробуем найти JSON в code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                json_str = text[start:end].strip()
                try:
                    return json.loads(json_str)
                except:
                    pass
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                json_str = text[start:end].strip()
                try:
                    return json.loads(json_str)
                except:
                    pass
        
        return None
    
    def execute_command(self, command_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнение команды
        
        Args:
            command_dict: Словарь с командой
            
        Returns:
            Результат выполнения
        """
        success, message, result = self.executor.execute(command_dict)
        
        # Если выполнялась навигация или клик, нужно обновить контекст
        action = command_dict.get("action")
        if action in ["navigate", "click"]:
            self.context_needed = True
        
        return {
            "success": success,
            "message": message,
            "result": result,
            "action": action
        }
    
    def process_user_instruction(self, user_message: str) -> Dict[str, Any]:
        """
        Обработка инструкции пользователя (генерация + выполнение)
        
        Args:
            user_message: Инструкция пользователя
            
        Returns:
            Результат выполнения
        """
        # Генерируем команду
        generation_result = self.generate_command(user_message)
        
        if "error" in generation_result:
            return {
                "success": False,
                "message": generation_result["error"],
                "command": None
            }
        
        command_dict = generation_result["command"]
        
        # Выполняем команду
        execution_result = self.execute_command(command_dict)
        
        return {
            "success": execution_result["success"],
            "message": execution_result["message"],
            "result": execution_result.get("result"),
            "command": command_dict,
            "raw_ai_response": generation_result.get("raw_response")
        }
