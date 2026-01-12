"""
Окно команд для автоматизации сайтов
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

# Импорт локального LLM клиента
try:
    from app.ai.local_llm_client import LocalLLMClient, create_local_llm_client
    LOCAL_LLM_AVAILABLE = True
except ImportError:
    LOCAL_LLM_AVAILABLE = False

# Импорт automation
from app.automation.ai_controller import AIController
from app.core.clicker import WebClicker


class ChatWindow:
    """Окно команд для автоматизации сайтов"""
    
    def __init__(self, parent=None, clicker: WebClicker = None):
        """Инициализация окна чата"""
        self.llm_client = None
        self.current_url = None
        self.clicker = clicker
        self.ai_controller = None
        
        # Создаем локальный LLM клиент
        if LOCAL_LLM_AVAILABLE:
            try:
                self.llm_client = create_local_llm_client()
                if self.llm_client:
                    print("[OK] Локальный LLM клиент инициализирован")
                else:
                    print("[WARNING] Не удалось создать локальный LLM клиент")
            except Exception as e:
                print(f"[WARNING] Ошибка при создании локального LLM клиента: {e}")
        else:
            print("[ERROR] Локальный LLM клиент недоступен. Установите: pip install torch transformers")
        
        # Инициализируем AI контроллер для автоматизации (если есть clicker и локальный клиент)
        if self.clicker and self.llm_client:
            try:
                self.ai_controller = AIController(self.clicker, llm_client=self.llm_client)
                print("[OK] AI контроллер для автоматизации инициализирован")
            except Exception as e:
                print(f"[WARNING] AI контроллер не настроен: {e}")
        
        if USE_CUSTOM_TKINTER:
            self.window = ctk.CTkToplevel(parent) if parent else ctk.CTk()
        else:
            self.window = tk.Toplevel(parent) if parent else tk.Tk()
        
        self.window.title("Автоматизация сайта")
        self.window.geometry("600x500")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        if USE_CUSTOM_TKINTER:
            # Заголовок
            title = ctk.CTkLabel(
                self.window,
                text="Автоматизация сайта",
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
                text="Автоматизация сайта",
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
            self.chat_area.insert("end", f"{'Вы' if is_user else 'Система'}: {message}\n\n")
            self.chat_area.see("end")
        else:
            tag = "user" if is_user else "gpt"
            self.chat_area.insert("end", f"{'Вы' if is_user else 'GPT'}: {message}\n\n", tag)
            self.chat_area.tag_config("user", foreground="#4CAF50")
            self.chat_area.tag_config("gpt", foreground="#2196F3")
            self.chat_area.see("end")
    
    def _send_message(self):
        """Обработка команды пользователя через систему автоматизации"""
        if not self.ai_controller:
            self._add_message("⚠ Ошибка: Локальная модель не настроена. Проверьте установку локальной модели (pip install torch transformers)", is_user=False)
            return
        
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self._add_message(message, is_user=True)
        self.input_entry.delete(0, "end")
        self.send_button.configure(state="disabled" if USE_CUSTOM_TKINTER else "disabled")
        
        # Проверяем доступность автоматизации
        automation_available = (
            self.ai_controller is not None and 
            self.clicker is not None and 
            self.clicker.driver is not None
        )
        
        if not automation_available:
            self._add_message("⚠ Автоматизация недоступна. Убедитесь, что браузер открыт и сайт загружен.", is_user=False)
            self.send_button.configure(state="normal" if USE_CUSTOM_TKINTER else "normal")
            return
        
        try:
            # Все команды обрабатываем через систему автоматизации
            self._add_message("🔄 Обрабатываю команду...", is_user=False)
            result = self.ai_controller.process_user_instruction(message)
            
            if result["success"]:
                # Команда выполнена успешно
                self._add_message(f"✅ {result['message']}", is_user=False)
                if result.get("result"):
                    self._add_message(f"Результат: {result['result']}", is_user=False)
            else:
                # Произошла ошибка
                error_msg = result.get("message", "Неизвестная ошибка")
                
                # Если ИИ вернул объяснение ошибки (через поле error в JSON)
                if result.get("error_explanation"):
                    self._add_message(f"❌ {result['error_explanation']}", is_user=False)
                else:
                    self._add_message(f"❌ Ошибка: {error_msg}", is_user=False)
                    
        except Exception as e:
            self._add_message(f"❌ Ошибка: {str(e)}", is_user=False)
        finally:
            self.send_button.configure(state="normal" if USE_CUSTOM_TKINTER else "normal")
    
    def show(self):
        """Показать окно"""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
