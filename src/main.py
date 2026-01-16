"""
Главная точка входа приложения
"""

import logging
import os
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def _load_env_file() -> None:
    """Загружает переменные окружения из .env в корне проекта, если файл есть."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main():
    """Главная функция приложения"""
    _load_env_file()
    print("=" * 50)
    print("Веб-Кликер Pro")
    print("=" * 50)
    print("Запуск GUI...")
    
    # Создание и запуск GUI
    from app.gui.main_window import MainWindow
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
