"""
Исполнитель сценариев
Выполняет сценарии автоматизации через AI контроллер
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from .parser import ScenarioParser
from .validator import ScenarioValidator

# Настройка логирования
logger = logging.getLogger(__name__)

# Таймаут для выполнения AI-команд (в секундах)
AI_COMMAND_TIMEOUT = 60


class ScenarioExecutor:
    """Исполнитель сценариев автоматизации"""
    
    def __init__(self, ai_controller, clicker, continue_on_error: bool = False):
        """
        Инициализация исполнителя
        
        Args:
            ai_controller: Экземпляр AIController для выполнения команд
            clicker: Экземпляр WebClicker (для проверки состояния браузера)
            continue_on_error: Продолжать выполнение при ошибке (по умолчанию False - останавливать)
        """
        self.ai_controller = ai_controller
        self.clicker = clicker
        self.continue_on_error = continue_on_error
        self.stop_requested = False
        self.current_step_index = 0
        self.total_steps = 0
        self.current_scenario = None
        self.errors_count = 0
        
        # Callbacks для обновления UI
        self.progress_callback: Optional[Callable] = None
        self.complete_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
    
    def execute(self, scenario: Dict[str, Any]) -> bool:
        """
        Выполнение сценария
        
        Args:
            scenario: Сценарий для выполнения
            
        Returns:
            True если выполнение завершено успешно, False при ошибке или остановке
        """
        scenario_name = scenario.get('name', 'Неизвестный сценарий')
        logger.info(f"Начало выполнения сценария: {scenario_name}")
        
        # Валидация сценария
        is_valid, error = ScenarioValidator.validate(scenario)
        if not is_valid:
            error_msg = f"Ошибка валидации сценария: {error}"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        self.current_scenario = scenario
        self.stop_requested = False
        self.current_step_index = 0
        self.errors_count = 0
        
        # Подсчет общего количества шагов (включая вложенные)
        self.total_steps = self._count_steps(scenario['steps'])
        logger.info(f"Всего шагов для выполнения: {self.total_steps}")
        
        try:
            # Выполнение шагов
            success = self._execute_steps(scenario['steps'])
            
            if self.stop_requested:
                logger.warning("Сценарий остановлен пользователем")
                if self.complete_callback:
                    self.complete_callback(stopped=True, message="Сценарий остановлен пользователем")
                return False
            
            if success:
                message = f"Сценарий выполнен успешно"
                if self.errors_count > 0:
                    message += f" (с {self.errors_count} ошибками)"
                logger.info(message)
                if self.complete_callback:
                    self.complete_callback(stopped=False, message=message)
            else:
                logger.error(f"Сценарий завершился с ошибками. Всего ошибок: {self.errors_count}")
            
            return success
            
        except Exception as e:
            error_msg = f"Критическая ошибка при выполнении сценария: {str(e)}"
            logger.exception(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        finally:
            logger.info(f"Завершение выполнения сценария: {scenario_name}")
            self.current_scenario = None
    
    def stop(self):
        """Остановка выполнения сценария"""
        self.stop_requested = True
    
    def set_progress_callback(self, callback: Callable):
        """Установка callback для обновления прогресса"""
        self.progress_callback = callback
    
    def set_complete_callback(self, callback: Callable):
        """Установка callback для завершения"""
        self.complete_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Установка callback для ошибок"""
        self.error_callback = callback
    
    def _count_steps(self, steps: List[Dict[str, Any]]) -> int:
        """
        Подсчет общего количества шагов (рекурсивно)
        
        Примечание: Подсчитывает количество уникальных шагов в структуре сценария,
        не учитывая количество итераций циклов (repeat). Это сделано намеренно
        для отображения структуры сценария, а не общего числа выполненных операций.
        Для точного подсчета итераций потребовалась бы более сложная логика с
        предварительным вычислением условий циклов.
        
        Args:
            steps: Список шагов
            
        Returns:
            Количество уникальных шагов в структуре сценария
        """
        count = 0
        for step in steps:
            count += 1
            if step.get('action') == 'repeat' and 'steps' in step:
                # Подсчитываем вложенные шаги, но не умножаем на количество итераций
                count += self._count_steps(step['steps'])
        return count
    
    def _execute_steps(self, steps: List[Dict[str, Any]]) -> bool:
        """
        Выполнение списка шагов
        
        Args:
            steps: Список шагов для выполнения
            
        Returns:
            True если выполнение успешно
        """
        all_steps_success = True
        
        for step in steps:
            if self.stop_requested:
                return False
            
            self.current_step_index += 1
            
            # Обновление прогресса
            if self.progress_callback:
                status = self._get_step_description(step)
                self.progress_callback(self.current_step_index, self.total_steps, status)
            
            step_description = self._get_step_description(step)
            logger.info(f"Выполнение шага {self.current_step_index}/{self.total_steps}: {step_description}")
            logger.debug(f"Детали шага: {step}")
            
            # Выполнение шага
            try:
                if step['action'] == 'repeat':
                    success = self._execute_repeat(step)
                else:
                    success = self._execute_step(step)
                
                if success:
                    logger.info(f"Шаг {self.current_step_index} выполнен успешно: {step_description}")
                else:
                    self.errors_count += 1
                    error_msg = f"Ошибка на шаге {self.current_step_index}: {step_description}"
                    logger.error(error_msg)
                    
                    if self.error_callback:
                        self.error_callback(error_msg)
                    
                    if not self.continue_on_error:
                        # Останавливаем выполнение, если не установлен флаг continue_on_error
                        logger.warning("Остановка выполнения сценария из-за ошибки (continue_on_error=False)")
                        return False
                    else:
                        # Продолжаем выполнение
                        logger.warning(f"Продолжение выполнения после ошибки (continue_on_error=True)")
                        all_steps_success = False
                
            except Exception as e:
                self.errors_count += 1
                error_msg = f"Исключение на шаге {self.current_step_index}: {step_description} - {str(e)}"
                logger.exception(error_msg)
                
                if self.error_callback:
                    self.error_callback(error_msg)
                
                if not self.continue_on_error:
                    return False
                else:
                    all_steps_success = False
            
            if self.stop_requested:
                return False
        
        return all_steps_success
    
    def _execute_repeat(self, repeat_block: Dict[str, Any]) -> bool:
        """
        Выполнение блока repeat (цикл)
        
        Args:
            repeat_block: Блок repeat
            
        Returns:
            True если выполнение успешно
        """
        repeat_type = repeat_block['type']
        nested_steps = repeat_block['steps']
        
        if repeat_type == 'until_stopped':
            iteration = 0
            while not self.stop_requested:
                iteration += 1
                if self.progress_callback:
                    self.progress_callback(
                        self.current_step_index,
                        self.total_steps,
                        f"Цикл: итерация {iteration}"
                    )
                
                if not self._execute_steps(nested_steps):
                    return False
                
                if self.stop_requested:
                    break
        
        elif repeat_type == 'count':
            times = repeat_block.get('times', 1)
            for iteration in range(1, times + 1):
                if self.stop_requested:
                    break
                
                if self.progress_callback:
                    self.progress_callback(
                        self.current_step_index,
                        self.total_steps,
                        f"Цикл: итерация {iteration} из {times}"
                    )
                
                if not self._execute_steps(nested_steps):
                    return False
        
        elif repeat_type == 'while':
            condition = repeat_block.get('condition')
            selector = repeat_block.get('selector')
            method = repeat_block.get('method', 'css')
            iteration = 0
            
            while not self.stop_requested:
                # Проверка условия
                condition_met = self._check_condition(condition, selector, method)
                if not condition_met:
                    break
                
                iteration += 1
                if self.progress_callback:
                    self.progress_callback(
                        self.current_step_index,
                        self.total_steps,
                        f"Цикл while: итерация {iteration}"
                    )
                
                if not self._execute_steps(nested_steps):
                    return False
        
        return True
    
    def _check_condition(self, condition: str, selector: str, method: str) -> bool:
        """
        Проверка условия для цикла while
        
        Args:
            condition: Тип условия ('element_exists', 'element_not_exists')
            selector: Селектор элемента
            method: Метод селектора
            
        Returns:
            True если условие выполнено
        """
        if not self.clicker or not self.clicker.driver:
            return False
        
        try:
            from selenium.webdriver.common.by import By
            
            # Маппинг методов
            method_map = {
                'css': By.CSS_SELECTOR,
                'xpath': By.XPATH,
                'id': By.ID,
                'name': By.NAME,
                'class': By.CLASS_NAME,
                'tag': By.TAG_NAME
            }
            
            by = method_map.get(method, By.CSS_SELECTOR)
            elements = self.clicker.driver.find_elements(by, selector)
            
            if condition == 'element_exists':
                return len(elements) > 0
            elif condition == 'element_not_exists':
                return len(elements) == 0
            
        except Exception:
            return False
        
        return False
    
    def _execute_step(self, step: Dict[str, Any]) -> bool:
        """
        Выполнение одного шага (гибридный подход: AI или прямое выполнение)
        
        Args:
            step: Шаг для выполнения
            
        Returns:
            True если выполнение успешно
        """
        if not self.ai_controller:
            if self.error_callback:
                self.error_callback("AI контроллер не инициализирован")
            return False
        
        # Определяем, нужно ли использовать AI или прямое выполнение
        use_ai = self._should_use_ai(step)
        
        if use_ai:
            # Выполнение через AI (для текстовых команд или нечетких селекторов)
            return self._execute_step_via_ai(step)
        else:
            # Прямое выполнение (для четких селекторов)
            return self._execute_step_direct(step)
    
    def _should_use_ai(self, step: Dict[str, Any]) -> bool:
        """
        Определение, нужно ли использовать AI для выполнения шага
        
        Логика гибридного подхода:
        - Если method == "text" → использовать AI (гибкий поиск по тексту)
        - Если action == "type" и указан field (текстовое описание) → использовать AI
        - Если action == "click" и method == "text" → использовать AI
        - В остальных случаях → прямое выполнение
        
        Args:
            step: Шаг сценария
            
        Returns:
            True если нужно использовать AI, False для прямого выполнения
        """
        action = step.get('action')
        method = step.get('method', 'css')
        
        # Для действий, которые всегда выполняются напрямую
        direct_actions = ['navigate', 'wait', 'scroll', 'screenshot']
        if action in direct_actions:
            return False
        
        # Для click и type с method == "text" → использовать AI
        if method == 'text':
            return True
        
        # Для type с field (текстовое описание поля) → использовать AI
        if action == 'type' and 'field' in step and 'selector' not in step:
            return True
        
        # В остальных случаях (четкие селекторы) → прямое выполнение
        return False
    
    def _execute_step_via_ai(self, step: Dict[str, Any]) -> bool:
        """
        Выполнение шага через AI контроллер с таймаутом и fallback на прямое выполнение
        
        Args:
            step: Шаг для выполнения
            
        Returns:
            True если выполнение успешно
        """
        try:
            # Формируем текстовую инструкцию для AI
            instruction = self._step_to_ai_instruction(step)
            if not instruction:
                error_msg = f"Не удалось сформировать инструкцию для шага: {step.get('action', 'unknown')}"
                logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False
            
            logger.info(f"Выполнение шага через AI: {instruction}")
            logger.debug(f"Детали шага для AI: {step}")
            
            # Выполняем через AI контроллер с таймаутом
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self.ai_controller.process_user_instruction, instruction)
                    result = future.result(timeout=AI_COMMAND_TIMEOUT)
            except FutureTimeoutError:
                error_msg = f"Таймаут выполнения AI-команды ({AI_COMMAND_TIMEOUT} сек): {instruction}"
                logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                # Пробуем fallback на прямое выполнение, если есть селектор
                return self._try_fallback_to_direct(step, "таймаут AI-команды")
            except Exception as e:
                error_msg = f"Исключение при выполнении AI-команды: {str(e)}"
                logger.exception(error_msg)
                # Пробуем fallback на прямое выполнение, если есть селектор
                return self._try_fallback_to_direct(step, error_msg)
            
            if not result.get("success", False):
                error_msg = result.get("message", "Неизвестная ошибка")
                logger.error(f"Ошибка выполнения шага через AI: {error_msg}")
                logger.error(f"Детали ошибки: шаг={step.get('action')}, селектор={step.get('selector', step.get('field', 'N/A'))}, метод={step.get('method', 'N/A')}")
                # Пробуем fallback на прямое выполнение, если есть селектор
                fallback_success = self._try_fallback_to_direct(step, error_msg)
                if fallback_success:
                    logger.info(f"Успешный fallback на прямое выполнение после ошибки AI")
                    return True
                
                if self.error_callback:
                    self.error_callback(f"Ошибка выполнения шага через AI: {error_msg}")
                return False
            
            logger.info(f"Шаг выполнен успешно через AI: {instruction}")
            return True
            
        except Exception as e:
            error_msg = f"Исключение при выполнении шага через AI: {str(e)}"
            logger.exception(error_msg)
            # Пробуем fallback на прямое выполнение, если есть селектор
            fallback_success = self._try_fallback_to_direct(step, error_msg)
            if fallback_success:
                logger.info(f"Успешный fallback на прямое выполнение после исключения")
                return True
            
            if self.error_callback:
                self.error_callback(error_msg)
            return False
    
    def _try_fallback_to_direct(self, step: Dict[str, Any], ai_error: str) -> bool:
        """
        Попытка fallback на прямое выполнение после ошибки AI
        
        Args:
            step: Шаг для выполнения
            ai_error: Сообщение об ошибке AI
            
        Returns:
            True если fallback успешен, False если fallback невозможен или не удался
        """
        action = step.get('action')
        
        # Fallback возможен только для click и type, если есть селектор
        if action not in ['click', 'type']:
            return False
        
        # Для type нужен либо selector, либо field (который можно использовать как selector)
        if action == 'type':
            if 'selector' not in step and 'field' not in step:
                return False
        # Для click нужен selector
        elif action == 'click':
            if 'selector' not in step:
                return False
        
        # Проверяем, что метод не "text" (для text fallback не имеет смысла)
        method = step.get('method', 'css')
        if method == 'text':
            return False
        
        logger.info(f"Попытка fallback на прямое выполнение после ошибки AI: {ai_error}")
        try:
            return self._execute_step_direct(step)
        except Exception as e:
            logger.debug(f"Fallback на прямое выполнение не удался: {str(e)}")
            return False
    
    def _execute_step_direct(self, step: Dict[str, Any]) -> bool:
        """
        Прямое выполнение шага через executor (без AI)
        
        Args:
            step: Шаг для выполнения
            
        Returns:
            True если выполнение успешно
        """
        if not self.ai_controller.executor:
            error_msg = "Executor не инициализирован"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        # Преобразование шага сценария в формат команды
        command_dict = self._convert_step_to_command(step)
        if not command_dict:
            error_msg = f"Ошибка преобразования шага: {step.get('action', 'unknown')}"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        logger.info(f"Прямое выполнение команды: {command_dict.get('action')} - {command_dict.get('selector', command_dict.get('url', ''))}")
        
        # Выполнение команды через executor
        try:
            success, message, result = self.ai_controller.executor.execute(command_dict)
            
            if not success:
                logger.error(f"Ошибка выполнения команды: {message}")
                if self.error_callback:
                    self.error_callback(f"Ошибка выполнения шага: {message}")
                return False
            
            logger.debug(f"Команда выполнена успешно: {message}")
            return True
            
        except Exception as e:
            error_msg = f"Исключение при выполнении шага: {str(e)}"
            logger.exception(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
    
    def _step_to_ai_instruction(self, step: Dict[str, Any]) -> Optional[str]:
        """
        Преобразование шага сценария в текстовую инструкцию для AI
        
        Формулировки оптимизированы для лучшего понимания AI моделью:
        - Используются четкие глаголы действий
        - Указывается тип элемента (кнопка, поле, элемент)
        - Значения передаются явно
        
        Args:
            step: Шаг сценария
            
        Returns:
            Текстовая инструкция или None при ошибке
        """
        action = step.get('action')
        
        if action == 'click':
            selector = step.get('selector', '')
            if selector:
                # Улучшенная формулировка: не предполагаем, что это кнопка
                method = step.get('method', 'css')
                if method == 'text':
                    return f"Найди и нажми на элемент с текстом '{selector}'"
                else:
                    return f"Найди и нажми на элемент: {selector}"
            return None
        
        elif action == 'type':
            field = step.get('field') or step.get('selector', '')
            value = step.get('value', '')
            if field and value:
                # Улучшенная формулировка: явно указываем, что нужно найти поле и ввести текст
                return f"Найди поле '{field}' и введи в него текст: {value}"
            elif field:
                return f"Найди поле '{field}' и введи текст"
            return None
        
        # Для остальных действий AI не используется
        return None
    
    def _convert_step_to_command(self, step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Преобразование шага сценария в формат команды для executor
        
        Args:
            step: Шаг сценария
            
        Returns:
            Словарь команды или None при ошибке
        """
        action = step.get('action')
        if not action:
            return None
        
        command_dict = {
            "action": action,
            "method": step.get("method", "css")
        }
        
        # Преобразование параметров в зависимости от типа действия
        if action == 'navigate':
            command_dict["url"] = step.get("url")
            
        elif action == 'click':
            command_dict["selector"] = step.get("selector")
            if "scroll" in step:
                command_dict["scroll"] = step["scroll"]
            
        elif action == 'type':
            # Преобразование field в selector
            selector = step.get("selector") or step.get("field")
            if not selector:
                return None
            command_dict["selector"] = selector
            command_dict["value"] = step.get("value")
            if "clear_first" in step:
                command_dict["clear_first"] = step["clear_first"]
            if "press_enter" in step:
                command_dict["press_enter"] = step["press_enter"]
            
        elif action == 'wait':
            if "seconds" in step:
                command_dict["seconds"] = step["seconds"]
            if "wait_for_element" in step:
                command_dict["wait_for_element"] = step["wait_for_element"]
                if "selector" in step:
                    command_dict["selector"] = step["selector"]
            if "timeout" in step:
                command_dict["timeout"] = step["timeout"]
            
        elif action == 'scroll':
            command_dict["direction"] = step.get("direction", "down")
            if "pixels" in step:
                command_dict["pixels"] = step["pixels"]
            if "selector" in step:
                command_dict["selector"] = step["selector"]
            
        elif action == 'get_text':
            command_dict["selector"] = step.get("selector")
            
        elif action == 'get_attribute':
            command_dict["selector"] = step.get("selector")
            # Преобразование attribute в value (для executor)
            if "attribute" in step:
                command_dict["value"] = step["attribute"]
            
        elif action == 'screenshot':
            if "filename" in step:
                command_dict["filename"] = step["filename"]
            
        else:
            return None
        
        return command_dict
    
    def _get_step_description(self, step: Dict[str, Any]) -> str:
        """
        Получение описания шага для отображения
        
        Args:
            step: Шаг
            
        Returns:
            Описание шага
        """
        action = step.get('action', 'unknown')
        
        if action == 'navigate':
            return f"Переход на {step.get('url', '')}"
        elif action == 'click':
            return f"Клик: {step.get('selector', '')}"
        elif action == 'type':
            field = step.get('field') or step.get('selector', '')
            return f"Ввод в {field}: {step.get('value', '')}"
        elif action == 'wait':
            if 'seconds' in step:
                return f"Ожидание {step['seconds']} сек"
            else:
                return "Ожидание элемента"
        elif action == 'repeat':
            return f"Цикл ({step.get('type', '')})"
        else:
            return f"{action}"
