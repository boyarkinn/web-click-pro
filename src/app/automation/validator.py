"""
Валидация команд перед выполнением
Проверяет корректность команд, сгенерированных ИИ
"""

from typing import Optional, List, Tuple
from .commands import Command, ActionType, SelectorMethod, ScrollDirection


class CommandValidator:
    """Валидатор команд"""
    
    @staticmethod
    def validate(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """
        Валидация команды
        
        Args:
            command_dict: Словарь с командой
            
        Returns:
            Tuple[bool, Optional[str]]: (валидна ли команда, сообщение об ошибке)
        """
        if not isinstance(command_dict, dict):
            return False, "Команда должна быть словарем"
        
        # Проверяем наличие action
        if "action" not in command_dict:
            return False, "Отсутствует поле 'action'"
        
        # Проверяем тип действия
        try:
            action = ActionType(command_dict["action"])
        except (ValueError, KeyError):
            return False, f"Неизвестный тип действия: {command_dict.get('action')}"
        
        # Валидация в зависимости от типа действия
        if action == ActionType.CLICK:
            return CommandValidator._validate_click(command_dict)
        elif action == ActionType.TYPE:
            return CommandValidator._validate_type(command_dict)
        elif action == ActionType.SCROLL:
            return CommandValidator._validate_scroll(command_dict)
        elif action == ActionType.WAIT:
            return CommandValidator._validate_wait(command_dict)
        elif action == ActionType.NAVIGATE:
            return CommandValidator._validate_navigate(command_dict)
        elif action == ActionType.GET_TEXT:
            return CommandValidator._validate_get_text(command_dict)
        elif action == ActionType.GET_ATTRIBUTE:
            return CommandValidator._validate_get_attribute(command_dict)
        elif action == ActionType.SCREENSHOT:
            return True, None  # Screenshot не требует параметров
        
        return False, f"Валидация для действия {action} не реализована"
    
    @staticmethod
    def _validate_click(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """Валидация команды клика"""
        if "selector" not in command_dict:
            return False, "Команда 'click' требует поле 'selector'"
        
        if not command_dict["selector"]:
            return False, "Селектор не может быть пустым"
        
        # Проверяем метод селектора
        method = command_dict.get("method", "css")
        try:
            SelectorMethod(method)
        except (ValueError, KeyError):
            return False, f"Неизвестный метод селектора: {method}"
        
        return True, None
    
    @staticmethod
    def _validate_type(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """Валидация команды ввода текста"""
        if "selector" not in command_dict:
            return False, "Команда 'type' требует поле 'selector'"
        
        if "value" not in command_dict:
            return False, "Команда 'type' требует поле 'value' (текст для ввода)"
        
        if not command_dict["selector"]:
            return False, "Селектор не может быть пустым"
        
        # Проверяем метод селектора
        method = command_dict.get("method", "css")
        try:
            SelectorMethod(method)
        except (ValueError, KeyError):
            return False, f"Неизвестный метод селектора: {method}"
        
        return True, None
    
    @staticmethod
    def _validate_scroll(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """Валидация команды прокрутки"""
        direction = command_dict.get("direction", "down")
        try:
            ScrollDirection(direction)
        except (ValueError, KeyError):
            return False, f"Неизвестное направление прокрутки: {direction}"
        
        # Если прокрутка к элементу, нужен селектор
        if direction == "to_element":
            if "selector" not in command_dict or not command_dict["selector"]:
                return False, "Прокрутка к элементу требует поле 'selector'"
        
        return True, None
    
    @staticmethod
    def _validate_wait(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """Валидация команды ожидания"""
        seconds = command_dict.get("seconds")
        wait_for_element = command_dict.get("wait_for_element", False)
        
        if not seconds and not wait_for_element:
            return False, "Команда 'wait' требует либо 'seconds', либо 'wait_for_element=True'"
        
        if seconds is not None and (not isinstance(seconds, (int, float)) or seconds < 0):
            return False, "Поле 'seconds' должно быть положительным числом"
        
        if wait_for_element:
            if "selector" not in command_dict or not command_dict["selector"]:
                return False, "Ожидание элемента требует поле 'selector'"
        
        return True, None
    
    @staticmethod
    def _validate_navigate(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """Валидация команды навигации"""
        if "url" not in command_dict:
            return False, "Команда 'navigate' требует поле 'url'"
        
        url = command_dict["url"]
        if not url:
            return False, "URL не может быть пустым"
        
        if not isinstance(url, str):
            return False, "URL должен быть строкой"
        
        # Базовая проверка URL
        if not url.startswith(("http://", "https://", "/")):
            return False, "URL должен начинаться с http://, https:// или /"
        
        return True, None
    
    @staticmethod
    def _validate_get_text(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """Валидация команды получения текста"""
        if "selector" not in command_dict:
            return False, "Команда 'get_text' требует поле 'selector'"
        
        if not command_dict["selector"]:
            return False, "Селектор не может быть пустым"
        
        return True, None
    
    @staticmethod
    def _validate_get_attribute(command_dict: dict) -> Tuple[bool, Optional[str]]:
        """Валидация команды получения атрибута"""
        if "selector" not in command_dict:
            return False, "Команда 'get_attribute' требует поле 'selector'"
        
        if "value" not in command_dict:
            return False, "Команда 'get_attribute' требует поле 'value' (название атрибута)"
        
        if not command_dict["selector"]:
            return False, "Селектор не может быть пустым"
        
        return True, None
    
    @staticmethod
    def validate_batch(commands: List[dict]) -> Tuple[List[dict], List[str]]:
        """
        Валидация списка команд
        
        Args:
            commands: Список команд для валидации
            
        Returns:
            Tuple[List[dict], List[str]]: (валидные команды, ошибки)
        """
        valid_commands = []
        errors = []
        
        for i, cmd in enumerate(commands):
            is_valid, error = CommandValidator.validate(cmd)
            if is_valid:
                valid_commands.append(cmd)
            else:
                errors.append(f"Команда {i + 1}: {error}")
        
        return valid_commands, errors
