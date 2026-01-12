"""
Примеры использования веб-кликера
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app.core.clicker import WebClicker
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


def example_1_basic_navigation():
    """Пример 1: Базовая навигация и чтение"""
    print("\n=== Пример 1: Базовая навигация ===")
    
    clicker = WebClicker(headless=False)
    
    try:
        clicker.start_browser("chrome")
        clicker.open_url("https://example.com")
        clicker.wait(2)
        
        # Читаем содержимое страницы
        content = clicker.read_page_content()
        print(f"Заголовок страницы: {content.get('title')}")
        print(f"URL: {content.get('url')}")
        
        # Получаем текст элемента
        text = clicker.get_text("h1")
        print(f"Текст заголовка: {text}")
        
    finally:
        clicker.close()


if __name__ == "__main__":
    print("Примеры использования веб-кликера")
    print("=" * 50)
    example_1_basic_navigation()
    print("\n" + "=" * 50)
    print("Примеры завершены")
