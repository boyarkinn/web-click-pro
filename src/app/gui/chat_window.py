"""
Окно команд для автоматизации сайтов
"""

import sys
import os
import threading
from tkinter import filedialog

# Пробуем использовать CustomTkinter
try:
    import customtkinter as ctk
    USE_CUSTOM_TKINTER = True
except ImportError:
    import tkinter as tk
    from tkinter import scrolledtext
    USE_CUSTOM_TKINTER = False

# Импорт LLM клиентов
from app.ai.remote_llm_client import RemoteLLMClient

# Импорт automation
from app.automation.ai_controller import AIController
from app.core.clicker import WebClicker

# Импорт сценариев
from app.scenarios.parser import ScenarioParser
from app.scenarios.executor import ScenarioExecutor


class ChatWindow:
    """Окно команд для автоматизации сайтов"""
    
    def __init__(self, parent=None, clicker: WebClicker = None):
        """Инициализация окна чата"""
        self.llm_client = None
        self.current_url = None
        self.clicker = clicker
        self.ai_controller = None
        
        # Поля для сценариев
        self.scenario_executor = None
        self.current_scenario = None
        self.scenario_file_path = None
        self.scenario_thread = None
        
        # Создаем LLM клиент (через бэкенд)
        self.llm_client = self._create_llm_client()
        
        # Инициализируем AI контроллер для автоматизации (если есть clicker и клиент)
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
        
        # Заголовок зависит от режима работы
        if clicker:
            self.window.title("Автоматизация сайта")
        else:
            self.window.title("Чат с ИИ")
        self.window.geometry("600x500")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создание виджетов"""
        if USE_CUSTOM_TKINTER:
            # Заголовок
            title_text = "Автоматизация сайта" if self.clicker else "Чат с ИИ"
            title = ctk.CTkLabel(
                self.window,
                text=title_text,
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title.pack(pady=10)
            
            # Фрейм управления сценариями (только для режима автоматизации)
            if self.clicker:
                self._create_scenario_widgets_ctk()
            
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
            
            # Кнопка "Назад"
            self.back_button = ctk.CTkButton(
                self.window,
                text="Назад",
                font=ctk.CTkFont(size=14),
                height=35,
                command=self._go_back,
                fg_color="gray",
                hover_color="darkgray"
            )
            self.back_button.pack(pady=(0, 10), padx=10, fill="x")
        else:
            # Обычный Tkinter
            title_text = "Автоматизация сайта" if self.clicker else "Чат с ИИ"
            title = tk.Label(
                self.window,
                text=title_text,
                font=("Arial", 20, "bold"),
                bg="#2b2b2b",
                fg="white"
            )
            title.pack(pady=10)
            
            # Фрейм управления сценариями (только для режима автоматизации)
            if self.clicker:
                self._create_scenario_widgets_tkinter()
            
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
            
            # Кнопка "Назад"
            self.back_button = tk.Button(
                self.window,
                text="Назад",
                font=("Arial", 14),
                bg="gray",
                fg="white",
                activebackground="darkgray",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                command=self._go_back
            )
            self.back_button.pack(pady=(0, 10), padx=10, fill="x", ipady=6)
    
    def _create_scenario_widgets_ctk(self):
        """Создание виджетов управления сценариями (CustomTkinter)"""
        # Фрейм управления сценариями
        scenario_frame = ctk.CTkFrame(self.window)
        scenario_frame.pack(pady=5, padx=10, fill="x")
        
        # Кнопка "Загрузить сценарий"
        self.load_scenario_btn = ctk.CTkButton(
            scenario_frame,
            text="Загрузить сценарий",
            command=self._load_scenario,
            width=150
        )
        self.load_scenario_btn.pack(side="left", padx=5)
        
        # Кнопка "Запустить сценарий"
        self.run_scenario_btn = ctk.CTkButton(
            scenario_frame,
            text="Запустить сценарий",
            command=self._run_scenario,
            width=150,
            state="disabled"
        )
        self.run_scenario_btn.pack(side="left", padx=5)
        
        # Кнопка "Остановить сценарий" (скрыта по умолчанию)
        self.stop_scenario_btn = ctk.CTkButton(
            scenario_frame,
            text="Остановить",
            command=self._stop_scenario,
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        # Не pack-им сразу, будет показываться при запуске
        
        # Индикатор прогресса
        self.progress_label = ctk.CTkLabel(
            scenario_frame,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.progress_label.pack(side="left", padx=10, fill="x", expand=True)
    
    def _create_scenario_widgets_tkinter(self):
        """Создание виджетов управления сценариями (Tkinter)"""
        # Фрейм управления сценариями
        scenario_frame = tk.Frame(self.window, bg="#2b2b2b")
        scenario_frame.pack(pady=5, padx=10, fill="x")
        
        # Кнопка "Загрузить сценарий"
        self.load_scenario_btn = tk.Button(
            scenario_frame,
            text="Загрузить сценарий",
            command=self._load_scenario,
            bg="#0078d4",
            fg="white",
            font=("Arial", 11),
            width=18
        )
        self.load_scenario_btn.pack(side="left", padx=5)
        
        # Кнопка "Запустить сценарий"
        self.run_scenario_btn = tk.Button(
            scenario_frame,
            text="Запустить сценарий",
            command=self._run_scenario,
            bg="#0078d4",
            fg="white",
            font=("Arial", 11),
            width=18,
            state="disabled"
        )
        self.run_scenario_btn.pack(side="left", padx=5)
        
        # Кнопка "Остановить сценарий" (скрыта по умолчанию)
        self.stop_scenario_btn = tk.Button(
            scenario_frame,
            text="Остановить",
            command=self._stop_scenario,
            bg="red",
            fg="white",
            font=("Arial", 11),
            width=15
        )
        # Не pack-им сразу, будет показываться при запуске
        
        # Индикатор прогресса
        self.progress_label = tk.Label(
            scenario_frame,
            text="",
            font=("Arial", 11),
            bg="#2b2b2b",
            fg="gray",
            anchor="w"
        )
        self.progress_label.pack(side="left", padx=10, fill="x", expand=True)
    
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
        """Обработка сообщения пользователя"""
        message = self.input_entry.get().strip()
        if not message:
            return
        
        # Проверяем наличие клиента
        if not self.llm_client:
            self._add_message("⚠ Ошибка: AI сервер недоступен. Проверьте API_BASE_URL и что бэкенд запущен.", is_user=False)
            return
        
        self._add_message(message, is_user=True)
        self.input_entry.delete(0, "end")
        self.send_button.configure(state="disabled" if USE_CUSTOM_TKINTER else "disabled")
        
        # Режим работы зависит от наличия clicker
        if self.clicker and self.ai_controller:
            # Режим автоматизации
            self._send_automation_message(message)
        else:
            # Режим простого чата
            self._send_chat_message(message)
    
    def _send_automation_message(self, message: str):
        """Отправка сообщения в режиме автоматизации"""
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
    
    def _send_chat_message(self, message: str):
        """Отправка сообщения в режиме простого чата"""
        try:
            self._add_message("🔄 Думаю...", is_user=False)
            
            # Простой чат с моделью
            response = self.llm_client.chat(
                message,
                system_prompt="Ты полезный помощник. Отвечай кратко и по делу.",
                max_tokens=500
            )
            
            if response:
                self._add_message(response, is_user=False)
            else:
                self._add_message("❌ Не удалось получить ответ от модели", is_user=False)
                
        except Exception as e:
            self._add_message(f"❌ Ошибка: {str(e)}", is_user=False)
        finally:
            self.send_button.configure(state="normal" if USE_CUSTOM_TKINTER else "normal")
    
    def _load_scenario(self):
        """Загрузка файла сценария через диалог"""
        try:
            file_path = filedialog.askopenfilename(
                title="Выберите файл сценария",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            
            if not file_path:
                return
            
            # Загрузка и парсинг сценария
            try:
                json_data = ScenarioParser.load_from_file(file_path)
            except FileNotFoundError as e:
                self._add_message(f"❌ Файл не найден: {str(e)}", is_user=False)
                return
            except ValueError as e:
                # Ошибка парсинга JSON
                self._add_message(f"❌ Ошибка парсинга JSON: {str(e)}", is_user=False)
                return
            except Exception as e:
                self._add_message(f"❌ Ошибка загрузки файла: {str(e)}", is_user=False)
                return
            
            try:
                scenario = ScenarioParser.parse(json_data)
            except ValueError as e:
                # Ошибка парсинга структуры
                self._add_message(f"❌ Ошибка парсинга сценария: {str(e)}", is_user=False)
                return
            
            # Валидация сценария
            from app.scenarios.validator import ScenarioValidator
            is_valid, error = ScenarioValidator.validate(scenario)
            if not is_valid:
                # Ошибка валидации - показываем список проблем
                self._add_message(f"❌ Ошибка валидации сценария:", is_user=False)
                # Разбиваем ошибки по строкам (если их несколько)
                errors = error.split('; ')
                for err in errors:
                    if err.strip():
                        self._add_message(f"  • {err.strip()}", is_user=False)
                return
            
            self.current_scenario = scenario
            self.scenario_file_path = file_path
            
            # Обновление UI
            scenario_name = scenario.get('name', 'Неизвестный сценарий')
            self._add_message(f"✅ Сценарий загружен: {scenario_name}", is_user=False)
            
            # Включаем кнопку запуска
            if USE_CUSTOM_TKINTER:
                self.run_scenario_btn.configure(state="normal")
            else:
                self.run_scenario_btn.configure(state="normal")
                
        except Exception as e:
            self._add_message(f"❌ Неожиданная ошибка: {str(e)}", is_user=False)
    
    def _run_scenario(self):
        """Запуск сценария"""
        if not self.current_scenario:
            self._add_message("❌ Сценарий не загружен", is_user=False)
            return
        
        if not self.ai_controller or not self.clicker:
            self._add_message("❌ Автоматизация недоступна. Убедитесь, что браузер открыт.", is_user=False)
            return
        
        # Создаем исполнитель сценария
        self.scenario_executor = ScenarioExecutor(self.ai_controller, self.clicker)
        
        # Устанавливаем callbacks
        self.scenario_executor.set_progress_callback(self._update_progress)
        self.scenario_executor.set_complete_callback(self._on_scenario_complete)
        self.scenario_executor.set_error_callback(self._on_scenario_error)
        
        # Изменяем состояние кнопок
        if USE_CUSTOM_TKINTER:
            self.run_scenario_btn.configure(state="disabled")
            self.load_scenario_btn.configure(state="disabled")
            # Показываем кнопку остановки (pack перед progress_label)
            self.progress_label.pack_forget()
            self.stop_scenario_btn.pack(side="left", padx=5)
            self.progress_label.pack(side="left", padx=10, fill="x", expand=True)
            self.stop_scenario_btn.configure(state="normal")
        else:
            self.run_scenario_btn.configure(state="disabled")
            self.load_scenario_btn.configure(state="disabled")
            # Показываем кнопку остановки (pack перед progress_label)
            self.progress_label.pack_forget()
            self.stop_scenario_btn.pack(side="left", padx=5)
            self.progress_label.pack(side="left", padx=10, fill="x", expand=True)
            self.stop_scenario_btn.configure(state="normal")
        
        # Показываем информацию о запуске
        scenario_name = self.current_scenario.get('name', 'Неизвестный сценарий')
        self._add_message(f"🚀 Запуск сценария: {scenario_name}", is_user=False)
        
        # Запускаем выполнение в отдельном потоке
        self.scenario_thread = threading.Thread(target=self._execute_scenario_thread, daemon=True)
        self.scenario_thread.start()
    
    def _execute_scenario_thread(self):
        """Выполнение сценария в отдельном потоке"""
        try:
            self.scenario_executor.execute(self.current_scenario)
        except Exception as e:
            self._on_scenario_error(f"Ошибка выполнения сценария: {str(e)}")
    
    def _stop_scenario(self):
        """Остановка выполнения сценария"""
        if self.scenario_executor:
            self.scenario_executor.stop()
            self._add_message("⏹ Остановка сценария...", is_user=False)
    
    def _update_progress(self, current: int, total: int, status: str):
        """Обновление индикатора прогресса"""
        def update_ui():
            progress_text = f"Шаг {current} из {total}: {status}"
            if USE_CUSTOM_TKINTER:
                self.progress_label.configure(text=progress_text)
            else:
                self.progress_label.configure(text=progress_text)
        
        # Обновляем UI в главном потоке
        if USE_CUSTOM_TKINTER:
            self.window.after(0, update_ui)
        else:
            self.window.after(0, update_ui)
    
    def _on_scenario_complete(self, stopped: bool, message: str):
        """Обработка завершения сценария"""
        def update_ui():
            if stopped:
                self._add_message(f"⏹ {message}", is_user=False)
            else:
                self._add_message(f"✅ {message}", is_user=False)
            
            # Сбрасываем состояние кнопок
            if USE_CUSTOM_TKINTER:
                self.run_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.load_scenario_btn.configure(state="normal")
                self.stop_scenario_btn.pack_forget()
                self.progress_label.configure(text="")
            else:
                self.run_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.load_scenario_btn.configure(state="normal")
                self.stop_scenario_btn.pack_forget()
                self.progress_label.configure(text="")
            
            self.scenario_executor = None
            self.scenario_thread = None
        
        # Обновляем UI в главном потоке
        if USE_CUSTOM_TKINTER:
            self.window.after(0, update_ui)
        else:
            self.window.after(0, update_ui)
    
    def _on_scenario_error(self, error: str):
        """Обработка ошибки сценария"""
        def update_ui():
            self._add_message(f"❌ {error}", is_user=False)
            
            # Сбрасываем состояние кнопок
            if USE_CUSTOM_TKINTER:
                self.run_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.load_scenario_btn.configure(state="normal")
                self.stop_scenario_btn.pack_forget()
                self.progress_label.configure(text="")
            else:
                self.run_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.load_scenario_btn.configure(state="normal")
                self.stop_scenario_btn.pack_forget()
                self.progress_label.configure(text="")
            
            self.scenario_executor = None
            self.scenario_thread = None
        
        # Обновляем UI в главном потоке
        if USE_CUSTOM_TKINTER:
            self.window.after(0, update_ui)
        else:
            self.window.after(0, update_ui)
    
    def _create_llm_client(self):
        """Создание LLM клиента (через бэкенд)"""
        try:
            client = RemoteLLMClient()
            if client.is_available():
                print("[OK] AI клиент через бэкенд инициализирован")
                return client
            print("[WARNING] AI сервер недоступен (health_check не прошел)")
        except Exception as e:
            print(f"[WARNING] Ошибка при создании AI клиента: {e}")

        return None
    
    def _go_back(self):
        """Вернуться назад (скрыть окно чата)"""
        self.window.withdraw()  # Скрываем окно
    
    def show(self):
        """Показать окно"""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()
