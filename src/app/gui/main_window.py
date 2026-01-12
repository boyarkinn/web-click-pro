"""
Главное окно приложения
"""

import sys
import os

# Пробуем использовать CustomTkinter (современный вид)
try:
    import customtkinter as ctk
    USE_CUSTOM_TKINTER = True
except ImportError:
    # Fallback на обычный Tkinter
    import tkinter as tk
    USE_CUSTOM_TKINTER = False

# Импорт кликера
from app.core.clicker import WebClicker


class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self):
        """Инициализация главного окна"""
        # Инициализация кликера
        self.clicker = None
        
        if USE_CUSTOM_TKINTER:
            # Настройка CustomTkinter
            ctk.set_appearance_mode("dark")  # "light" или "dark"
            ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
            
            # Создание окна
            self.root = ctk.CTk()
            self.root.title("Веб-Кликер Pro")
            self.root.geometry("800x600")
            
            # Центрирование окна
            self._center_window()
            
            # Создание интерфейса
            self._create_widgets()
        else:
            # Обычный Tkinter
            self.root = tk.Tk()
            self.root.title("Веб-Кликер Pro")
            self.root.geometry("800x600")
            self.root.configure(bg="#2b2b2b")
            
            # Центрирование окна
            self._center_window()
            
            # Создание интерфейса
            self._create_widgets_tkinter()
    
    def _center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """Создание виджетов (CustomTkinter)"""
        # Заголовок
        title = ctk.CTkLabel(
            self.root,
            text="Веб-Кликер Pro",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=30)
        
        # Подзаголовок
        subtitle = ctk.CTkLabel(
            self.root,
            text="Автоматизация работы с веб-сайтами",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        subtitle.pack(pady=10)
        
        # Фрейм для ввода URL
        url_frame = ctk.CTkFrame(self.root)
        url_frame.pack(pady=40, padx=40, fill="x")
        
        # Метка для поля ввода
        url_label = ctk.CTkLabel(
            url_frame,
            text="URL сайта:",
            font=ctk.CTkFont(size=14)
        )
        url_label.pack(pady=(20, 10), padx=20)
        
        # Поле ввода URL
        self.url_entry = ctk.CTkEntry(
            url_frame,
            placeholder_text="https://example.com",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.url_entry.pack(pady=10, padx=20, fill="x")
        
        # Кнопка открытия сайта
        self.open_button = ctk.CTkButton(
            url_frame,
            text="Открыть сайт",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=40,
            command=self._open_website
        )
        self.open_button.pack(pady=(10, 20), padx=20, fill="x")
        
        # Статус
        self.status_label = ctk.CTkLabel(
            self.root,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_label.pack(pady=10)
        
        # Версия
        version = ctk.CTkLabel(
            self.root,
            text="Версия 1.0.0",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version.pack(side="bottom", pady=20)
    
    def _create_widgets_tkinter(self):
        """Создание виджетов (обычный Tkinter)"""
        # Заголовок
        title = tk.Label(
            self.root,
            text="Веб-Кликер Pro",
            font=("Arial", 32, "bold"),
            bg="#2b2b2b",
            fg="white"
        )
        title.pack(pady=30)
        
        # Подзаголовок
        subtitle = tk.Label(
            self.root,
            text="Автоматизация работы с веб-сайтами",
            font=("Arial", 16),
            bg="#2b2b2b",
            fg="gray"
        )
        subtitle.pack(pady=10)
        
        # Фрейм для ввода URL
        url_frame = tk.Frame(self.root, bg="#2b2b2b")
        url_frame.pack(pady=40, padx=40, fill="x")
        
        # Метка для поля ввода
        url_label = tk.Label(
            url_frame,
            text="URL сайта:",
            font=("Arial", 14),
            bg="#2b2b2b",
            fg="white"
        )
        url_label.pack(pady=(20, 10))
        
        # Поле ввода URL
        self.url_entry = tk.Entry(
            url_frame,
            font=("Arial", 14),
            bg="#3b3b3b",
            fg="white",
            insertbackground="white",
            relief="flat",
            bd=5
        )
        self.url_entry.pack(pady=10, padx=20, fill="x", ipady=8)
        self.url_entry.insert(0, "https://example.com")
        
        # Кнопка открытия сайта
        self.open_button = tk.Button(
            url_frame,
            text="Открыть сайт",
            font=("Arial", 14, "bold"),
            bg="#0078d4",
            fg="white",
            activebackground="#005a9e",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._open_website
        )
        self.open_button.pack(pady=(10, 20), padx=20, fill="x", ipady=8)
        
        # Статус
        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="gray"
        )
        self.status_label.pack(pady=10)
        
        # Версия
        version = tk.Label(
            self.root,
            text="Версия 1.0.0",
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="gray"
        )
        version.pack(side="bottom", pady=20)
    
    def _open_website(self):
        """Открытие сайта в браузере"""
        url = self.url_entry.get().strip()
        
        # Проверка на пустой URL
        if not url:
            self._update_status("Введите URL сайта", error=True)
            return
        
        # Добавление https:// если отсутствует
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # Обновление статуса
        self._update_status("Запуск браузера...")
        self.open_button.configure(state="disabled" if USE_CUSTOM_TKINTER else "disabled")
        
        try:
            # Создание кликера
            if not self.clicker:
                self.clicker = WebClicker(headless=False)
            
            # Запуск браузера
            if not self.clicker.driver:
                if not self.clicker.start_browser("chrome"):
                    self._update_status("Ошибка: не удалось запустить браузер", error=True)
                    self.open_button.configure(state="normal" if USE_CUSTOM_TKINTER else "normal")
                    return
            
            # Открытие сайта
            if self.clicker.open_url(url):
                self._update_status(f"Сайт открыт: {url}", success=True)
            else:
                self._update_status("Ошибка при открытии сайта", error=True)
            
        except Exception as e:
            self._update_status(f"Ошибка: {str(e)}", error=True)
        finally:
            self.open_button.configure(state="normal" if USE_CUSTOM_TKINTER else "normal")
    
    def _update_status(self, message: str, error: bool = False, success: bool = False):
        """Обновление статуса"""
        if USE_CUSTOM_TKINTER:
            if error:
                self.status_label.configure(text=message, text_color="red")
            elif success:
                self.status_label.configure(text=message, text_color="green")
            else:
                self.status_label.configure(text=message, text_color="gray")
        else:
            if error:
                self.status_label.configure(text=message, fg="red")
            elif success:
                self.status_label.configure(text=message, fg="green")
            else:
                self.status_label.configure(text=message, fg="gray")
    
    def run(self):
        """Запуск главного цикла приложения"""
        # Закрытие браузера при закрытии окна
        if USE_CUSTOM_TKINTER:
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        else:
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.root.mainloop()
    
    def _on_closing(self):
        """Обработка закрытия окна"""
        if self.clicker:
            self.clicker.close()
        self.root.destroy()


def create_app():
    """Создание и запуск приложения"""
    app = MainWindow()
    app.run()
    return app


if __name__ == "__main__":
    # Для тестирования
    app = MainWindow()
    app.run()
