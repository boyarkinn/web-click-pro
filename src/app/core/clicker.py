"""
Базовый кликер для автоматизации работы с веб-сайтами
Поддерживает: открытие сайтов, поиск элементов, клики, чтение содержимого, анализ
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
try:
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
import time
import json
from typing import Optional, List, Dict, Any


class WebClicker:
    """Класс для автоматизации работы с веб-сайтами"""
    
    def __init__(self, headless: bool = False, wait_timeout: int = 10):
        """
        Инициализация кликера
        
        Args:
            headless: Запуск браузера в фоновом режиме (без окна)
            wait_timeout: Время ожидания элементов по умолчанию (секунды)
        """
        self.wait_timeout = wait_timeout
        self.driver = None
        self.headless = headless
        
    def start_browser(self, browser: str = "chrome"):
        """
        Запуск браузера
        
        Args:
            browser: Тип браузера ("chrome" или "firefox")
        """
        try:
            if browser.lower() == "chrome":
                chrome_options = Options()
                if self.headless:
                    chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Используем webdriver-manager для автоматической установки драйвера
                if WEBDRIVER_MANAGER_AVAILABLE:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    self.driver = webdriver.Chrome(options=chrome_options)
            elif browser.lower() == "firefox":
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                if self.headless:
                    firefox_options.add_argument("--headless")
                self.driver = webdriver.Firefox(options=firefox_options)
            else:
                raise ValueError(f"Неподдерживаемый браузер: {browser}")
            
            self.driver.maximize_window()
            print(f"[OK] Браузер {browser} успешно запущен")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при запуске браузера: {e}")
            return False
    
    def open_url(self, url: str):
        """
        Открытие URL
        
        Args:
            url: Адрес сайта для открытия
        """
        if not self.driver:
            print("[ERROR] Браузер не запущен. Вызовите start_browser() сначала")
            return False
        
        try:
            self.driver.get(url)
            print(f"[OK] Открыт URL: {url}")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при открытии URL: {e}")
            return False
    
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: Optional[int] = None):
        """
        Ожидание появления элемента на странице
        
        Args:
            selector: Селектор элемента
            by: Тип селектора (By.CSS_SELECTOR, By.ID, By.XPATH и т.д.)
            timeout: Время ожидания (если None, используется wait_timeout)
        
        Returns:
            WebElement или None
        """
        if not self.driver:
            return None
        
        timeout = timeout or self.wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return element
        except TimeoutException:
            print(f"[ERROR] Элемент не найден за {timeout} секунд: {selector}")
            return None
    
    def find_element(self, selector: str, by: By = By.CSS_SELECTOR, wait: bool = True):
        """
        Поиск элемента на странице
        
        Args:
            selector: Селектор элемента
            by: Тип селектора
            wait: Ждать появления элемента или нет
        
        Returns:
            WebElement или None
        """
        if not self.driver:
            print(f"[DEBUG] find_element: Браузер не запущен, невозможно найти элемент")
            return None
        
        method_name = "CSS_SELECTOR" if by == By.CSS_SELECTOR else str(by)
        print(f"[DEBUG] find_element: Поиск элемента selector='{selector}', method={method_name}, wait={wait}")
        
        try:
            if wait:
                element = self.wait_for_element(selector, by)
            else:
                element = self.driver.find_element(by, selector)
            
            if element:
                try:
                    tag = element.tag_name
                    elem_id = element.get_attribute("id") or ""
                    elem_name = element.get_attribute("name") or ""
                    elem_type = element.get_attribute("type") or ""
                    print(f"[DEBUG] find_element: Элемент найден! tag={tag}, id='{elem_id}', name='{elem_name}', type='{elem_type}'")
                except:
                    print(f"[DEBUG] find_element: Элемент найден (не удалось получить атрибуты)")
            else:
                print(f"[DEBUG] find_element: Элемент не найден (wait_for_element вернул None)")
            
            return element
        except NoSuchElementException:
            print(f"[ERROR] Элемент не найден (NoSuchElementException): {selector}")
            return None
        except Exception as e:
            print(f"[ERROR] Исключение при поиске элемента: {e}")
            return None
    
    def find_elements(self, selector: str, by: By = By.CSS_SELECTOR):
        """
        Поиск всех элементов по селектору
        
        Args:
            selector: Селектор элемента
            by: Тип селектора
        
        Returns:
            Список WebElement
        """
        if not self.driver:
            return []
        
        try:
            elements = self.driver.find_elements(by, selector)
            return elements
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске элементов: {e}")
            return []
    
    def click(self, selector: str, by: By = By.CSS_SELECTOR, wait: bool = True, scroll: bool = True):
        """
        Клик по элементу
        
        Args:
            selector: Селектор элемента
            by: Тип селектора
            wait: Ждать появления элемента
            scroll: Прокрутить к элементу перед кликом
        
        Returns:
            True если успешно, False иначе
        """
        element = self.find_element(selector, by, wait)
        if not element:
            return False
        
        try:
            if scroll:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
            
            # Пробуем обычный клик
            try:
                element.click()
            except:
                # Если не получилось, используем JavaScript клик
                self.driver.execute_script("arguments[0].click();", element)
            
            print(f"[OK] Клик выполнен: {selector}")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при клике: {e}")
            return False
    
    def type_text(self, selector: str, text: str, by: By = By.CSS_SELECTOR, clear: bool = True):
        """
        Ввод текста в поле
        
        Args:
            selector: Селектор элемента
            text: Текст для ввода
            by: Тип селектора
            clear: Очистить поле перед вводом
        
        Returns:
            True если успешно, False иначе
        """
        method_name = "CSS_SELECTOR" if by == By.CSS_SELECTOR else str(by)
        print(f"[DEBUG] type_text: Попытка ввода текста selector='{selector}', method={method_name}, text_length={len(text)}, clear={clear}")
        
        element = self.find_element(selector, by)
        if not element:
            print(f"[ERROR] type_text: Не удалось найти элемент для ввода текста: selector='{selector}', method={method_name}")
            return False
        
        try:
            # Получаем информацию об элементе
            element_tag = element.tag_name
            element_type = element.get_attribute("type") or ""
            element_name = element.get_attribute("name") or ""
            element_id = element.get_attribute("id") or ""
            element_placeholder = element.get_attribute("placeholder") or ""
            print(f"[DEBUG] type_text: Элемент найден - tag={element_tag}, type='{element_type}', name='{element_name}', id='{element_id}', placeholder='{element_placeholder}'")
            
            if clear:
                print(f"[DEBUG] type_text: Очистка поля перед вводом")
                element.clear()
            
            print(f"[DEBUG] type_text: Ввод текста '{text[:50]}...'")
            element.send_keys(text)
            
            # Проверяем, что текст был введен
            entered_value = element.get_attribute("value") or ""
            print(f"[DEBUG] type_text: Текст введен успешно! entered_length={len(entered_value)}, entered_preview='{entered_value[:50]}...'")
            print(f"[OK] Текст введен в {selector}: {text[:50]}...")
            return True
        except Exception as e:
            print(f"[ERROR] type_text: Ошибка при вводе текста: {e}")
            import traceback
            print(f"[ERROR] type_text: Traceback: {traceback.format_exc()}")
            return False
    
    def type_text_direct(self, text: str, press_enter: bool = False):
        """
        Ввод текста напрямую через клавиатуру в активный элемент (для contenteditable)
        
        Args:
            text: Текст для ввода
            press_enter: Нажать Enter после ввода
            
        Returns:
            True если успешно, False иначе
        """
        if not self.driver:
            print(f"[ERROR] type_text_direct: Браузер не запущен")
            return False
        
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Получаем активный элемент (body или текущий фокус)
            active_element = self.driver.switch_to.active_element
            
            print(f"[DEBUG] type_text_direct: Ввод текста через клавиатуру: '{text[:50]}...'")
            
            # Используем ActionChains для более надежного ввода
            actions = ActionChains(self.driver)
            actions.send_keys(text)
            if press_enter:
                actions.send_keys(Keys.RETURN)
            actions.perform()
            
            print(f"[OK] Текст введен через клавиатуру: {text[:50]}...")
            return True
        except Exception as e:
            print(f"[ERROR] type_text_direct: Ошибка при вводе текста: {e}")
            # Fallback - пробуем через driver напрямую
            try:
                self.driver.switch_to.active_element.send_keys(text)
                if press_enter:
                    self.driver.switch_to.active_element.send_keys(Keys.RETURN)
                print(f"[OK] Текст введен через fallback метод")
                return True
            except Exception as e2:
                print(f"[ERROR] type_text_direct: Fallback тоже не сработал: {e2}")
                return False
    
    def get_text(self, selector: str, by: By = By.CSS_SELECTOR) -> Optional[str]:
        """
        Получение текста элемента
        
        Args:
            selector: Селектор элемента
            by: Тип селектора
        
        Returns:
            Текст элемента или None
        """
        element = self.find_element(selector, by)
        if not element:
            return None
        
        try:
            text = element.text
            return text
        except Exception as e:
            print(f"[ERROR] Ошибка при получении текста: {e}")
            return None
    
    def get_attribute(self, selector: str, attribute: str, by: By = By.CSS_SELECTOR) -> Optional[str]:
        """
        Получение атрибута элемента
        
        Args:
            selector: Селектор элемента
            attribute: Название атрибута (например, "href", "value")
            by: Тип селектора
        
        Returns:
            Значение атрибута или None
        """
        element = self.find_element(selector, by)
        if not element:
            return None
        
        try:
            value = element.get_attribute(attribute)
            return value
        except Exception as e:
            print(f"[ERROR] Ошибка при получении атрибута: {e}")
            return None
    
    def read_page_content(self) -> Dict[str, Any]:
        """
        Чтение и анализ содержимого страницы в текстовом формате
        
        Returns:
            Словарь с детальной информацией о странице
        """
        if not self.driver:
            return {}
        
        try:
            # Базовая информация
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Извлекаем кнопки с деталями
            buttons = []
            try:
                for btn in self.driver.find_elements(By.TAG_NAME, "button")[:30]:
                    btn_text = btn.text.strip() if btn.text else ""
                    btn_id = btn.get_attribute("id") or ""
                    btn_class = btn.get_attribute("class") or ""
                    btn_type = btn.get_attribute("type") or "button"
                    
                    if btn_text or btn_id:
                        buttons.append({
                            "text": btn_text,
                            "id": btn_id,
                            "class": btn_class,
                            "type": btn_type
                        })
            except Exception as e:
                print(f"[WARNING] Ошибка при извлечении кнопок: {e}")
            
            # Извлекаем input поля с деталями
            inputs = []
            try:
                for inp in self.driver.find_elements(By.TAG_NAME, "input")[:30]:
                    inp_type = inp.get_attribute("type") or "text"
                    inp_name = inp.get_attribute("name") or ""
                    inp_id = inp.get_attribute("id") or ""
                    inp_placeholder = inp.get_attribute("placeholder") or ""
                    inp_value = inp.get_attribute("value") or ""
                    
                    inputs.append({
                        "type": inp_type,
                        "name": inp_name,
                        "id": inp_id,
                        "placeholder": inp_placeholder,
                        "value": inp_value
                    })
            except Exception as e:
                print(f"[WARNING] Ошибка при извлечении полей ввода: {e}")
            
            # Извлекаем ссылки с текстом
            links = []
            try:
                for link in self.driver.find_elements(By.TAG_NAME, "a")[:30]:
                    link_text = link.text.strip() if link.text else ""
                    link_href = link.get_attribute("href") or ""
                    
                    if link_text or link_href:
                        links.append({
                            "text": link_text,
                            "href": link_href
                        })
            except Exception as e:
                print(f"[WARNING] Ошибка при извлечении ссылок: {e}")
            
            # Извлекаем заголовки
            headings = []
            try:
                for tag in ["h1", "h2", "h3"]:
                    for heading in self.driver.find_elements(By.TAG_NAME, tag)[:10]:
                        heading_text = heading.text.strip() if heading.text else ""
                        if heading_text:
                            headings.append({
                                "level": tag,
                                "text": heading_text
                            })
            except Exception as e:
                print(f"[WARNING] Ошибка при извлечении заголовков: {e}")
            
            # Извлекаем текстовые элементы (div, span, p с видимым текстом)
            visible_text = []
            try:
                for tag in ["div", "span", "p", "label"]:
                    for elem in self.driver.find_elements(By.TAG_NAME, tag)[:50]:
                        elem_text = elem.text.strip() if elem.text else ""
                        if elem_text and len(elem_text) > 5 and len(elem_text) < 200:
                            visible_text.append(elem_text)
            except Exception as e:
                print(f"[WARNING] Ошибка при извлечении текста: {e}")
            
            content = {
                "title": self.driver.title,
                "url": self.driver.current_url,
                "buttons": buttons,
                "inputs": inputs,
                "links": links,
                "headings": headings,
                "visible_text": list(set(visible_text))[:50],  # Уникальные тексты
                "body_text_preview": body_text[:500]  # Первые 500 символов основного текста
            }
            return content
        except Exception as e:
            print(f"[ERROR] Ошибка при чтении содержимого: {e}")
            return {}
    
    def wait(self, seconds: float):
        """
        Ожидание указанное количество секунд
        
        Args:
            seconds: Количество секунд для ожидания
        """
        time.sleep(seconds)
    
    def scroll_to_bottom(self):
        """Прокрутка страницы вниз"""
        if not self.driver:
            return
        
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
    
    def scroll_to_top(self):
        """Прокрутка страницы вверх"""
        if not self.driver:
            return
        
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    
    def execute_script(self, script: str):
        """
        Выполнение JavaScript кода
        
        Args:
            script: JavaScript код для выполнения
        """
        if not self.driver:
            return None
        
        try:
            result = self.driver.execute_script(script)
            return result
        except Exception as e:
            print(f"[ERROR] Ошибка при выполнении скрипта: {e}")
            return None
    
    def take_screenshot(self, filename: str = "screenshot.png"):
        """
        Создание скриншота страницы
        
        Args:
            filename: Имя файла для сохранения
        """
        if not self.driver:
            return False
        
        try:
            self.driver.save_screenshot(filename)
            print(f"[OK] Скриншот сохранен: {filename}")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка при создании скриншота: {e}")
            return False
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("[OK] Браузер закрыт")
    
    def __enter__(self):
        """Поддержка контекстного менеджера"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие при выходе из контекста"""
        self.close()
