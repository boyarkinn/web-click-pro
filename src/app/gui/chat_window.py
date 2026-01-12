"""
Окно чата с GPT для анализа сайтов
"""

import sys
import os

# Пробуем использовать CustomTkinter
try:
    import customtkinter as ctk
    USE_CUSTOM_TKINTER = True
except ImportError:
    import tkinter as tk
    from tkinter import scrolledtext
    USE_CUSTOM_TKINTER = False

# Импорт AI клиента
from app.ai.openai_client import OpenAIClient


class ChatWindow:
    """Окно чата с GPT"""
    
    def __init__(self, parent=None):
        """Инициализация окна чата"""
        self.ai_client = None
        self.current_url = None
        
        try:
            self.ai_client = OpenAIClient()
        except ValueError as e:
            print(f"[WARNING] OpenAI не настроен: {e}")
        
        if USE_CUSTOM_TKINTER:
            self.window = ctk.CTkToplevel(parent) if parent else ctk.CTk()
        else:
            self.window = tk.Toplevel(parent) if parent else tk.Tk()
        
        self.window.title("GPT Анализ сайта")
        self.window.geometry("600x500")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        if USE_CUSTOM_TKINTER:
            # Заголовок
            title = ctk.CTkLabel(
                self.window,
                text="GPT Анализ",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title.pack(pady=10)
            
            # Область чата
            self.chat_area = ctk.CTkTextbox(
                self.window,
                height=350,
                font=ctk.CTkFont(size=12)
            )
            self.chat_area.pack(pady=10, padx=10, fill="both", expand=True)
            
            # Поле ввода
            input_frame = ctk.CTkFrame(self.window)
            input_frame.pack(pady=10, padx=10, fill="x")
            
            self.input_entry = ctk.CTkEntry(
                input_frame,
                placeholder_text="Введите вопрос...",
                font=ctk.CTkFont(size=12)
            )
            self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
            self.input_entry.bind("<Return>", lambda e: self._send_message())
            
            self.send_button = ctk.CTkButton(
                input_frame,
                text="Отправить",
                command=self._send_message,
                width=100
            )
            self.send_button.pack(side="right", padx=5)
        else:
            # Обычный Tkinter
            title = tk.Label(
                self.window,
                text="GPT Анализ",
                font=("Arial", 20, "bold"),
                bg="#2b2b2b",
                fg="white"
            )
            title.pack(pady=10)
            
            # Область чата
            self.chat_area = scrolledtext.ScrolledText(
                self.window,
                height=20,
                width=70,
                font=("Arial", 11),
                bg="#1e1e1e",
                fg="white",
                wrap=tk.WORD
            )
            self.chat_area.pack(pady=10, padx=10, fill="both", expand=True)
            
            # Поле ввода
            input_frame = tk.Frame(self.window, bg="#2b2b2b")
            input_frame.pack(pady=10, padx=10, fill="x")
            
            self.input_entry = tk.Entry(
                input_frame,
                font=("Arial", 12),
                bg="#3b3b3b",
                fg="white",
                insertbackground="white"
            )
            self.input_entry.pack(side="left", padx=5, fill="x", expand=True)
            self.input_entry.bind("<Return>", lambda e: self._send_message())
            
            self.send_button = tk.Button(
                input_frame,
                text="Отправить",
                command=self._send_message,
                bg="#0078d4",
                fg="white",
                font=("Arial", 12)
            )
            self.send_button.pack(side="right", padx=5)
    
    def _add_message(self, message: str, is_user: bool = False):
        """Добавление сообщения в чат"""
        if USE_CUSTOM_TKINTER:
            self.chat_area.insert("end", f"{'Вы' if is_user else 'GPT'}: {message}\n\n")
            self.chat_area.see("end")
        else:
            tag = "user" if is_user else "gpt"
            self.chat_area.insert("end", f"{'Вы' if is_user else 'GPT'}: {message}\n\n", tag)
            self.chat_area.tag_config("user", foreground="#4CAF50")
            self.chat_area.tag_config("gpt", foreground="#2196F3")
            self.chat_area.see("end")
    
    def _send_message(self):
        """Отправка сообщения"""
        if not self.ai_client:
            self._add_message("Ошибка: OpenAI не настроен. Проверьте OPENAI_API_KEY", is_user=False)
            return
        
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self._add_message(message, is_user=True)
        self.input_entry.delete(0, "end")
        self.send_button.configure(state="disabled" if USE_CUSTOM_TKINTER else "disabled")
        
        try:
            response = self.ai_client.chat(message)
            if response:
                self._add_message(response, is_user=False)
            else:
                self._add_message("Ошибка при получении ответа от GPT", is_user=False)
        except Exception as e:
            self._add_message(f"Ошибка: {str(e)}", is_user=False)
        finally:
            self.send_button.configure(state="normal" if USE_CUSTOM_TKINTER else "normal")
    
    def analyze_website(self, screenshot_path: str, url: str):
        """Анализ сайта через GPT"""
        if not self.ai_client:
            self._add_message("Ошибка: OpenAI не настроен", is_user=False)
            return
        
        self.current_url = url
        self._add_message(f"Анализирую сайт: {url}...", is_user=False)
        
        try:
            prompt = (
                "Ты видишь скриншот веб-сайта. Опиши подробно:\n"
                "1. Какой это сайт (название, тип)\n"
                "2. Что на нем изображено\n"
                "3. Для чего этот сайт предназначен\n"
                "4. Какие основные функции/возможности видны\n"
                "5. Общее впечатление и оценка дизайна\n\n"
                "Будь конкретным и детальным."
            )
            
            response = self.ai_client.analyze_image(screenshot_path, prompt)
            
            if response:
                self._add_message(f"Анализ сайта {url}:\n\n{response}", is_user=False)
            else:
                self._add_message("Не удалось проанализировать сайт", is_user=False)
        except Exception as e:
            self._add_message(f"Ошибка при анализе: {str(e)}", is_user=False)
    
    def show(self):
        """Показать окно"""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
