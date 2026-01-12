"""
Главная точка входа приложения
"""

import logging
from app.gui.main_window import MainWindow

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def main():
    """Главная функция приложения"""
    print("=" * 50)
    print("Веб-Кликер Pro")
    print("=" * 50)
    print("Запуск GUI...")
    
    # Создание и запуск GUI
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
