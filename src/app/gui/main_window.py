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
# Импорт API клиента
from app.api.client import APIClient
# Импорт для работы с файлами
from tkinter import filedialog
# Импорт сценариев
from app.scenarios.parser import ScenarioParser
from app.core.paths import get_env_path


class MainWindow:
    """Главное окно приложения"""
    
    def __init__(self):
        """Инициализация главного окна"""
        # Инициализация кликера
        self.clicker = None
        # Окна
        self.chat_window = None
        self.simple_chat_window = None
        self.account_window = None
        self.api_client = APIClient()
        self.account_login_value = None
        self.account_email_value = None
        self.account_status_label = None
        self.account_current_password_entry = None
        self.account_new_password_entry = None
        self.account_confirm_password_entry = None
        # Выбранный сценарий
        self.selected_scenario = None
        self.selected_scenario_path = None
        self.window_width = 920
        self.window_height = 640
        
        if USE_CUSTOM_TKINTER:
            # Настройка CustomTkinter
            ctk.set_appearance_mode("dark")  # "light" или "dark"
            ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
            
            # Создание окна
            self.root = ctk.CTk()
            self.root.title("Веб-Кликер Pro")
            self.root.geometry(f"{self.window_width}x{self.window_height}")
            self.root.minsize(900, 800)
            self.root.configure(fg_color="#0f1115")
            
            # Центрирование окна
            self._center_window()
            
            # Создание интерфейса
            self._create_widgets()
        else:
            # Обычный Tkinter
            self.root = tk.Tk()
            self.root.title("Веб-Кликер Pro")
            self.root.geometry(f"{self.window_width}x{self.window_height}")
            self.root.minsize(900, 800)
            self.root.configure(bg="#0f1115")
            
            # Центрирование окна
            self._center_window()
            
            # Создание интерфейса
            self._create_widgets_tkinter()
    
    def _center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        # Используем заданный размер вместо реального размера окна
        width = self.window_width
        height = self.window_height
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """Создание виджетов (CustomTkinter)"""
        # Контентный контейнер (главный экран)
        self.main_content = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_content.pack(padx=36, pady=28, fill="both", expand=True)
        
        # Контейнер заголовка
        header_card = ctk.CTkFrame(
            self.main_content,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        header_card.pack(fill="x", pady=(0, 18))
        
        # Заголовок
        title = ctk.CTkLabel(
            header_card,
            text="Веб-Кликер Pro",
            font=ctk.CTkFont(size=34, weight="bold"),
            text_color="#f8fafc"
        )
        title.pack(anchor="center", padx=20, pady=(16, 4))
        
        # Подзаголовок
        subtitle = ctk.CTkLabel(
            header_card,
            text="Автоматизация действий в браузере для быстрых задач",
            font=ctk.CTkFont(size=15),
            text_color="#9aa4b2"
        )
        subtitle.pack(anchor="center", padx=20, pady=(0, 16))
        
        # Фрейм для карточек выбора режима
        self.mode_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.mode_frame.pack(fill="x", pady=(4, 16))
        
        # Карточка "Запустить сценарий"
        scenario_card = ctk.CTkFrame(
            self.mode_frame,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        scenario_card.pack(fill="x", pady=(0, 16))
        
        self.run_scenario_entry_button = ctk.CTkButton(
            scenario_card,
            text="Запустить сценарий",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color="#4c8bf5",
            hover_color="#3b76d8",
            command=self._show_scenario_input
        )
        self.run_scenario_entry_button.pack(padx=20, pady=18, fill="x")
        
        # Карточка "Чат"
        chat_card = ctk.CTkFrame(
            self.mode_frame,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        chat_card.pack(fill="x", pady=(0, 16))
        
        self.chat_button = ctk.CTkButton(
            chat_card,
            text="Чат",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=self._open_simple_chat
        )
        self.chat_button.pack(padx=20, pady=18, fill="x")

        # Карточка "Аккаунт"
        account_card = ctk.CTkFrame(
            self.mode_frame,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        account_card.pack(fill="x")

        self.account_button = ctk.CTkButton(
            account_card,
            text="Аккаунт",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            corner_radius=10,
            fg_color="#f59e0b",
            hover_color="#d97706",
            command=self._open_account
        )
        self.account_button.pack(padx=20, pady=18, fill="x")
        
        # Фрейм для выбора сценария (скрыт по умолчанию)
        self.scenario_input_frame = ctk.CTkFrame(self.root, fg_color="#0f1115")
        self.scenario_input_frame.pack_forget()  # Скрыт по умолчанию

        # Фрейм аккаунта (скрыт по умолчанию)
        self.account_frame = ctk.CTkFrame(self.root, fg_color="#0f1115")
        self.account_frame.pack_forget()

        account_content = ctk.CTkFrame(self.account_frame, fg_color="transparent")
        account_content.pack(padx=36, pady=28, fill="both", expand=True)

        account_header_card = ctk.CTkFrame(
            account_content,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        account_header_card.pack(fill="x", pady=(0, 18))
        account_header_card.pack_propagate(True)

        account_header_row = ctk.CTkFrame(account_header_card, fg_color="transparent")
        account_header_row.pack(fill="x", padx=20, pady=(14, 12))
        account_header_row.pack_propagate(True)
        account_header_row.grid_columnconfigure(0, weight=1)
        account_header_row.grid_columnconfigure(1, weight=0)
        account_header_row.grid_columnconfigure(2, weight=1)

        self.account_back_button = ctk.CTkButton(
            account_header_row,
            text="Назад",
            font=ctk.CTkFont(size=13),
            height=30,
            width=90,
            command=self._close_account_window,
            fg_color="#1f2937",
            hover_color="#273244"
        )
        self.account_back_button.grid(row=0, column=0, sticky="w")

        account_title = ctk.CTkLabel(
            account_header_row,
            text="Аккаунт",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc"
        )
        account_title.grid(row=0, column=1, sticky="n")

        account_card = ctk.CTkFrame(
            account_content,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        account_card.pack(fill="x")

        info_card = ctk.CTkFrame(
            account_card,
            fg_color="#0f1115",
            border_width=1,
            border_color="#2a3140",
            corner_radius=12,
        )
        info_card.pack(padx=16, pady=(18, 16), fill="x")

        login_row = ctk.CTkFrame(info_card, fg_color="transparent")
        login_row.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(login_row, text="Логин", text_color="#9aa4b2").pack(side="left")
        self.account_login_value = ctk.CTkLabel(login_row, text="—", text_color="#f8fafc")
        self.account_login_value.pack(side="right")

        email_row = ctk.CTkFrame(info_card, fg_color="transparent")
        email_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(email_row, text="Почта", text_color="#9aa4b2").pack(side="left")
        self.account_email_value = ctk.CTkLabel(email_row, text="—", text_color="#f8fafc")
        self.account_email_value.pack(side="right")

        password_card = ctk.CTkFrame(
            account_card,
            fg_color="#0f1115",
            border_width=1,
            border_color="#2a3140",
            corner_radius=12,
        )
        password_card.pack(padx=16, pady=(0, 18), fill="x")

        ctk.CTkLabel(
            password_card,
            text="Смена пароля",
            text_color="#f8fafc",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 8))

        current_frame, self.account_current_password_entry = self._create_account_password_field_ctk(
            password_card,
            placeholder_text="Текущий пароль",
            height=34,
        )
        current_frame.pack(padx=14, pady=(0, 8), fill="x")

        new_frame, self.account_new_password_entry = self._create_account_password_field_ctk(
            password_card,
            placeholder_text="Новый пароль",
            height=34,
        )
        new_frame.pack(padx=14, pady=(0, 8), fill="x")

        confirm_frame, self.account_confirm_password_entry = self._create_account_password_field_ctk(
            password_card,
            placeholder_text="Подтвердите новый пароль",
            height=34,
        )
        confirm_frame.pack(padx=14, pady=(0, 8), fill="x")

        self.account_status_label = ctk.CTkLabel(
            password_card,
            text="",
            text_color="#f87171",
            font=ctk.CTkFont(size=12),
        )
        self.account_status_label.pack(pady=(0, 6))

        ctk.CTkButton(
            password_card,
            text="Сменить пароль",
            height=36,
            corner_radius=8,
            fg_color="#4c8bf5",
            hover_color="#3b76d8",
            command=self._handle_change_password,
        ).pack(padx=14, pady=(0, 12), fill="x")

        ctk.CTkButton(
            account_card,
            text="Выйти из аккаунта",
            height=34,
            corner_radius=8,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self._handle_logout,
        ).pack(padx=16, pady=(0, 18), fill="x")
        
        scenario_content = ctk.CTkFrame(self.scenario_input_frame, fg_color="transparent")
        scenario_content.pack(padx=36, pady=28, fill="both", expand=True)
        
        scenario_header_card = ctk.CTkFrame(
            scenario_content,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        scenario_header_card.pack(fill="x", pady=(0, 18))
        scenario_header_card.pack_propagate(True)
        
        header_row = ctk.CTkFrame(scenario_header_card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(14, 12))
        header_row.pack_propagate(True)
        header_row.grid_columnconfigure(0, weight=1)
        header_row.grid_columnconfigure(1, weight=0)
        header_row.grid_columnconfigure(2, weight=1)
        
        self.scenario_back_button = ctk.CTkButton(
            header_row,
            text="Назад",
            font=ctk.CTkFont(size=13),
            height=30,
            width=90,
            command=self._show_main_menu,
            fg_color="#1f2937",
            hover_color="#273244"
        )
        self.scenario_back_button.grid(row=0, column=0, sticky="w")
        
        header_text = ctk.CTkFrame(header_row, fg_color="transparent")
        header_text.grid(row=0, column=1, sticky="nsew")
        header_text.pack_propagate(True)
        
        scenario_title = ctk.CTkLabel(
            header_text,
            text="Запустить сценарий",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f8fafc"
        )
        scenario_title.pack(anchor="center", pady=(2, 4))
        
        scenario_subtitle = ctk.CTkLabel(
            header_text,
            text="Выберите JSON-файл и запустите автоматизацию.",
            font=ctk.CTkFont(size=13),
            text_color="#9aa4b2"
        )
        scenario_subtitle.pack(anchor="center")
        
        # Пустая колонка справа для центрирования текста
        
        scenario_card = ctk.CTkFrame(
            scenario_content,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=16
        )
        scenario_card.pack(fill="x")
        
        # Метка для выбора сценария
        scenario_label = ctk.CTkLabel(
            scenario_card,
            text="Выберите сценарий",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e2e8f0"
        )
        scenario_label.pack(anchor="w", pady=(18, 6), padx=20)
        
        # Метка выбранного сценария
        self.scenario_info_label = ctk.CTkLabel(
            scenario_card,
            text="Сценарий не выбран",
            font=ctk.CTkFont(size=12),
            text_color="#8a97a8"
        )
        self.scenario_info_label.pack(anchor="w", pady=(0, 12), padx=20)
        
        # Фрейм для кнопок сценария
        scenario_buttons_frame = ctk.CTkFrame(scenario_card, fg_color="transparent")
        scenario_buttons_frame.pack(pady=(0, 16), padx=20, fill="x")
        
        # Кнопка выбора сценария
        self.select_scenario_button = ctk.CTkButton(
            scenario_buttons_frame,
            text="Выбрать файл",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            command=self._select_scenario,
            fg_color="#3b4758",
            hover_color="#334052"
        )
        self.select_scenario_button.pack(side="left", padx=(0, 10))
        
        # Кнопка запуска сценария
        self.run_scenario_button = ctk.CTkButton(
            scenario_buttons_frame,
            text="Запустить",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            command=self._run_scenario_from_main,
            fg_color="#22c55e",
            hover_color="#16a34a"
        )
        self.run_scenario_button.pack(side="left")
        self._set_run_button_state(False)
        
        
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
        # Контентный контейнер (главный экран)
        self.main_content = tk.Frame(self.root, bg="#0f1115")
        self.main_content.pack(padx=36, pady=28, fill="both", expand=True)
        
        # Контейнер заголовка
        header_card = tk.Frame(
            self.main_content,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        header_card.pack(fill="x", pady=(0, 18))
        
        # Заголовок
        title = tk.Label(
            header_card,
            text="Веб-Кликер Pro",
            font=("Segoe UI", 32, "bold"),
            bg="#161a22",
            fg="#f8fafc"
        )
        title.pack(anchor="center", padx=20, pady=(16, 4))
        
        # Подзаголовок
        subtitle = tk.Label(
            header_card,
            text="Автоматизация действий в браузере для быстрых задач",
            font=("Segoe UI", 14),
            bg="#161a22",
            fg="#9aa4b2"
        )
        subtitle.pack(anchor="center", padx=20, pady=(0, 16))
        
        # Фрейм для карточек выбора режима
        self.mode_frame = tk.Frame(self.main_content, bg="#0f1115")
        self.mode_frame.pack(fill="x", pady=(4, 16))
        
        # Карточка "Запустить сценарий"
        scenario_card = tk.Frame(
            self.mode_frame,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        scenario_card.pack(fill="x", pady=(0, 16))
        
        self.run_scenario_entry_button = tk.Button(
            scenario_card,
            text="Запустить сценарий",
            font=("Segoe UI", 13, "bold"),
            bg="#4c8bf5",
            fg="white",
            activebackground="#3b76d8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._show_scenario_input
        )
        self.run_scenario_entry_button.pack(padx=20, pady=18, fill="x", ipady=6)
        
        # Карточка "Чат"
        chat_card = tk.Frame(
            self.mode_frame,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        chat_card.pack(fill="x", pady=(0, 16))
        
        self.chat_button = tk.Button(
            chat_card,
            text="Чат",
            font=("Segoe UI", 13, "bold"),
            bg="#22c55e",
            fg="white",
            activebackground="#16a34a",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._open_simple_chat
        )
        self.chat_button.pack(padx=20, pady=18, fill="x", ipady=6)

        # Карточка "Аккаунт"
        account_card = tk.Frame(
            self.mode_frame,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        account_card.pack(fill="x")

        self.account_button = tk.Button(
            account_card,
            text="Аккаунт",
            font=("Segoe UI", 13, "bold"),
            bg="#f59e0b",
            fg="white",
            activebackground="#d97706",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._open_account
        )
        self.account_button.pack(padx=20, pady=18, fill="x", ipady=6)
        
        # Фрейм для выбора сценария (скрыт по умолчанию)
        self.scenario_input_frame = tk.Frame(self.root, bg="#0f1115")

        # Фрейм аккаунта (скрыт по умолчанию)
        self.account_frame = tk.Frame(self.root, bg="#0f1115")

        account_content = tk.Frame(self.account_frame, bg="#0f1115")
        account_content.pack(padx=36, pady=28, fill="both", expand=True)

        account_header_card = tk.Frame(
            account_content,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        account_header_card.pack(fill="x", pady=(0, 18))
        account_header_card.pack_propagate(True)

        account_header_row = tk.Frame(account_header_card, bg="#161a22")
        account_header_row.pack(fill="x", padx=20, pady=(14, 12))
        account_header_row.pack_propagate(True)
        account_header_row.grid_columnconfigure(0, weight=1)
        account_header_row.grid_columnconfigure(1, weight=0)
        account_header_row.grid_columnconfigure(2, weight=1)

        self.account_back_button = tk.Button(
            account_header_row,
            text="Назад",
            font=("Segoe UI", 12),
            bg="#1f2937",
            fg="white",
            activebackground="#273244",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._close_account_window,
            width=10
        )
        self.account_back_button.grid(row=0, column=0, sticky="w")

        account_title = tk.Label(
            account_header_row,
            text="Аккаунт",
            font=("Segoe UI", 20, "bold"),
            bg="#161a22",
            fg="#f8fafc"
        )
        account_title.grid(row=0, column=1, sticky="n")

        account_card = tk.Frame(
            account_content,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        account_card.pack(fill="x")

        info_card = tk.Frame(account_card, bg="#0f1115", highlightthickness=1, highlightbackground="#2a3140")
        info_card.pack(padx=16, pady=(18, 16), fill="x")

        login_row = tk.Frame(info_card, bg="#0f1115")
        login_row.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(login_row, text="Логин", bg="#0f1115", fg="#9aa4b2").pack(side="left")
        self.account_login_value = tk.Label(login_row, text="—", bg="#0f1115", fg="#f8fafc")
        self.account_login_value.pack(side="right")

        email_row = tk.Frame(info_card, bg="#0f1115")
        email_row.pack(fill="x", padx=14, pady=(0, 12))
        tk.Label(email_row, text="Почта", bg="#0f1115", fg="#9aa4b2").pack(side="left")
        self.account_email_value = tk.Label(email_row, text="—", bg="#0f1115", fg="#f8fafc")
        self.account_email_value.pack(side="right")

        password_card = tk.Frame(account_card, bg="#0f1115", highlightthickness=1, highlightbackground="#2a3140")
        password_card.pack(padx=16, pady=(0, 18), fill="x")

        tk.Label(
            password_card,
            text="Смена пароля",
            bg="#0f1115",
            fg="#f8fafc",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 8))

        current_frame, self.account_current_password_entry = self._create_account_password_field_tk(password_card)
        current_frame.pack(padx=14, pady=(0, 8), fill="x")

        new_frame, self.account_new_password_entry = self._create_account_password_field_tk(password_card)
        new_frame.pack(padx=14, pady=(0, 8), fill="x")

        confirm_frame, self.account_confirm_password_entry = self._create_account_password_field_tk(password_card)
        confirm_frame.pack(padx=14, pady=(0, 8), fill="x")

        self.account_status_label = tk.Label(password_card, text="", bg="#0f1115", fg="#f87171")
        self.account_status_label.pack(pady=(0, 6))

        tk.Button(
            password_card,
            text="Сменить пароль",
            bg="#4c8bf5",
            fg="white",
            activebackground="#3b76d8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._handle_change_password,
        ).pack(padx=14, pady=(0, 12), fill="x")

        tk.Button(
            account_card,
            text="Выйти из аккаунта",
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._handle_logout,
        ).pack(padx=16, pady=(0, 18), fill="x")
        
        scenario_content = tk.Frame(self.scenario_input_frame, bg="#0f1115")
        scenario_content.pack(padx=36, pady=28, fill="both", expand=True)
        
        scenario_header_card = tk.Frame(
            scenario_content,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        scenario_header_card.pack(fill="x", pady=(0, 18))
        scenario_header_card.pack_propagate(True)
        
        header_row = tk.Frame(scenario_header_card, bg="#161a22")
        header_row.pack(fill="x", padx=20, pady=(14, 12))
        header_row.pack_propagate(True)
        header_row.grid_columnconfigure(0, weight=1)
        header_row.grid_columnconfigure(1, weight=0)
        header_row.grid_columnconfigure(2, weight=1)
        
        self.scenario_back_button = tk.Button(
            header_row,
            text="Назад",
            font=("Segoe UI", 12),
            bg="#1f2937",
            fg="white",
            activebackground="#273244",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._show_main_menu,
            width=10
        )
        self.scenario_back_button.grid(row=0, column=0, sticky="w")
        
        header_text = tk.Frame(header_row, bg="#161a22")
        header_text.grid(row=0, column=1, sticky="nsew")
        header_text.pack_propagate(True)
        
        scenario_title = tk.Label(
            header_text,
            text="Запустить сценарий",
            font=("Segoe UI", 20, "bold"),
            bg="#161a22",
            fg="#f8fafc"
        )
        scenario_title.pack(anchor="center", pady=(2, 4))
        
        scenario_subtitle = tk.Label(
            header_text,
            text="Выберите JSON-файл и запустите автоматизацию.",
            font=("Segoe UI", 12),
            bg="#161a22",
            fg="#9aa4b2"
        )
        scenario_subtitle.pack(anchor="center")
        
        # Пустая колонка справа для центрирования текста
        
        scenario_card = tk.Frame(
            scenario_content,
            bg="#161a22",
            highlightthickness=1,
            highlightbackground="#2a3140"
        )
        scenario_card.pack(fill="x")
        
        # Метка для выбора сценария
        scenario_label = tk.Label(
            scenario_card,
            text="Выберите сценарий",
            font=("Segoe UI", 13, "bold"),
            bg="#161a22",
            fg="#e2e8f0"
        )
        scenario_label.pack(anchor="w", pady=(16, 6), padx=20)
        
        # Метка выбранного сценария
        self.scenario_info_label = tk.Label(
            scenario_card,
            text="Сценарий не выбран",
            font=("Segoe UI", 11),
            bg="#161a22",
            fg="#8a97a8"
        )
        self.scenario_info_label.pack(anchor="w", pady=(0, 12), padx=20)
        
        # Фрейм для кнопок сценария
        scenario_buttons_frame = tk.Frame(scenario_card, bg="#161a22")
        scenario_buttons_frame.pack(pady=(0, 16), padx=20, fill="x")
        
        # Кнопка выбора сценария
        self.select_scenario_button = tk.Button(
            scenario_buttons_frame,
            text="Выбрать файл",
            font=("Segoe UI", 12, "bold"),
            bg="#3b4758",
            fg="white",
            activebackground="#334052",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._select_scenario
        )
        self.select_scenario_button.pack(side="left", padx=(0, 10), ipadx=10, ipady=6)
        
        # Кнопка запуска сценария
        self.run_scenario_button = tk.Button(
            scenario_buttons_frame,
            text="Запустить",
            font=("Segoe UI", 12, "bold"),
            bg="#22c55e",
            fg="white",
            activebackground="#16a34a",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self._run_scenario_from_main,
            state="disabled"
        )
        self.run_scenario_button.pack(side="left", ipadx=12, ipady=6)
        self._set_run_button_state(False)
        
        
        # Статус
        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12),
            bg="#0f1115",
            fg="gray"
        )
        self.status_label.pack(pady=10)
        
        # Версия
        version = tk.Label(
            self.root,
            text="Версия 1.0.0",
            font=("Arial", 12),
            bg="#0f1115",
            fg="gray"
        )
        version.pack(side="bottom", pady=20)
    
    def _show_main_menu(self):
        """Показать главное меню (кнопки выбора режима)"""
        # Скрываем фреймы сценария и аккаунта
        if USE_CUSTOM_TKINTER:
            self.scenario_input_frame.pack_forget()
            self.account_frame.pack_forget()
        else:
            self.scenario_input_frame.pack_forget()
            self.account_frame.pack_forget()
        # Показываем главный экран
        if USE_CUSTOM_TKINTER:
            self.main_content.pack(padx=36, pady=28, fill="both", expand=True)
        else:
            self.main_content.pack(padx=36, pady=28, fill="both", expand=True)
    
    def _show_scenario_input(self):
        """Показать форму выбора сценария"""
        # Скрываем главное меню
        if USE_CUSTOM_TKINTER:
            self.main_content.pack_forget()
            self.scenario_input_frame.pack(pady=28, padx=36, fill="x")
        else:
            self.main_content.pack_forget()
            self.scenario_input_frame.pack(pady=28, padx=36, fill="x")

    def _show_account_page(self):
        """Показать страницу аккаунта"""
        if USE_CUSTOM_TKINTER:
            self.main_content.pack_forget()
            self.account_frame.pack(pady=28, padx=36, fill="x")
        else:
            self.main_content.pack_forget()
            self.account_frame.pack(pady=28, padx=36, fill="x")
    
    def _open_simple_chat(self):
        """Открыть простой чат без кликера"""
        if not self.simple_chat_window:
            self.simple_chat_window = ChatWindow(self.root, clicker=None)
        self.simple_chat_window.show()

    def _open_account(self):
        """Открыть страницу аккаунта"""
        self._show_account_page()
        self._load_account_profile()

    def _close_account_window(self):
        self._show_main_menu()
        self._set_account_status("")
        if self.account_current_password_entry:
            self.account_current_password_entry.delete(0, "end")
        if self.account_new_password_entry:
            self.account_new_password_entry.delete(0, "end")
        if self.account_confirm_password_entry:
            self.account_confirm_password_entry.delete(0, "end")

    def _load_account_profile(self):
        profile = self.api_client.get_profile()
        if not profile:
            self._set_account_status("Не удалось загрузить профиль", error=True)
            return
        if self.account_login_value:
            self.account_login_value.configure(text=profile.get("login", "—"))
        if self.account_email_value:
            self.account_email_value.configure(text=profile.get("email", "—"))
        self._set_account_status("")

    def _set_account_status(self, message: str, error: bool = True):
        if not self.account_status_label:
            return
        color = "#f87171" if error else "#22c55e"
        if USE_CUSTOM_TKINTER:
            self.account_status_label.configure(text=message, text_color=color)
        else:
            self.account_status_label.config(text=message, fg=color)

    def _create_account_password_field_ctk(self, parent, placeholder_text: str, height: int = 34):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder_text, show="*", height=height)
        entry.pack(side="left", fill="x", expand=True)

        state = {"visible": False}

        def toggle():
            state["visible"] = not state["visible"]
            entry.configure(show="" if state["visible"] else "*")
            toggle_btn.configure(text="🙈" if state["visible"] else "👁")

        toggle_btn = ctk.CTkButton(
            frame,
            text="👁",
            width=32,
            height=height,
            corner_radius=8,
            fg_color="#1f2937",
            hover_color="#273244",
            command=toggle,
        )
        toggle_btn.pack(side="right", padx=(8, 0))
        return frame, entry

    def _create_account_password_field_tk(self, parent):
        frame = tk.Frame(parent, bg="#0f1115")
        entry = tk.Entry(frame, show="*")
        entry.pack(side="left", fill="x", expand=True)

        state = {"visible": False}

        def toggle():
            state["visible"] = not state["visible"]
            entry.config(show="" if state["visible"] else "*")
            toggle_btn.config(text="🙈" if state["visible"] else "👁")

        toggle_btn = tk.Button(
            frame,
            text="👁",
            width=2,
            command=toggle,
            bg="#1f2937",
            fg="#f8fafc",
            activebackground="#273244",
            activeforeground="#f8fafc",
            relief="flat",
            cursor="hand2",
        )
        toggle_btn.pack(side="right", padx=(8, 0))
        return frame, entry

    def _handle_change_password(self):
        if not self.account_current_password_entry:
            return
        current_password = self.account_current_password_entry.get().strip()
        new_password = self.account_new_password_entry.get().strip()
        confirm_password = self.account_confirm_password_entry.get().strip()

        if not current_password or not new_password or not confirm_password:
            self._set_account_status("Заполните все поля", error=True)
            return
        if new_password != confirm_password:
            self._set_account_status("Пароли не совпадают", error=True)
            return

        result = self.api_client.change_password(
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )
        if not result or not result.get("message"):
            self._set_account_status("Не удалось сменить пароль", error=True)
            return

        self._set_account_status("Пароль обновлен", error=False)
        self.account_current_password_entry.delete(0, "end")
        self.account_new_password_entry.delete(0, "end")
        self.account_confirm_password_entry.delete(0, "end")

    def _handle_logout(self):
        self.api_client.clear_auth_token()
        os.environ.pop("API_AUTH_TOKEN", None)
        self._persist_auth_token(None)
        self._set_account_status("Вы вышли из аккаунта", error=False)

        # Возвращаемся к авторизации без закрытия приложения
        try:
            from app.gui.auth_window import AuthWindow
        except Exception:
            self.root.after(200, self.root.destroy)
            return

        self.root.withdraw()
        auth_window = AuthWindow(parent=self.root)
        if not auth_window.run():
            self.root.destroy()
            return

        token = os.environ.get("API_AUTH_TOKEN", "")
        if token:
            self.api_client.set_auth_token(token)
        self.root.deiconify()
        self._show_main_menu()
        self._load_account_profile()

    def _persist_auth_token(self, token: str | None) -> None:
        env_path = get_env_path()
        lines: list[str] = []
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
        filtered = [line for line in lines if not line.startswith("API_AUTH_TOKEN=")]
        if token:
            filtered.append(f"API_AUTH_TOKEN={token}")
        env_path.write_text("\n".join(filtered) + ("\n" if filtered else ""), encoding="utf-8")
    
    
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
                self._set_run_button_state(True)
            else:
                self.scenario_info_label.configure(text=f"{scenario_name} ({file_name})")
                self._set_run_button_state(True)
            
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
            self._set_run_button_state(False)
            self.select_scenario_button.configure(state="disabled")
        else:
            self._set_run_button_state(False)
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
                        self._set_run_button_state(True)
                        self.select_scenario_button.configure(state="normal")
                    else:
                        self._set_run_button_state(True)
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
                self._set_run_button_state(bool(self.selected_scenario))
                self.select_scenario_button.configure(state="normal")
            else:
                self._set_run_button_state(bool(self.selected_scenario))
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
    
    def _set_run_button_state(self, enabled: bool):
        """Обновить внешний вид кнопки запуска сценария"""
        if USE_CUSTOM_TKINTER:
            if enabled:
                self.run_scenario_button.configure(
                    state="normal",
                    fg_color="#22c55e",
                    hover_color="#16a34a",
                    text_color="#ffffff"
                )
            else:
                self.run_scenario_button.configure(
                    state="disabled",
                    fg_color="#2b313d",
                    hover_color="#2b313d",
                    text_color="#9aa4b2"
                )
        else:
            if enabled:
                self.run_scenario_button.configure(
                    state="normal",
                    bg="#22c55e",
                    fg="white",
                    activebackground="#16a34a",
                    activeforeground="white",
                    disabledforeground="white"
                )
            else:
                self.run_scenario_button.configure(
                    state="disabled",
                    bg="#2b313d",
                    fg="#9aa4b2",
                    activebackground="#2b313d",
                    activeforeground="#9aa4b2",
                    disabledforeground="#9aa4b2"
                )
    
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
