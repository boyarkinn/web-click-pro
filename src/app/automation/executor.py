"""
Исполнитель команд для автоматизации
Выполняет команды через WebClicker
"""

from typing import Optional, Dict, Any, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from .commands import (
    Command, ActionType, SelectorMethod, ScrollDirection,
    ClickCommand, TypeCommand, ScrollCommand, WaitCommand, NavigateCommand
)
from ..core.clicker import WebClicker


class CommandExecutor:
    """Исполнитель команд"""
    
    def __init__(self, clicker: WebClicker):
        """
        Инициализация исполнителя
        
        Args:
            clicker: Экземпляр WebClicker для выполнения команд
        """
        self.clicker = clicker
        self._selector_method_map = {
            SelectorMethod.CSS: By.CSS_SELECTOR,
            SelectorMethod.XPATH: By.XPATH,
            SelectorMethod.ID: By.ID,
            SelectorMethod.NAME: By.NAME,
            SelectorMethod.CLASS: By.CLASS_NAME,
            SelectorMethod.TAG: By.TAG_NAME,
        }
    
    def execute(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[Any]]:
        """
        Выполнение команды
        
        Args:
            command_dict: Словарь с командой
            
        Returns:
            Tuple[bool, Optional[str], Optional[Any]]: (успех, сообщение, результат)
        """
        try:
            action = ActionType(command_dict["action"])
        except (ValueError, KeyError):
            return False, f"Неизвестный тип действия: {command_dict.get('action')}", None
        
        try:
            if action == ActionType.CLICK:
                return self._execute_click(command_dict)
            elif action == ActionType.TYPE:
                return self._execute_type(command_dict)
            elif action == ActionType.SCROLL:
                return self._execute_scroll(command_dict)
            elif action == ActionType.WAIT:
                return self._execute_wait(command_dict)
            elif action == ActionType.NAVIGATE:
                return self._execute_navigate(command_dict)
            elif action == ActionType.GET_TEXT:
                return self._execute_get_text(command_dict)
            elif action == ActionType.GET_ATTRIBUTE:
                return self._execute_get_attribute(command_dict)
            elif action == ActionType.SCREENSHOT:
                return self._execute_screenshot(command_dict)
            else:
                return False, f"Действие {action} не реализовано", None
        except Exception as e:
            return False, f"Ошибка при выполнении команды: {str(e)}", None
    
    def _execute_click(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], None]:
        """Выполнение команды клика"""
        selector = command_dict["selector"]
        method = SelectorMethod(command_dict.get("method", "css"))
        scroll = command_dict.get("scroll", True)
        
        if method == SelectorMethod.TEXT:
            # Поиск по тексту элемента
            by = By.XPATH
            selector = f"//*[text()='{selector}']"
        else:
            by = self._selector_method_map[method]
        
        success = self.clicker.click(selector, by=by, scroll=scroll)
        if success:
            return True, f"Клик выполнен: {selector}", None
        else:
            return False, f"Не удалось выполнить клик: {selector}", None
    
    def _execute_type(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], None]:
        """Выполнение команды ввода текста"""
        selector = command_dict["selector"]
        value = command_dict["value"]
        method = SelectorMethod(command_dict.get("method", "css"))
        clear_first = command_dict.get("clear_first", True)
        press_enter = command_dict.get("press_enter", False)
        
        if method == SelectorMethod.TEXT:
            # Поиск по тексту - для ввода текста это не подходит
            return False, "Для команды 'type' нельзя использовать метод 'text'", None
        
        by = self._selector_method_map[method]
        
        success = self.clicker.type_text(selector, value, by=by, clear=clear_first)
        
        if success and press_enter:
            # Нажимаем Enter после ввода
            element = self.clicker.find_element(selector, by)
            if element:
                try:
                    element.send_keys(Keys.RETURN)
                except:
                    pass
        
        if success:
            return True, f"Текст введен в {selector}: {value[:50]}...", None
        else:
            return False, f"Не удалось ввести текст в {selector}", None
    
    def _execute_scroll(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], None]:
        """Выполнение команды прокрутки"""
        direction = ScrollDirection(command_dict.get("direction", "down"))
        pixels = command_dict.get("pixels")
        selector = command_dict.get("selector")
        
        if not self.clicker.driver:
            return False, "Браузер не запущен", None
        
        try:
            if direction == ScrollDirection.TO_ELEMENT:
                if not selector:
                    return False, "Для прокрутки к элементу нужен селектор", None
                
                method = SelectorMethod(command_dict.get("method", "css"))
                by = self._selector_method_map[method]
                
                element = self.clicker.find_element(selector, by)
                if element:
                    self.clicker.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    self.clicker.wait(0.5)
                    return True, f"Прокрутка к элементу: {selector}", None
                else:
                    return False, f"Элемент не найден для прокрутки: {selector}", None
            
            elif direction == ScrollDirection.DOWN:
                if pixels:
                    self.clicker.driver.execute_script(f"window.scrollBy(0, {pixels});")
                else:
                    self.clicker.scroll_to_bottom()
                return True, "Прокрутка вниз выполнена", None
            
            elif direction == ScrollDirection.UP:
                if pixels:
                    self.clicker.driver.execute_script(f"window.scrollBy(0, -{pixels});")
                else:
                    self.clicker.scroll_to_top()
                return True, "Прокрутка вверх выполнена", None
            
            elif direction == ScrollDirection.TOP:
                self.clicker.scroll_to_top()
                return True, "Прокрутка в начало выполнена", None
            
            elif direction == ScrollDirection.BOTTOM:
                self.clicker.scroll_to_bottom()
                return True, "Прокрутка в конец выполнена", None
            
            return False, f"Неизвестное направление прокрутки: {direction}", None
        except Exception as e:
            return False, f"Ошибка при прокрутке: {str(e)}", None
    
    def _execute_wait(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], None]:
        """Выполнение команды ожидания"""
        seconds = command_dict.get("seconds")
        wait_for_element = command_dict.get("wait_for_element", False)
        
        if wait_for_element:
            selector = command_dict.get("selector")
            if not selector:
                return False, "Ожидание элемента требует селектор", None
            
            method = SelectorMethod(command_dict.get("method", "css"))
            by = self._selector_method_map[method]
            timeout = command_dict.get("timeout", 10)
            
            element = self.clicker.wait_for_element(selector, by, timeout)
            if element:
                return True, f"Элемент найден: {selector}", None
            else:
                return False, f"Элемент не найден за {timeout} секунд: {selector}", None
        
        elif seconds:
            self.clicker.wait(seconds)
            return True, f"Ожидание {seconds} секунд выполнено", None
        
        return False, "Команда wait требует либо seconds, либо wait_for_element", None
    
    def _execute_navigate(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], None]:
        """Выполнение команды навигации"""
        url = command_dict["url"]
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        success = self.clicker.open_url(url)
        if success:
            return True, f"Переход на {url} выполнен", None
        else:
            return False, f"Не удалось перейти на {url}", None
    
    def _execute_get_text(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Выполнение команды получения текста"""
        selector = command_dict["selector"]
        method = SelectorMethod(command_dict.get("method", "css"))
        
        if method == SelectorMethod.TEXT:
            return False, "Для команды 'get_text' нельзя использовать метод 'text'", None
        
        by = self._selector_method_map[method]
        
        text = self.clicker.get_text(selector, by)
        if text is not None:
            return True, f"Текст получен из {selector}", text
        else:
            return False, f"Не удалось получить текст из {selector}", None
    
    def _execute_get_attribute(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Выполнение команды получения атрибута"""
        selector = command_dict["selector"]
        attribute = command_dict["value"]  # В value хранится название атрибута
        method = SelectorMethod(command_dict.get("method", "css"))
        
        if method == SelectorMethod.TEXT:
            return False, "Для команды 'get_attribute' нельзя использовать метод 'text'", None
        
        by = self._selector_method_map[method]
        
        value = self.clicker.get_attribute(selector, attribute, by)
        if value is not None:
            return True, f"Атрибут {attribute} получен из {selector}", value
        else:
            return False, f"Не удалось получить атрибут {attribute} из {selector}", None
    
    def _execute_screenshot(self, command_dict: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Выполнение команды скриншота"""
        filename = command_dict.get("filename", "screenshot.png")
        
        success = self.clicker.take_screenshot(filename)
        if success:
            return True, f"Скриншот сохранен: {filename}", filename
        else:
            return False, "Не удалось создать скриншот", None
