"""
Окно авторизации (регистрация/вход)
"""

import os

try:
    import customtkinter as ctk
    USE_CUSTOM_TKINTER = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
    USE_CUSTOM_TKINTER = False

from app.api.client import APIClient


class AuthWindow:
    """Окно авторизации перед запуском приложения"""

    def __init__(self):
        self.api = APIClient()
        self.success = False
        self.user = None
        self.token = None

        if USE_CUSTOM_TKINTER:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
            self.root.title("Веб-Кликер Pro — Авторизация")
            self.root.geometry("460x520")
            self.root.minsize(420, 480)
            self.root.configure(fg_color="#0f1115")
            self._create_widgets()
        else:
            self.root = tk.Tk()
            self.root.title("Веб-Кликер Pro — Авторизация")
            self.root.geometry("460x520")
            self.root.minsize(420, 480)
            self.root.configure(bg="#0f1115")
            self._create_widgets_tkinter()

        self._center_window()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _set_error(self, label, message: str):
        if USE_CUSTOM_TKINTER:
            label.configure(text=message)
        else:
            label.config(text=message)

    def _complete_login(self, result: dict):
        token = result.get("token")
        if not token:
            return
        self.token = token
        self.user = result.get("user")
        os.environ["API_AUTH_TOKEN"] = token
        self.success = True
        self.root.destroy()

    def _handle_login(self):
        identifier = self.login_identifier_entry.get().strip()
        password = self.login_password_entry.get()
        if not identifier or not password:
            self._set_error(self.login_error_label, "Введите логин/почту и пароль")
            return
        result = self.api.login_user(identifier=identifier, password=password)
        if not result or not result.get("token"):
            self._set_error(self.login_error_label, "Не удалось войти. Проверьте данные.")
            return
        self._complete_login(result)

    def _handle_register(self):
        login = self.reg_login_entry.get().strip()
        email = self.reg_email_entry.get().strip()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        if not login or not email or not password or not confirm:
            self._set_error(self.register_error_label, "Заполните все поля регистрации")
            return
        result = self.api.register_user(
            login=login,
            email=email,
            password=password,
            confirm_password=confirm,
        )
        if not result or not result.get("token"):
            self._set_error(self.register_error_label, "Не удалось зарегистрироваться")
            return
        self._complete_login(result)

    def _create_widgets(self):
        container = ctk.CTkFrame(self.root, fg_color="transparent")
        container.pack(padx=28, pady=24, fill="both", expand=True)

        header = ctk.CTkFrame(
            container,
            fg_color="#161a22",
            border_width=1,
            border_color="#2a3140",
            corner_radius=14,
        )
        header.pack(fill="x", pady=(0, 18))

        title = ctk.CTkLabel(
            header,
            text="Авторизация",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#f8fafc",
        )
        title.pack(anchor="center", padx=20, pady=(16, 6))

        subtitle = ctk.CTkLabel(
            header,
            text="Вход или регистрация для доступа к серверу",
            font=ctk.CTkFont(size=13),
            text_color="#9aa4b2",
        )
        subtitle.pack(anchor="center", padx=20, pady=(0, 16))

        tabs = ctk.CTkTabview(container, fg_color="#0f1115")
        tabs.pack(fill="both", expand=True)
        login_tab = tabs.add("Вход")
        register_tab = tabs.add("Регистрация")

        # Login tab
        self.login_identifier_entry = ctk.CTkEntry(
            login_tab,
            placeholder_text="Логин или почта",
            height=38,
        )
        self.login_identifier_entry.pack(pady=(22, 10), padx=16, fill="x")

        self.login_password_entry = ctk.CTkEntry(
            login_tab,
            placeholder_text="Пароль",
            show="*",
            height=38,
        )
        self.login_password_entry.pack(pady=(0, 10), padx=16, fill="x")

        self.login_error_label = ctk.CTkLabel(
            login_tab,
            text="",
            text_color="#f87171",
            font=ctk.CTkFont(size=12),
        )
        self.login_error_label.pack(pady=(0, 6))

        login_button = ctk.CTkButton(
            login_tab,
            text="Войти",
            height=40,
            corner_radius=10,
            fg_color="#4c8bf5",
            hover_color="#3b76d8",
            command=self._handle_login,
        )
        login_button.pack(pady=(6, 16), padx=16, fill="x")

        # Register tab
        self.reg_login_entry = ctk.CTkEntry(
            register_tab,
            placeholder_text="Логин",
            height=38,
        )
        self.reg_login_entry.pack(pady=(22, 10), padx=16, fill="x")

        self.reg_email_entry = ctk.CTkEntry(
            register_tab,
            placeholder_text="Почта",
            height=38,
        )
        self.reg_email_entry.pack(pady=(0, 10), padx=16, fill="x")

        self.reg_password_entry = ctk.CTkEntry(
            register_tab,
            placeholder_text="Пароль",
            show="*",
            height=38,
        )
        self.reg_password_entry.pack(pady=(0, 10), padx=16, fill="x")

        self.reg_confirm_entry = ctk.CTkEntry(
            register_tab,
            placeholder_text="Подтвердите пароль",
            show="*",
            height=38,
        )
        self.reg_confirm_entry.pack(pady=(0, 10), padx=16, fill="x")

        self.register_error_label = ctk.CTkLabel(
            register_tab,
            text="",
            text_color="#f87171",
            font=ctk.CTkFont(size=12),
        )
        self.register_error_label.pack(pady=(0, 6))

        register_button = ctk.CTkButton(
            register_tab,
            text="Зарегистрироваться",
            height=40,
            corner_radius=10,
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=self._handle_register,
        )
        register_button.pack(pady=(6, 16), padx=16, fill="x")

    def _create_widgets_tkinter(self):
        container = tk.Frame(self.root, bg="#0f1115")
        container.pack(padx=28, pady=24, fill="both", expand=True)

        header = tk.Frame(container, bg="#161a22", bd=1, relief="solid")
        header.pack(fill="x", pady=(0, 18))

        title = tk.Label(
            header,
            text="Авторизация",
            bg="#161a22",
            fg="#f8fafc",
            font=("Arial", 18, "bold"),
        )
        title.pack(anchor="center", padx=20, pady=(16, 6))

        subtitle = tk.Label(
            header,
            text="Вход или регистрация для доступа к серверу",
            bg="#161a22",
            fg="#9aa4b2",
            font=("Arial", 10),
        )
        subtitle.pack(anchor="center", padx=20, pady=(0, 16))

        tabs = ttk.Notebook(container)
        tabs.pack(fill="both", expand=True)
        login_tab = tk.Frame(tabs, bg="#0f1115")
        register_tab = tk.Frame(tabs, bg="#0f1115")
        tabs.add(login_tab, text="Вход")
        tabs.add(register_tab, text="Регистрация")

        tk.Label(login_tab, text="Логин или почта", bg="#0f1115", fg="#f8fafc").pack(pady=(22, 4))
        self.login_identifier_entry = tk.Entry(login_tab)
        self.login_identifier_entry.pack(pady=(0, 10), padx=16, fill="x")

        tk.Label(login_tab, text="Пароль", bg="#0f1115", fg="#f8fafc").pack(pady=(0, 4))
        self.login_password_entry = tk.Entry(login_tab, show="*")
        self.login_password_entry.pack(pady=(0, 10), padx=16, fill="x")

        self.login_error_label = tk.Label(login_tab, text="", bg="#0f1115", fg="#f87171")
        self.login_error_label.pack(pady=(0, 6))

        tk.Button(login_tab, text="Войти", command=self._handle_login).pack(pady=(6, 16), padx=16, fill="x")

        tk.Label(register_tab, text="Логин", bg="#0f1115", fg="#f8fafc").pack(pady=(22, 4))
        self.reg_login_entry = tk.Entry(register_tab)
        self.reg_login_entry.pack(pady=(0, 10), padx=16, fill="x")

        tk.Label(register_tab, text="Почта", bg="#0f1115", fg="#f8fafc").pack(pady=(0, 4))
        self.reg_email_entry = tk.Entry(register_tab)
        self.reg_email_entry.pack(pady=(0, 10), padx=16, fill="x")

        tk.Label(register_tab, text="Пароль", bg="#0f1115", fg="#f8fafc").pack(pady=(0, 4))
        self.reg_password_entry = tk.Entry(register_tab, show="*")
        self.reg_password_entry.pack(pady=(0, 10), padx=16, fill="x")

        tk.Label(register_tab, text="Подтвердите пароль", bg="#0f1115", fg="#f8fafc").pack(pady=(0, 4))
        self.reg_confirm_entry = tk.Entry(register_tab, show="*")
        self.reg_confirm_entry.pack(pady=(0, 10), padx=16, fill="x")

        self.register_error_label = tk.Label(register_tab, text="", bg="#0f1115", fg="#f87171")
        self.register_error_label.pack(pady=(0, 6))

        tk.Button(register_tab, text="Зарегистрироваться", command=self._handle_register).pack(
            pady=(6, 16),
            padx=16,
            fill="x",
        )

    def _on_close(self):
        if not self.success:
            if USE_CUSTOM_TKINTER:
                self.root.destroy()
            else:
                messagebox.showinfo("Выход", "Авторизация отменена")
                self.root.destroy()

    def run(self) -> bool:
        self.root.mainloop()
        return self.success
