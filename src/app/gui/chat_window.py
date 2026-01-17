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
        self.parent = parent
        self.llm_client = None
        self.current_url = None
        self.clicker = clicker
        self.ai_controller = None
        
        # Поля для сценариев
        self.scenario_executor = None
        self.current_scenario = None
        self.scenario_file_path = None
        self.scenario_thread = None
        self._last_progress_step = 0
        self._last_progress_status = None
        
        # Создаем LLM клиент (через бэкенд)
        self.llm_client = self._create_llm_client()
        
        # Инициализируем AI контроллер для автоматизации (если есть clicker и клиент)
        if self.clicker and self.llm_client:
            try:
                self.ai_controller = AIController(self.clicker, llm_client=self.llm_client)
                print("[OK] AI контроллер для автоматизации инициализирован")
            except Exception as e:
                print(f"[WARNING] AI контроллер не настроен: {e}")
        
        self._create_window()

    def _create_window(self):
        """Создание или пересоздание окна чата"""
        if USE_CUSTOM_TKINTER:
            self.window = ctk.CTkToplevel(self.parent) if self.parent else ctk.CTk()
        else:
            self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()

        # Заголовок зависит от режима работы
        if self.clicker:
            self.window.title("Автоматизация сайта")
        else:
            self.window.title("Чат с ИИ")
        self.window.geometry("450x600")
        try:
            self.window.minsize(450, 600)
        except Exception:
            pass
        if USE_CUSTOM_TKINTER:
            self.window.configure(fg_color="#0f1115")
        else:
            self.window.configure(bg="#0f1115")

        self._create_widgets()
        self._bind_close_handler()
        self._bring_to_front()

    def _bind_close_handler(self):
        """Перехват закрытия окна, чтобы не разрушать его"""
        try:
            self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass

    def _on_close(self):
        """Обработка закрытия окна чата"""
        try:
            self.window.withdraw()
            if self.parent and not self.clicker:
                self.parent.deiconify()
        except Exception:
            pass
    
    def _create_widgets(self):
        """Создание виджетов"""
        if USE_CUSTOM_TKINTER:
            main_content = ctk.CTkFrame(self.window, fg_color="transparent")
            main_content.pack(padx=24, pady=22, fill="both", expand=True)
            
            # Заголовок
            title_text = "Автоматизация сайта" if self.clicker else "Чат с ассистентом"
            subtitle_text = ""
            
            header_card = ctk.CTkFrame(
                main_content,
                fg_color="#161a22",
                border_width=1,
                border_color="#2a3140",
                corner_radius=16
            )
            header_card.pack(fill="x", pady=(0, 16))
            header_card.pack_propagate(True)
            
            header_row = ctk.CTkFrame(header_card, fg_color="transparent")
            header_row.pack(fill="x", padx=20, pady=(14, 14))
            header_row.pack_propagate(True)
            header_row.grid_columnconfigure(0, weight=1)
            header_row.grid_columnconfigure(1, weight=0)
            header_row.grid_columnconfigure(2, weight=1)
            
            # Кнопку "Назад" в чате не показываем
            
            header_text = ctk.CTkFrame(header_row, fg_color="transparent")
            header_text.grid(row=0, column=1, sticky="nsew")
            header_text.pack_propagate(True)
            
            title = ctk.CTkLabel(
                header_text,
                text=title_text,
                font=ctk.CTkFont(size=26, weight="bold"),
                text_color="#f8fafc"
            )
            title.pack(anchor="center", pady=(2, 4))
            
            if subtitle_text:
                subtitle = ctk.CTkLabel(
                    header_text,
                    text=subtitle_text,
                    font=ctk.CTkFont(size=13),
                    text_color="#9aa4b2"
                )
                subtitle.pack(anchor="center")
            
            # Пустая колонка справа для центрирования текста
            
            # Фрейм управления сценариями (только для режима автоматизации)
            if self.clicker:
                scenario_card = ctk.CTkFrame(
                    main_content,
                    fg_color="#161a22",
                    border_width=1,
                    border_color="#2a3140",
                    corner_radius=16
                )
                scenario_card.pack(fill="x", pady=(0, 16))
                self._create_scenario_widgets_ctk(scenario_card)
            
            # Область чата
            chat_card = ctk.CTkFrame(
                main_content,
                fg_color="#161a22",
                border_width=1,
                border_color="#2a3140",
                corner_radius=16
            )
            chat_card.pack(fill="both", expand=True)
            
            self.chat_area = ctk.CTkTextbox(
                chat_card,
                font=ctk.CTkFont(size=12),
                fg_color="#0f1115",
                text_color="#e2e8f0"
            )
            self.chat_area.pack(pady=16, padx=16, fill="both", expand=True)
            
            # Поле ввода
            input_card = ctk.CTkFrame(
                main_content,
                fg_color="#161a22",
                border_width=1,
                border_color="#2a3140",
                corner_radius=16
            )
            input_card.pack(fill="x", pady=(16, 0))
            
            input_frame = ctk.CTkFrame(input_card, fg_color="transparent")
            input_frame.pack(padx=16, pady=14, fill="x")
            
            self.input_entry = ctk.CTkEntry(
                input_frame,
                placeholder_text="Введите сообщение...",
                font=ctk.CTkFont(size=12),
                fg_color="#0f1115",
                text_color="#e2e8f0",
                border_color="#2a3140"
            )
            self.input_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
            self.input_entry.bind("<Return>", lambda e: self._send_message())
            
            self.send_button = ctk.CTkButton(
                input_frame,
                text="Отправить",
                command=self._send_message,
                width=120,
                fg_color="#4c8bf5",
                hover_color="#3b76d8"
            )
            self.send_button.pack(side="right")
        else:
            # Обычный Tkinter
            main_content = tk.Frame(self.window, bg="#0f1115")
            main_content.pack(padx=24, pady=22, fill="both", expand=True)
            
            title_text = "Автоматизация сайта" if self.clicker else "Чат с ассистентом"
            subtitle_text = ""
            
            header_card = tk.Frame(
                main_content,
                bg="#161a22",
                highlightthickness=1,
                highlightbackground="#2a3140"
            )
            header_card.pack(fill="x", pady=(0, 16))
            header_card.pack_propagate(True)
            
            header_row = tk.Frame(header_card, bg="#161a22")
            header_row.pack(fill="x", padx=20, pady=(14, 14))
            header_row.pack_propagate(True)
            header_row.grid_columnconfigure(0, weight=1)
            header_row.grid_columnconfigure(1, weight=0)
            header_row.grid_columnconfigure(2, weight=1)
            
            # Кнопку "Назад" в чате не показываем
            
            header_text = tk.Frame(header_row, bg="#161a22")
            header_text.grid(row=0, column=1, sticky="nsew")
            header_text.pack_propagate(True)
            
            title = tk.Label(
                header_text,
                text=title_text,
                font=("Segoe UI", 22, "bold"),
                bg="#161a22",
                fg="#f8fafc"
            )
            title.pack(anchor="center", pady=(2, 4))
            
            if subtitle_text:
                subtitle = tk.Label(
                    header_text,
                    text=subtitle_text,
                    font=("Segoe UI", 11),
                    bg="#161a22",
                    fg="#9aa4b2"
                )
                subtitle.pack(anchor="center")
            
            # Пустая колонка справа для центрирования текста
            
            # Фрейм управления сценариями (только для режима автоматизации)
            if self.clicker:
                scenario_card = tk.Frame(
                    main_content,
                    bg="#161a22",
                    highlightthickness=1,
                    highlightbackground="#2a3140"
                )
                scenario_card.pack(fill="x", pady=(0, 16))
                self._create_scenario_widgets_tkinter(scenario_card)
            
            # Область чата
            chat_card = tk.Frame(
                main_content,
                bg="#161a22",
                highlightthickness=1,
                highlightbackground="#2a3140"
            )
            chat_card.pack(fill="both", expand=True)
            
            self.chat_area = scrolledtext.ScrolledText(
                chat_card,
                font=("Segoe UI", 11),
                bg="#0f1115",
                fg="#e2e8f0",
                insertbackground="white",
                wrap=tk.WORD
            )
            self.chat_area.pack(pady=16, padx=16, fill="both", expand=True)
            
            # Поле ввода
            input_card = tk.Frame(
                main_content,
                bg="#161a22",
                highlightthickness=1,
                highlightbackground="#2a3140"
            )
            input_card.pack(fill="x", pady=(16, 0))
            
            input_frame = tk.Frame(input_card, bg="#161a22")
            input_frame.pack(padx=16, pady=14, fill="x")
            
            self.input_entry = tk.Entry(
                input_frame,
                font=("Segoe UI", 12),
                bg="#0f1115",
                fg="#e2e8f0",
                insertbackground="white",
                relief="flat"
            )
            self.input_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)
            self.input_entry.bind("<Return>", lambda e: self._send_message())
            
            self.send_button = tk.Button(
                input_frame,
                text="Отправить",
                command=self._send_message,
                bg="#4c8bf5",
                fg="white",
                activebackground="#3b76d8",
                activeforeground="white",
                font=("Segoe UI", 12),
                relief="flat",
                cursor="hand2",
                width=12
            )
            self.send_button.pack(side="right")
    
    def _create_scenario_widgets_ctk(self, parent):
        """Создание виджетов управления сценариями (CustomTkinter)"""
        # Фрейм управления сценариями
        scenario_frame = ctk.CTkFrame(parent, fg_color="transparent")
        scenario_frame.pack(padx=16, pady=14, fill="x")
        
        # Кнопка "Перезагрузить сценарий"
        self.restart_scenario_btn = ctk.CTkButton(
            scenario_frame,
            text="Перезапустить",
            command=self._restart_scenario,
            width=150,
            fg_color="#3b4758",
            hover_color="#334052",
            state="disabled"
        )
        self.restart_scenario_btn.pack(side="left", padx=5)
        
        # Кнопка "Остановить сценарий" (скрыта по умолчанию)
        self.stop_scenario_btn = ctk.CTkButton(
            scenario_frame,
            text="Остановить",
            command=self._stop_scenario,
            width=120,
            fg_color="red",
            hover_color="darkred"
        )
        self.stop_scenario_btn.pack(side="left", padx=5)
        self.stop_scenario_btn.configure(state="disabled")
        
        # Индикатор прогресса
        self.progress_label = ctk.CTkLabel(
            scenario_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#9aa4b2"
        )
        self.progress_label.pack(side="left", padx=10, fill="x", expand=True)
    
    def _create_scenario_widgets_tkinter(self, parent):
        """Создание виджетов управления сценариями (Tkinter)"""
        # Фрейм управления сценариями
        scenario_frame = tk.Frame(parent, bg="#161a22")
        scenario_frame.pack(padx=16, pady=14, fill="x")
        
        # Кнопка "Перезагрузить сценарий"
        self.restart_scenario_btn = tk.Button(
            scenario_frame,
            text="Перезапустить",
            command=self._restart_scenario,
            bg="#3b4758",
            fg="white",
            font=("Segoe UI", 11),
            width=16,
            relief="flat",
            cursor="hand2",
            activebackground="#334052",
            activeforeground="white",
            state="disabled"
        )
        self.restart_scenario_btn.pack(side="left", padx=5)
        
        # Кнопка "Остановить сценарий"
        self.stop_scenario_btn = tk.Button(
            scenario_frame,
            text="Остановить",
            command=self._stop_scenario,
            bg="red",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=15,
            relief="flat",
            cursor="hand2",
            activebackground="darkred",
            activeforeground="white",
            state="disabled"
        )
        self.stop_scenario_btn.pack(side="left", padx=5)
        
        # Индикатор прогресса
        self.progress_label = tk.Label(
            scenario_frame,
            text="",
            font=("Segoe UI", 11),
            bg="#161a22",
            fg="#9aa4b2",
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
        
        if self._handle_user_wait_input(message):
            return
        
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
    
    def _handle_user_wait_input(self, message: str) -> bool:
        """Передает ввод пользователя сценарному ожиданию, если оно активно."""
        if not self.scenario_executor or not self.scenario_executor.is_waiting_for_user():
            return False
        
        try:
            self.scenario_executor.provide_user_input(message)
            self._add_message("✅ Ответ получен, продолжаю сценарий.", is_user=False)
        except Exception as e:
            self._add_message(f"❌ Ошибка передачи ответа: {str(e)}", is_user=False)
        finally:
            self.send_button.configure(state="normal" if USE_CUSTOM_TKINTER else "normal")
        return True
    
    def _load_scenario(self):
        """Загрузка файла сценария через диалог"""
        try:
            file_path = filedialog.askopenfilename(
                title="Выберите файл сценария",
                filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
            )
            
            if not file_path:
                return
            
            self._load_scenario_from_path(file_path)
                
        except Exception as e:
            self._add_message(f"❌ Неожиданная ошибка: {str(e)}", is_user=False)
    
    def _restart_scenario(self):
        """Перезапуск текущего сценария"""
        if not self.scenario_file_path:
            self._add_message("❌ Нет загруженного сценария для перезапуска.", is_user=False)
            return
        
        if self.scenario_executor:
            self._stop_scenario()
            if USE_CUSTOM_TKINTER:
                self.window.after(200, self._run_scenario)
            else:
                self.window.after(200, self._run_scenario)
        else:
            self._run_scenario()
    
    def _load_scenario_from_path(self, file_path: str):
        """Загрузка сценария по пути"""
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
        
        # Включаем кнопку перезагрузки
        if USE_CUSTOM_TKINTER:
            self.restart_scenario_btn.configure(state="normal")
        else:
            self.restart_scenario_btn.configure(state="normal")
    
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
        self.scenario_executor.set_message_callback(self._on_scenario_message)
        
        # Изменяем состояние кнопок
        if USE_CUSTOM_TKINTER:
            self.restart_scenario_btn.configure(state="disabled")
            # Показываем кнопку остановки (pack перед progress_label)
            self.progress_label.pack_forget()
            self.progress_label.pack(side="left", padx=10, fill="x", expand=True)
            self.stop_scenario_btn.configure(state="normal")
        else:
            self.restart_scenario_btn.configure(state="disabled")
            # Показываем кнопку остановки (pack перед progress_label)
            self.progress_label.pack_forget()
            self.progress_label.pack(side="left", padx=10, fill="x", expand=True)
            self.stop_scenario_btn.configure(state="normal")
        
        # Показываем информацию о запуске
        self._last_progress_step = 0
        self._last_progress_status = None
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
            if status.startswith("Цикл:"):
                return
            if current != self._last_progress_step or status != self._last_progress_status:
                self._add_message(f"➡ Шаг {current}/{total}: {status}", is_user=False)
                self._last_progress_step = current
                self._last_progress_status = status
        
        # Обновляем UI в главном потоке
        if USE_CUSTOM_TKINTER:
            self.window.after(0, update_ui)
        else:
            self.window.after(0, update_ui)

    def _on_scenario_message(self, message: str):
        """Сообщение от сценария (данные/ответ AI)"""
        def update_ui():
            self._add_message(message, is_user=False)
        
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
                self.restart_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.progress_label.configure(text="")
                self.stop_scenario_btn.configure(state="disabled")
            else:
                self.restart_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.progress_label.configure(text="")
                self.stop_scenario_btn.configure(state="disabled")
            
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
                self.restart_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.progress_label.configure(text="")
                self.stop_scenario_btn.configure(state="disabled")
            else:
                self.restart_scenario_btn.configure(state="normal" if self.current_scenario else "disabled")
                self.progress_label.configure(text="")
                self.stop_scenario_btn.configure(state="disabled")
            
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
        try:
            if self.parent and not self.clicker:
                self.parent.deiconify()
        except Exception:
            pass
    
    def show(self):
        """Показать окно"""
        if not self._is_window_alive():
            self._create_window()
            return
        self.window.deiconify()
        self._bring_to_front()

    def _is_window_alive(self) -> bool:
        """Проверка, что окно существует и не уничтожено"""
        try:
            return bool(self.window.winfo_exists())
        except Exception:
            return False

    def _bring_to_front(self):
        """Поднять окно поверх главного"""
        try:
            if self.window.master and not self.clicker:
                self.window.transient(self.window.master)
        except Exception:
            pass
        try:
            self.window.lift()
            self.window.focus_force()
            # Briefly toggle topmost to ensure it appears above the main window
            self.window.attributes("-topmost", True)
            self.window.after(200, lambda: self.window.attributes("-topmost", False))
        except Exception:
            pass
