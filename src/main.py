"""
Главная точка входа приложения
"""

from app.gui.main_window import MainWindow


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
