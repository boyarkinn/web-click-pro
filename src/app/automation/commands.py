"""
Определения типов команд для автоматизации
Структурированные команды, которые ИИ может генерировать
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class ActionType(Enum):
    """Типы действий, которые может выполнять кликер"""
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"
    GET_TEXT = "get_text"
    GET_ATTRIBUTE = "get_attribute"
    SCREENSHOT = "screenshot"


class SelectorMethod(Enum):
    """Методы поиска элементов"""
    CSS = "css"
    XPATH = "xpath"
    ID = "id"
    NAME = "name"
    CLASS = "class"
    TAG = "tag"
    TEXT = "text"  # Поиск по тексту элемента


class ScrollDirection(Enum):
    """Направления прокрутки"""
    UP = "up"
    DOWN = "down"
    TO_ELEMENT = "to_element"
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class Command:
    """Базовая команда"""
    action: ActionType
    selector: Optional[str] = None
    method: SelectorMethod = SelectorMethod.CSS
    value: Optional[str] = None
    timeout: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование команды в словарь"""
        result = {
            "action": self.action.value,
            "method": self.method.value
        }
        if self.selector:
            result["selector"] = self.selector
        if self.value:
            result["value"] = self.value
        if self.timeout:
            result["timeout"] = self.timeout
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Command":
        """Создание команды из словаря"""
        action = ActionType(data.get("action", "click"))
        method = SelectorMethod(data.get("method", "css"))
        return cls(
            action=action,
            selector=data.get("selector"),
            method=method,
            value=data.get("value"),
            timeout=data.get("timeout")
        )


@dataclass
class ClickCommand(Command):
    """Команда клика по элементу"""
    action: ActionType = ActionType.CLICK
    scroll: bool = True  # Прокрутить к элементу перед кликом
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["scroll"] = self.scroll
        return result


@dataclass
class TypeCommand(Command):
    """Команда ввода текста"""
    action: ActionType = ActionType.TYPE
    clear_first: bool = True  # Очистить поле перед вводом
    press_enter: bool = False  # Нажать Enter после ввода
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["clear_first"] = self.clear_first
        result["press_enter"] = self.press_enter
        return result


@dataclass
class ScrollCommand(Command):
    """Команда прокрутки страницы"""
    action: ActionType = ActionType.SCROLL
    direction: ScrollDirection = ScrollDirection.DOWN
    pixels: Optional[int] = None  # Количество пикселей для прокрутки
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["direction"] = self.direction.value
        if self.pixels:
            result["pixels"] = self.pixels
        return result


@dataclass
class WaitCommand(Command):
    """Команда ожидания"""
    action: ActionType = ActionType.WAIT
    seconds: Optional[float] = None  # Ждать определенное количество секунд
    wait_for_element: bool = False  # Ждать появления элемента
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.seconds:
            result["seconds"] = self.seconds
        result["wait_for_element"] = self.wait_for_element
        return result


@dataclass
class NavigateCommand(Command):
    """Команда навигации по URL"""
    action: ActionType = ActionType.NAVIGATE
    url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.url:
            result["url"] = self.url
        return result
