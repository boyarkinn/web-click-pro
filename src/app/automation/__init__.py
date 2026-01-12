"""
Модуль автоматизации веб-сайтов с помощью ИИ
Позволяет ИИ управлять браузером через структурированные команды
"""

from .commands import Command, ActionType, ClickCommand, TypeCommand, ScrollCommand, WaitCommand, NavigateCommand
from .validator import CommandValidator
from .executor import CommandExecutor
from .ai_controller import AIController

__all__ = [
    "Command",
    "ActionType",
    "ClickCommand",
    "TypeCommand",
    "ScrollCommand",
    "WaitCommand",
    "NavigateCommand",
    "CommandValidator",
    "CommandExecutor",
    "AIController",
]
