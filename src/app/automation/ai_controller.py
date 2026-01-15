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

class AIController:
    """Контроллер для работы с ИИ и выполнения команд"""
    
    def __init__(self, clicker: WebClicker, llm_client):
        """
        Инициализация контроллера
        
        Args:
            clicker: Экземпляр WebClicker
            llm_client: LLM клиент (обязательно)
        """
        if not llm_client:
            raise ValueError("LLM клиент обязателен для работы автоматизации")
        
        self.clicker = clicker
        self.llm_client = llm_client
        self.executor = CommandExecutor(clicker)
        self.validator = CommandValidator()
        self.last_url = None  # URL последней страницы для отслеживания изменений
    
    def get_page_context(self) -> str:
        """
        Получение контекста текущей страницы в текстовом формате для ИИ
        
        Returns:
            Строка с детальным описанием страницы для ИИ
        """
        if not self.clicker.driver:
            return "Браузер не запущен"
        
        try:
            content = self.clicker.read_page_content()
            
            # Формируем структурированный контекст
            context_lines = [
                f"=== ИНФОРМАЦИЯ О СТРАНИЦЕ ===",
                f"URL: {content.get('url', 'Неизвестно')}",
                f"Заголовок: {content.get('title', 'Неизвестно')}",
                ""
            ]
            
            # Кнопки
            buttons = content.get('buttons', [])
            if buttons:
                context_lines.append(f"=== КНОПКИ ({len(buttons)}) ===")
                for i, btn in enumerate(buttons[:20], 1):
                    btn_info = []
                    if btn.get('text'):
                        btn_info.append(f"Текст: '{btn['text']}'")
                    if btn.get('id'):
                        btn_info.append(f"ID: #{btn['id']}")
                    if btn.get('class'):
                        classes = btn['class'].split()[:2]  # Первые 2 класса
                        btn_info.append(f"Класс: .{'.'.join(classes)}")
                    if btn.get('type'):
                        btn_info.append(f"Тип: {btn['type']}")
                    
                    if btn_info:
                        context_lines.append(f"{i}. {', '.join(btn_info)}")
                context_lines.append("")
            
            # Поля ввода
            inputs = content.get('inputs', [])
            if inputs:
                context_lines.append(f"=== ПОЛЯ ВВОДА ({len(inputs)}) ===")
                for i, inp in enumerate(inputs[:20], 1):
                    inp_info = []
                    if inp.get('type'):
                        inp_info.append(f"Тип: {inp['type']}")
                    if inp.get('name'):
                        inp_info.append(f"Name: {inp['name']}")
                    if inp.get('id'):
                        inp_info.append(f"ID: #{inp['id']}")
                    if inp.get('placeholder'):
                        inp_info.append(f"Placeholder: '{inp['placeholder']}'")
                    
                    if inp_info:
                        context_lines.append(f"{i}. {', '.join(inp_info)}")
                context_lines.append("")
            
            # Ссылки
            links = content.get('links', [])
            if links:
                context_lines.append(f"=== ССЫЛКИ ({len(links)}) ===")
                for i, link in enumerate(links[:15], 1):
                    link_info = []
                    if link.get('text'):
                        link_info.append(f"'{link['text']}'")
                    if link.get('href'):
                        href = link['href'][:60]  # Первые 60 символов
                        link_info.append(f"→ {href}")
                    
                    if link_info:
                        context_lines.append(f"{i}. {' '.join(link_info)}")
                context_lines.append("")
            
            # Заголовки
            headings = content.get('headings', [])
            if headings:
                context_lines.append(f"=== ЗАГОЛОВКИ ({len(headings)}) ===")
                for heading in headings[:10]:
                    context_lines.append(f"{heading['level'].upper()}: {heading['text']}")
                context_lines.append("")
            
            # Видимый текст (ключевые фразы)
            visible_text = content.get('visible_text', [])
            if visible_text:
                context_lines.append(f"=== КЛЮЧЕВЫЕ ТЕКСТЫ ===")
                for text in visible_text[:20]:
                    if len(text) > 5:
                        context_lines.append(f"- {text[:100]}")  # Первые 100 символов
                context_lines.append("")
            
            # Предпросмотр основного текста
            body_preview = content.get('body_text_preview', '')
            if body_preview:
                context_lines.append(f"=== ПРЕДПРОСМОТР ТЕКСТА СТРАНИЦЫ ===")
                context_lines.append(body_preview)
            
            return "\n".join(context_lines)
        except Exception as e:
            return f"Ошибка при получении контекста: {str(e)}"
    
    def generate_command(self, user_message: str, include_context: bool = None) -> Dict[str, Any]:
        """
        Генерация команды через ИИ
        
        Args:
            user_message: Сообщение пользователя с инструкцией
            include_context: Включать ли контекст страницы (если None, всегда включается)
            
        Returns:
            Словарь с командой или None при ошибке
        """
        # Всегда передаем контекст страницы, если не указано иное
        if include_context is None:
            include_context = True
        
        # Формируем промпт для ИИ
        system_prompt = """Ты часть системы автоматизации веб-сайтов. Твоя задача - преобразовывать инструкции пользователя в JSON команды для выполнения действий на сайте.

ВАЖНО: 
- Когда пользователь просит выполнить действие (нажать кнопку, ввести текст, перейти и т.д.) - верни ТОЛЬКО JSON команду (ОДНУ команду за раз)
- Если действие невозможно выполнить или есть проблема (элемент не найден, неясная инструкция) - верни JSON с полем "error" и объяснением проблемы: {"error": "объяснение проблемы"}
- НЕ пиши объяснения вне JSON - только команда или ошибка в формате JSON
- Для сложных действий (например "Войди в аккаунт") - верни ОДНУ ПЕРВУЮ команду (например, ввод логина). Пользователь отправит следующую команду для следующего шага.

Доступные команды:
1. click - клик по элементу
   {"action": "click", "selector": "селектор", "method": "css|xpath|id|name|class|tag|text"}
   ДОПУСТИМЫЕ МЕТОДЫ: только "css", "xpath", "id", "name", "class", "tag", "text"
   ЗАПРЕЩЕНО использовать другие методы (js, javascript, query и т.д.)

2. type - ввод текста в поле
   {"action": "type", "selector": "селектор", "value": "текст для ввода", "method": "css|xpath|id|name|class|tag", "clear_first": true, "press_enter": false}
   ДОПУСТИМЫЕ МЕТОДЫ: только "css", "xpath", "id", "name", "class", "tag" (НЕ "text")
   Пример: {"action": "type", "selector": "input[name='username']", "value": "qwerqwer", "method": "css"}

3. scroll - прокрутка страницы
   {"action": "scroll", "direction": "up|down|top|bottom|to_element", "selector": "селектор (если to_element)", "pixels": число (опционально)}

4. wait - ожидание
   {"action": "wait", "seconds": число} или {"action": "wait", "wait_for_element": true, "selector": "селектор"}

5. navigate - переход по URL
   {"action": "navigate", "url": "https://example.com"}

6. get_text - получение текста элемента
   {"action": "get_text", "selector": "селектор", "method": "css|xpath|id|name|class|tag"}
   ДОПУСТИМЫЕ МЕТОДЫ: только "css", "xpath", "id", "name", "class", "tag"

7. get_attribute - получение атрибута элемента
   {"action": "get_attribute", "selector": "селектор", "value": "название атрибута", "method": "css|xpath|id|name|class|tag"}
   ДОПУСТИМЫЕ МЕТОДЫ: только "css", "xpath", "id", "name", "class", "tag"

8. screenshot - скриншот страницы
   {"action": "screenshot", "filename": "screenshot.png"}

ФОРМАТ ОТВЕТА:
- Успешная команда: {"action": "...", "selector": "...", ...} - только JSON, без текста
- Ошибка: {"error": "подробное объяснение проблемы"} - если элемент не найден, инструкция неясна и т.д.

ПРАВИЛА ВЫБОРА МЕТОДА СЕЛЕКТОРА (КРИТИЧЕСКИ ВАЖНО!):
ДОПУСТИМЫЕ МЕТОДЫ (ТОЛЬКО ЭТИ!): "css", "xpath", "id", "name", "class", "tag", "text"
ЗАПРЕЩЕНО использовать другие методы (js, javascript, query, querySelector и т.д.) - они НЕ ПОДДЕРЖИВАЮТСЯ!

- CSS селекторы (method: "css"): 
  * Начинаются с # (id) или . (class): "#login-form", ".button"
  * Содержат []: "input[name='username']", "#form input[type='text']"
  * Комбинации: "#login-form input[name='username']", ".button.primary"
  * Если селектор содержит #, . или [] - ВСЕГДА используй method: "css"
  
- XPath селекторы (method: "xpath"):
  * Начинаются с // или /: "//button[@type='submit']", "/html/body/div"
  * Содержат @: "//input[@name='username']"
  * Используй только для сложных поисков, если CSS не подходит
  
- Другие методы (ТОЛЬКО ЭТИ!):
  * method: "id" - только для простого ID без #: {"selector": "login-form", "method": "id"}
  * method: "name" - только для атрибута name: {"selector": "username", "method": "name"}
  * method: "class" - только для одного класса без .: {"selector": "button", "method": "class"}
  * method: "tag" - только для тега: {"selector": "button", "method": "tag"}
  * method: "text" - для поиска по тексту элемента (ТОЛЬКО для click): {"selector": "Войти", "method": "text"}

ПРАВИЛА:
- Будь точным в селекторах - используй ID, name или CSS селекторы когда возможно
- Если текст кнопки/элемента указан в инструкции - используй method: "text" и в selector укажи этот текст
- Для форм используй CSS селекторы: "input[name='username']", "#login-form input[type='password']"
- НИКОГДА не используй XPath для CSS селекторов! Если видишь #, . или [] - используй method: "css"
- НИКОГДА не используй методы "js", "javascript", "query" и т.д. - они НЕ РАБОТАЮТ! Используй ТОЛЬКО допустимые методы: "css", "xpath", "id", "name", "class", "tag", "text" """

        user_prompt = user_message
        
        if include_context:
            context = self.get_page_context()
            user_prompt = f"{context}\n\nИнструкция пользователя: {user_message}"
        
        try:
            # Используем локальный LLM
            if not self.llm_client:
                return {"error": "Локальный LLM клиент не инициализирован"}
            
            response = self.llm_client.chat(user_prompt, system_prompt, max_tokens=500)
            
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
        
        # Обновляем последний URL для отслеживания изменений страницы
        action = command_dict.get("action")
        if action == "navigate":
            # После навигации обновляем URL
            if self.clicker.driver:
                try:
                    self.last_url = self.clicker.driver.current_url
                except:
                    pass
        
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
