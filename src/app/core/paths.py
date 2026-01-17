"""
Утилиты для определения путей приложения.
"""

from __future__ import annotations

from pathlib import Path
import sys


def get_app_root() -> Path:
    """
    Возвращает базовую директорию приложения.

    - В обычном режиме: корень проекта.
    - В собранном exe (PyInstaller): папка с exe.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[3]


def get_env_path() -> Path:
    """Возвращает путь к .env рядом с приложением."""
    return get_app_root() / ".env"
