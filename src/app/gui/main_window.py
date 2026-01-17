"""
Главное окно приложения
"""

import sys
import os
import time

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
# Импорт чата
from app.gui.chat_window import ChatWindow
# Импорт для работы с файлами
from tkinter import filedialog
# Импорт сценариев
from app.scenarios.parser import ScenarioParser


class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self):
        """Инициализация главного окна"""
        # Инициализация кликера
        self.clicker = None
        # Окна
        self.chat_window = None
        self.simple_chat_window = None
        # Выбранный сценарий
        self.selected_scenario = None
        self.selected_scenario_path = None
        
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
        # Используем заданный размер (800x600) вместо реального размера окна
        width = 800
        height = 600
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
        
        # Фрейм для кнопок выбора режима
        self.mode_frame = ctk.CTkFrame(self.root)
        self.mode_frame.pack(pady=50, padx=40, fill="x")
        
        # Кнопка "Запустить сценарий"
        self.run_scenario_entry_button = ctk.CTkButton(
            self.mode_frame,
            text="Запустить сценарий",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            command=self._show_scenario_input
        )
        self.run_scenario_entry_button.pack(pady=20, padx=40, fill="x")
        
        # Кнопка "Чат"
        self.chat_button = ctk.CTkButton(
            self.mode_frame,
            text="Чат",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            command=self._open_simple_chat,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.chat_button.pack(pady=20, padx=40, fill="x")
        
        # Фрейм для выбора сценария (скрыт по умолчанию)
        self.scenario_input_frame = ctk.CTkFrame(self.root)
        self.scenario_input_frame.pack_forget()  # Скрыт по умолчанию
        
        # Метка для выбора сценария
        scenario_label = ctk.CTkLabel(
            self.scenario_input_frame,
            text="Выберите сценарий:",
            font=ctk.CTkFont(size=14)
        )
        scenario_label.pack(pady=(20, 10), padx=20)
        
        # Метка выбранного сценария
        self.scenario_info_label = ctk.CTkLabel(
            self.scenario_input_frame,
            text="Сценарий не выбран",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.scenario_info_label.pack(pady=(0, 10), padx=20)
        
        # Фрейм для кнопок сценария
        scenario_buttons_frame = ctk.CTkFrame(self.scenario_input_frame, fg_color="transparent")
        scenario_buttons_frame.pack(pady=10, padx=20, fill="x")
        
        # Кнопка выбора сценария
        self.select_scenario_button = ctk.CTkButton(
            scenario_buttons_frame,
            text="Выбрать сценарий",
            font=ctk.CTkFont(size=14),
            height=35,
            command=self._select_scenario,
            width=150
        )
        self.select_scenario_button.pack(side="left", padx=(0, 10))
        
        # Кнопка запуска сценария
        self.run_scenario_button = ctk.CTkButton(
            scenario_buttons_frame,
            text="Запустить сценарий",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=35,
            command=self._run_scenario_from_main,
            width=150,
            state="disabled",
            fg_color="green",
            hover_color="darkgreen"
        )
        self.run_scenario_button.pack(side="left")
        
        # Кнопка "Назад"
        self.scenario_back_button = ctk.CTkButton(
            self.scenario_input_frame,
            text="Назад",
            font=ctk.CTkFont(size=14),
            height=35,
            command=self._show_main_menu,
            fg_color="gray",
            hover_color="darkgray"
        )
        self.scenario_back_button.pack(pady=(0, 20), padx=20, fill="x")
        
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
        
        # Фрейм для кнопок выбора режима
        self.mode_frame = tk.Frame(self.root, bg="#2b2b2b")
        self.mode_frame.pack(pady=50, padx=40, fill="x")
        
        # Кнопка "Запустить сценарий"
        self.run_scenario_entry_button = tk.Button(
            self.mode_frame,
            text="Запустить сценарий",
            font=("Arial", 18, "bold"),
            bg="#0078d4",
            fg="white",
            activebackground="#005a9e",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._show_scenario_input
        )
        self.run_scenario_entry_button.pack(pady=20, padx=40, fill="x", ipady=10)
        
        # Кнопка "Чат"
        self.chat_button = tk.Button(
            self.mode_frame,
            text="Чат",
            font=("Arial", 18, "bold"),
            bg="green",
            fg="white",
            activebackground="darkgreen",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._open_simple_chat
        )
        self.chat_button.pack(pady=20, padx=40, fill="x", ipady=10)
        
        # Фрейм для выбора сценария (скрыт по умолчанию)
        self.scenario_input_frame = tk.Frame(self.root, bg="#2b2b2b")
        
        # Метка для выбора сценария
        scenario_label = tk.Label(
            self.scenario_input_frame,
            text="Выберите сценарий:",
            font=("Arial", 14),
            bg="#2b2b2b",
            fg="white"
        )
        scenario_label.pack(pady=(20, 10), padx=20)
        
        # Метка выбранного сценария
        self.scenario_info_label = tk.Label(
            self.scenario_input_frame,
            text="Сценарий не выбран",
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="gray"
        )
        self.scenario_info_label.pack(pady=(0, 10), padx=20)
        
        # Фрейм для кнопок сценария
        scenario_buttons_frame = tk.Frame(self.scenario_input_frame, bg="#2b2b2b")
        scenario_buttons_frame.pack(pady=10, padx=20, fill="x")
        
        # Кнопка выбора сценария
        self.select_scenario_button = tk.Button(
            scenario_buttons_frame,
            text="Выбрать сценарий",
            font=("Arial", 12),
            bg="#0078d4",
            fg="white",
            activebackground="#005a9e",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._select_scenario,
            width=18,
            height=2
        )
        self.select_scenario_button.pack(side="left", padx=(0, 10))
        
        # Кнопка запуска сценария
        self.run_scenario_button = tk.Button(
            scenario_buttons_frame,
            text="Запустить сценарий",
            font=("Arial", 12, "bold"),
            bg="green",
            fg="white",
            activebackground="darkgreen",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._run_scenario_from_main,
            width=18,
            height=2,
            state="disabled"
        )
        self.run_scenario_button.pack(side="left")
        
        # Кнопка "Назад"
        self.scenario_back_button = tk.Button(
            self.scenario_input_frame,
            text="Назад",
            font=("Arial", 14),
            bg="gray",
            fg="white",
            activebackground="darkgray",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._show_main_menu
        )
        self.scenario_back_button.pack(pady=(0, 20), padx=20, fill="x", ipady=6)
        
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
    
    def _show_main_menu(self):
        """Показать главное меню (кнопки выбора режима)"""
        # Скрываем фреймы сценария
        if USE_CUSTOM_TKINTER:
            self.scenario_input_frame.pack_forget()
        else:
            self.scenario_input_frame.pack_forget()
        # Показываем кнопки режима
        self.mode_frame.pack(pady=50, padx=40, fill="x")
    
    def _show_scenario_input(self):
        """Показать форму выбора сценария"""
        # Скрываем главное меню
        if USE_CUSTOM_TKINTER:
            self.mode_frame.pack_forget()
            self.scenario_input_frame.pack(pady=40, padx=40, fill="x")
        else:
            self.mode_frame.pack_forget()
            self.scenario_input_frame.pack(pady=40, padx=40, fill="x")
    
    def _open_simple_chat(self):
        """Открыть простой чат без кликера"""
        if not self.simple_chat_window:
            self.simple_chat_window = ChatWindow(self.root, clicker=None)
        self.simple_chat_window.show()
    
    
    def _select_scenario(self):
        """Выбор файла сценария"""
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
                self._update_status(f"Ошибка: файл не найден: {str(e)}", error=True)
                return
            except ValueError as e:
                self._update_status(f"Ошибка парсинга JSON: {str(e)}", error=True)
                return
            except Exception as e:
                self._update_status(f"Ошибка загрузки файла: {str(e)}", error=True)
                return
            
            try:
                scenario = ScenarioParser.parse(json_data)
            except ValueError as e:
                self._update_status(f"Ошибка парсинга сценария: {str(e)}", error=True)
                return
            
            # Валидация сценария
            from app.scenarios.validator import ScenarioValidator
            is_valid, error = ScenarioValidator.validate(scenario)
            if not is_valid:
                self._update_status(f"Ошибка валидации: {error}", error=True)
                return
            
            self.selected_scenario = scenario
            self.selected_scenario_path = file_path
            
            # Обновление UI
            scenario_name = scenario.get('name', 'Неизвестный сценарий')
            file_name = os.path.basename(file_path)
            if USE_CUSTOM_TKINTER:
                self.scenario_info_label.configure(text=f"{scenario_name} ({file_name})")
                self.run_scenario_button.configure(state="normal")
            else:
                self.scenario_info_label.configure(text=f"{scenario_name} ({file_name})")
                self.run_scenario_button.configure(state="normal")
            
            self._update_status(f"Сценарий выбран: {scenario_name}", success=True)
            
        except Exception as e:
            self._update_status(f"Неожиданная ошибка: {str(e)}", error=True)
    
    def _run_scenario_from_main(self):
        """Запуск сценария из главного окна"""
        if not self.selected_scenario:
            self._update_status("Сценарий не выбран", error=True)
            return
        
        # Обновление статуса
        self._update_status("Запуск браузера...")
        if USE_CUSTOM_TKINTER:
            self.run_scenario_button.configure(state="disabled")
            self.select_scenario_button.configure(state="disabled")
        else:
            self.run_scenario_button.configure(state="disabled")
            self.select_scenario_button.configure(state="disabled")
        
        try:
            # Создание кликера
            if not self.clicker:
                self.clicker = WebClicker(headless=False)
            
            # Запуск браузера
            if not self.clicker.driver:
                if not self.clicker.start_browser("chrome"):
                    self._update_status("Ошибка: не удалось запустить браузер", error=True)
                    if USE_CUSTOM_TKINTER:
                        self.run_scenario_button.configure(state="normal")
                        self.select_scenario_button.configure(state="normal")
                    else:
                        self.run_scenario_button.configure(state="normal")
                        self.select_scenario_button.configure(state="normal")
                    return
            
            # Создаем или показываем окно чата (передаем clicker для автоматизации)
            if not self.chat_window:
                self.chat_window = ChatWindow(self.root, clicker=self.clicker)
            else:
                # Обновляем clicker в существующем окне чата
                self.chat_window.clicker = self.clicker
                if self.chat_window.llm_client:
                    try:
                        from app.automation.ai_controller import AIController
                        self.chat_window.ai_controller = AIController(
                            self.clicker, 
                            llm_client=self.chat_window.llm_client
                        )
                    except:
                        pass
            
            # Загружаем сценарий в ChatWindow
            self.chat_window.current_scenario = self.selected_scenario
            self.chat_window.scenario_file_path = self.selected_scenario_path
            
            # Показываем окно чата
            self.chat_window.show()
            
            # Запускаем сценарий в ChatWindow
            self.chat_window._run_scenario()

            # Убираем главное окно, чтобы не перекрывать браузер
            try:
                self.root.iconify()
            except Exception:
                pass
            
            self._update_status("Сценарий запущен", success=True)
            
        except Exception as e:
            self._update_status(f"Ошибка: {str(e)}", error=True)
        finally:
            if USE_CUSTOM_TKINTER:
                self.run_scenario_button.configure(state="normal" if self.selected_scenario else "disabled")
                self.select_scenario_button.configure(state="normal")
            else:
                self.run_scenario_button.configure(state="normal" if self.selected_scenario else "disabled")
                self.select_scenario_button.configure(state="normal")
    
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
