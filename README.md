# Веб-Кликер Pro

Десктопное приложение для автоматизации работы с веб-сайтами. Поддерживает открытие сайтов, поиск элементов, клики, чтение содержимого, анализ через AI и синхронизацию с облачным бэкендом.

## Структура проекта

```
clicker-app/
├── src/                    # Исходный код десктопного приложения
│   ├── main.py            # Точка входа
│   └── app/               # Основной пакет
│       ├── core/          # Ядро (кликер)
│       └── api/           # API клиент для бэкенда
├── server/                 # Облачный сервер (VPS/самостоятельный хостинг)
│   ├── main.py            # FastAPI сервер
│   └── requirements.txt   # Зависимости для сервера
├── examples/               # Примеры использования
└── requirements.txt        # Зависимости для десктопа
```

## Возможности

- ✅ Открытие и навигация по сайтам
- ✅ Поиск элементов по различным селекторам (CSS, XPath, ID и т.д.)
- ✅ Клики по элементам
- ✅ Ввод текста в поля
- ✅ Чтение текста и атрибутов элементов
- ✅ Анализ содержимого страницы
- ✅ Ожидание элементов
- ✅ Прокрутка страницы
- ✅ Выполнение JavaScript кода
- ✅ Создание скриншотов
- ✅ Синхронизация с облачным бэкендом
- ✅ Управление аккаунтами и задачами

## Установка

1. Установите Python 3.7 или выше

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. ChromeDriver установится автоматически:
   - При первом запуске `webdriver-manager` автоматически скачает нужную версию ChromeDriver
   - Ничего делать не нужно - все работает "из коробки"!
   
   **Что такое ChromeDriver?**
   - Это программа, которая позволяет Selenium управлять браузером Chrome
   - Без него Selenium не сможет открыть Chrome
   - `webdriver-manager` автоматически находит и скачивает правильную версию для вашей версии Chrome
   
   **Если нужна ручная установка:**
   - Скачайте с [ChromeDriver](https://chromedriver.chromium.org/)
   - Распакуйте и добавьте в PATH системы
   - Но это обычно не требуется!

## Быстрый старт

### Запуск приложения

```bash
python src/main.py
```

### Примеры

Примеры использования находятся в папке `examples/`:

```bash
python examples/example.py
```

### Базовый пример

```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.clicker import WebClicker

# Создание кликера
clicker = WebClicker(headless=False)

# Запуск браузера
clicker.start_browser("chrome")

# Открытие сайта
clicker.open_url("https://example.com")

# Ожидание
clicker.wait(2)

# Клик по элементу
clicker.click("a[href*='example']")

# Ввод текста
clicker.type_text("#search", "текст для поиска")

# Чтение текста
text = clicker.get_text(".content")

# Закрытие браузера
clicker.close()
```

## API клиент

Для работы с облачным бэкендом используйте `APIClient`:

```python
from app.api.client import APIClient

client = APIClient("http://your-server.example.com")

# Получить список аккаунтов
accounts = client.get_accounts()

# Создать аккаунт
new_account = client.create_account(
    name="My Account",
    login="user@example.com",
    password="password123",
    website="https://example.com"
)
```

## Сервер (VPS)

Сервер находится в папке `server/` и деплоится на VPS/самостоятельный хостинг.

Для локального запуска:
```bash
cd server
pip install -r requirements.txt
python main.py
```

## Примечания

- Убедитесь, что у вас установлен Chrome или Firefox
- Для Chrome автоматически используется ChromeDriver через webdriver-manager
- Используйте разумные задержки между действиями, чтобы не перегружать сайт
- Некоторые сайты могут блокировать автоматизацию - используйте опции для обхода

## Лицензия

Свободное использование для личных и коммерческих целей.
