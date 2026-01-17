"""
Исполнитель сценариев
Выполняет сценарии автоматизации через AI контроллер
"""

import logging
import threading
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
        self.waiting_for_user = False
        self._user_input_event = threading.Event()
        self._user_input_value: Optional[str] = None
        self._user_inputs: Dict[str, str] = {}
        self._waiting_input_key: Optional[str] = None
        self._waiting_input_prompt: Optional[str] = None
        
        # Callbacks для обновления UI
        self.progress_callback: Optional[Callable] = None
        self.complete_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        self.message_callback: Optional[Callable[[str], None]] = None
    
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
        if self.waiting_for_user:
            self._user_input_event.set()
    
    def set_progress_callback(self, callback: Callable):
        """Установка callback для обновления прогресса"""
        self.progress_callback = callback
    
    def set_complete_callback(self, callback: Callable):
        """Установка callback для завершения"""
        self.complete_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """Установка callback для ошибок"""
        self.error_callback = callback
    
    def set_message_callback(self, callback: Callable[[str], None]):
        """Установка callback для сообщений"""
        self.message_callback = callback
    
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
                    resolved_step = self._resolve_step_variables(step)
                    success = self._execute_step(resolved_step)
                
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
        
        action = step.get('action')
        
        # Ожидание пользователя
        if action == 'wait_user':
            return self._execute_wait_user(step)
        
        # Выполнение решения AI по извлеченному контенту
        if action == 'ai_decide':
            return self._execute_ai_decide(step)
        
        # Специальная обработка для ai_analyze
        if action == 'ai_analyze':
            return self._execute_ai_analyze(step)
        
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
        
        ВАЖНО: Для сценариев AI используется минимально - только когда действительно необходимо.
        Executor уже поддерживает поиск по тексту через XPath, поэтому method="text" 
        выполняется напрямую без AI.
        
        Логика для сценариев:
        - method == "text" → прямое выполнение (executor использует XPath)
        - action == "type" с field (без selector) → использовать AI (нужен анализ страницы)
        - В остальных случаях → прямое выполнение
        
        Примечание: AI используется в основном для интерактивного режима (чат).
        Для сценариев предпочтительно использовать четкие селекторы для скорости и надежности.
        
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
        
        # ai_analyze всегда использует AI
        if action == 'ai_analyze':
            return True
        
        # Для method == "text" → прямое выполнение (executor использует XPath: //*[text()='...'])
        # Это работает для кнопок, ссылок и других элементов с текстом
        # НЕ используем AI, так как executor уже умеет искать по тексту
        if method == 'text':
            return False
        
        # Для type с field (текстовое описание поля БЕЗ selector) → использовать AI
        # AI нужен для анализа страницы и поиска поля по label, placeholder и т.д.
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
    
    def _execute_ai_decide(self, step: Dict[str, Any]) -> bool:
        """
        Выполнение решения AI на основе извлеченного контента
        
        Ожидается, что AI вернет номер выбранного варианта или его текст.
        """
        if not self.ai_controller or not self.ai_controller.llm_client:
            error_msg = "AI клиент не инициализирован"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False

    def _execute_wait_user(self, step: Dict[str, Any]) -> bool:
        """Ожидание пользовательского ввода через чат."""
        prompt = step.get('message', 'Ожидается ввод пользователя.')
        store_as = step.get('store_as')
        timeout = step.get('timeout')
        
        self.waiting_for_user = True
        self._waiting_input_key = store_as
        self._waiting_input_prompt = prompt
        self._user_input_value = None
        self._user_input_event.clear()
        
        self._emit_message(
            "⏸ Ожидание пользователя\n"
            f"{prompt}\n"
            "Введите ответ в чат, чтобы продолжить."
        )
        
        if timeout is not None:
            try:
                timeout = float(timeout)
            except Exception:
                timeout = None
        
        if timeout and timeout > 0:
            self._user_input_event.wait(timeout=timeout)
        else:
            while not self.stop_requested and not self._user_input_event.is_set():
                self._user_input_event.wait(timeout=0.2)
        
        self.waiting_for_user = False
        
        if self.stop_requested:
            return False
        
        if self._user_input_value is None and timeout:
            if self.error_callback:
                self.error_callback("Время ожидания ответа пользователя истекло")
            return False
        
        return True
        
        # Извлекаем контекст (вопрос/описание)
        context_text = step.get('context_text')
        if not context_text and step.get('context_selector'):
            context_text = self._extract_context_text(
                step.get('context_selector'),
                step.get('context_method', 'css')
            )
        
        if not context_text:
            error_msg = "Не удалось извлечь контекст для ai_decide"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        # Извлекаем варианты ответа
        options = step.get('options')
        option_elements = None
        if not options and step.get('options_selector'):
            option_elements = self._find_elements(
                step.get('options_selector'),
                step.get('options_method', 'css'),
                visible_only=True
            )
            options = self._extract_options_text(option_elements)
        
        if not options:
            error_msg = "Не удалось получить варианты для ai_decide"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        # Формируем запрос к AI
        prompt = step.get('prompt', 'Выбери правильный вариант.')
        options_lines = [f"{i + 1}) {opt}" for i, opt in enumerate(options)]
        user_prompt = (
            f"{prompt}\n\n"
            f"Вопрос/контекст:\n{context_text}\n\n"
            f"Варианты:\n" + "\n".join(options_lines) + "\n\n"
            "Ответ: укажи только номер варианта."
        )
        self._emit_message(
            "AI решение: отправлены данные\n"
            f"Промпт: {prompt}\n"
            f"Контекст:\n{context_text}\n"
            "Варианты:\n" + "\n".join(options_lines)
        )
        
        system_prompt = (
            "Ты выбираешь один вариант ответа. "
            "Верни только номер варианта (например, 2) без лишнего текста."
        )
        
        max_retries = step.get('max_retries', 1)
        response = None
        choice_index = None
        
        for attempt in range(max_retries + 1):
            try:
                response = self.ai_controller.llm_client.chat(
                    user_prompt,
                    system_prompt=system_prompt,
                    max_tokens=50
                )
            except Exception as e:
                error_msg = f"Ошибка при обращении к AI: {str(e)}"
                logger.exception(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False
            
            choice_index = self._parse_choice_index(response, options)
            if choice_index is not None and 1 <= choice_index <= len(options):
                break
            
            logger.warning(
                "AI вернул недопустимый номер, повторяем запрос: "
                f"ответ='{response}'"
            )
            self._emit_message(
                "AI решение: некорректный ответ, повтор запроса\n"
                f"Сырой ответ: {response}"
            )
            choice_index = None
        
        if choice_index is None:
            logger.warning("AI не вернул корректный номер, выбираем первый вариант")
            choice_index = 1
        
        logger.info(f"AI выбрал вариант: {choice_index}")
        self._emit_message(
            "AI решение: ответ\n"
            f"Сырой ответ: {response}\n"
            f"Выбранный вариант: {choice_index}"
        )
        
        # Если заданы шаги для выбранного варианта - выполняем их
        choice_steps = step.get('choice_steps')
        if choice_steps:
            if 1 <= choice_index <= len(choice_steps):
                return self._execute_steps(choice_steps[choice_index - 1])
            error_msg = f"Выбранный индекс вне диапазона choice_steps: {choice_index}"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        # Иначе кликаем по выбранному элементу
        click_selector = step.get('click_selector') or step.get('options_selector')
        click_method = step.get('click_method') or step.get('options_method', 'css')
        if not click_selector:
            error_msg = "Для ai_decide не указан click_selector/options_selector"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        click_elements = self._find_elements(click_selector, click_method, visible_only=True)
        if not click_elements or choice_index < 1 or choice_index > len(click_elements):
            error_msg = f"Не удалось найти элемент для выбора варианта {choice_index}"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        try:
            element = click_elements[choice_index - 1]
            target = element
            try:
                if element.tag_name.lower() == "input":
                    label_el = self._find_associated_label(element)
                    if label_el:
                        target = label_el
            except Exception:
                pass
            # Прокрутка в центр экрана, чтобы избежать перекрытия фиксированной шапкой
            self.clicker.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
                target
            )
            try:
                self.clicker.wait(0.2)
            except Exception:
                pass
            try:
                target.click()
            except Exception:
                # Фоллбэк: клик через JS (для перекрытий)
                self.clicker.driver.execute_script("arguments[0].click();", target)
            return True
        except Exception as e:
            error_msg = f"Ошибка клика по выбранному варианту: {str(e)}"
            logger.exception(error_msg)
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
    
    def _execute_ai_analyze(self, step: Dict[str, Any]) -> bool:
        """
        Выполнение AI анализа текста/контента
        
        Args:
            step: Шаг с действием ai_analyze
            
        Returns:
            True если анализ выполнен успешно
        """
        prompt = step.get('prompt')
        text = step.get('text')
        selector = step.get('selector')
        
        # Получаем текст для анализа
        text_to_analyze = None
        
        if text:
            # Текст указан напрямую
            text_to_analyze = text
        elif selector:
            # Нужно получить текст из элемента
            method = step.get('method', 'css')
            try:
                from selenium.webdriver.common.by import By
                method_map = {
                    'css': By.CSS_SELECTOR,
                    'xpath': By.XPATH,
                    'id': By.ID,
                    'name': By.NAME,
                    'class': By.CLASS_NAME,
                    'tag': By.TAG_NAME
                }
                by = method_map.get(method, By.CSS_SELECTOR)
                
                element = self.clicker.find_element(selector, by)
                if element:
                    text_to_analyze = element.text
                else:
                    error_msg = f"Не удалось найти элемент для анализа: {selector}"
                    logger.error(error_msg)
                    if self.error_callback:
                        self.error_callback(error_msg)
                    return False
            except Exception as e:
                error_msg = f"Ошибка при получении текста из элемента: {str(e)}"
                logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False
        else:
            error_msg = "ai_analyze требует либо 'text', либо 'selector'"
            logger.error(error_msg)
            if self.error_callback:
                self.error_callback(error_msg)
            return False
        
        # Формируем запрос для AI
        ai_prompt = f"{prompt}\n\nТекст для анализа:\n{text_to_analyze}"
        self._emit_message(
            "AI анализ: отправлены данные\n"
            f"Промпт: {prompt}\n"
            f"Текст:\n{text_to_analyze}"
        )
        
        try:
            # Выполняем анализ через AI (без контекста страницы, так как текст уже получен)
            result = self.ai_controller.llm_client.chat(
                ai_prompt,
                system_prompt="Ты помощник для анализа текста. Анализируй текст и отвечай на вопросы пользователя кратко и точно.",
                max_tokens=300
            )
            
            if result:
                logger.info(f"AI анализ выполнен: {result[:100]}...")
                self._emit_message(f"AI анализ: ответ\n{result}")
                # Результат можно использовать дальше, но пока просто логируем
                return True
            else:
                error_msg = "AI не вернул результат анализа"
                logger.error(error_msg)
                if self.error_callback:
                    self.error_callback(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Ошибка при выполнении AI анализа: {str(e)}"
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
            # Поддержка прямого ввода через клавиатуру (для contenteditable)
            if "use_keyboard" in step:
                command_dict["use_keyboard"] = step["use_keyboard"]
            
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
        elif action == 'ai_analyze':
            prompt = step.get('prompt', '')
            if len(prompt) > 50:
                prompt = prompt[:50] + '...'
            return f"AI анализ: {prompt}"
        elif action == 'ai_decide':
            prompt = step.get('prompt', '')
            if len(prompt) > 50:
                prompt = prompt[:50] + '...'
            return f"AI решение: {prompt}"
        elif action == 'wait_user':
            message = step.get('message', '')
            if len(message) > 50:
                message = message[:50] + '...'
            return f"Ожидание пользователя: {message}"
        else:
            return f"{action}"

    def _find_elements(self, selector: str, method: str, visible_only: bool = True) -> List[Any]:
        """Поиск элементов с фильтрацией видимости."""
        if not self.clicker or not self.clicker.driver:
            return []
        try:
            from selenium.webdriver.common.by import By
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
            if not visible_only:
                return elements
            return [el for el in elements if el.is_displayed()]
        except Exception:
            return []
    
    def _extract_context_text(self, selector: str, method: str) -> Optional[str]:
        """Извлекает наиболее подходящий текст из набора элементов."""
        elements = self._find_elements(selector, method, visible_only=True)
        if not elements:
            return None
        texts = [el.text.strip() for el in elements if el.text and el.text.strip()]
        if not texts:
            return None
        # Предпочитаем текст с вопросительным знаком, иначе самый длинный
        for text in texts:
            if "?" in text:
                return text
        return max(texts, key=len)
    
    def _extract_options_text(self, elements: Optional[List[Any]]) -> List[str]:
        """Извлекает тексты вариантов из элементов."""
        if not elements:
            return []
        options = []
        for el in elements:
            text = (el.text or "").strip()
            try:
                if el.tag_name.lower() == "input":
                    label_el = self._find_associated_label(el)
                    if label_el and label_el.text:
                        text = label_el.text.strip()
            except Exception:
                pass
            if not text:
                # Пробуем атрибуты
                for attr in ["aria-label", "value", "title", "data-answer", "data-title"]:
                    value = el.get_attribute(attr)
                    if value:
                        text = value.strip()
                        break
            if text == "on":
                text = ""
            if not text:
                # Пробуем связанный label по id
                el_id = el.get_attribute("id")
                if el_id:
                    try:
                        label = self.clicker.driver.find_element(
                            "xpath", f"//label[@for='{el_id}']"
                        )
                        if label and label.text:
                            text = label.text.strip()
                    except Exception:
                        pass
            if not text:
                # Пробуем текст родителя
                try:
                    parent = el.find_element("xpath", "..")
                    if parent and parent.text:
                        text = parent.text.strip()
                except Exception:
                    pass
            if text:
                options.append(text)
        return options

    def _find_associated_label(self, element: Any) -> Optional[Any]:
        """Пытается найти label, связанный с input."""
        try:
            from selenium.webdriver.common.by import By
            el_id = element.get_attribute("id")
            if el_id:
                labels = self.clicker.driver.find_elements(By.CSS_SELECTOR, f"label[for='{el_id}']")
                if labels:
                    return labels[0]
            labels = element.find_elements(By.XPATH, "ancestor::label[1]")
            if labels:
                return labels[0]
            labels = element.find_elements(By.XPATH, "following-sibling::label[1]")
            if labels:
                return labels[0]
            labels = element.find_elements(By.XPATH, "parent::label")
            if labels:
                return labels[0]
        except Exception:
            return None
        return None
    
    def _parse_choice_index(self, response: Optional[str], options: List[str]) -> Optional[int]:
        """Пытается получить индекс выбора из ответа AI."""
        if not response:
            return None
        text = response.strip()
        
        # Попытка извлечь число
        try:
            import re
            match = re.search(r"\b(\d{1,2})\b", text)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        
        # Попытка сопоставить по тексту варианта
        lowered = text.lower()
        for i, opt in enumerate(options, start=1):
            if opt and opt.lower() in lowered:
                return i
        
        return None

    def _emit_message(self, message: str) -> None:
        """Отправляет сообщение в UI (если задан callback)."""
        if self.message_callback:
            try:
                self.message_callback(message)
            except Exception:
                pass

    def provide_user_input(self, message: str) -> None:
        """Передает ввод пользователя для продолжения сценария."""
        if not self.waiting_for_user:
            return
        text = (message or "").strip()
        if not text:
            text = message or ""
        self._user_input_value = text
        self._user_inputs["last_user_input"] = text
        if self._waiting_input_key:
            self._user_inputs[self._waiting_input_key] = text
        self._user_input_event.set()

    def is_waiting_for_user(self) -> bool:
        """Признак ожидания пользовательского ввода."""
        return self.waiting_for_user

    def _resolve_step_variables(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Подстановка пользовательских значений в шаг сценария."""
        if not self._user_inputs:
            return step
        
        def replace_value(value: Any) -> Any:
            if not isinstance(value, str):
                return value
            for key, stored in self._user_inputs.items():
                value = value.replace(f"{{{{{key}}}}}", stored)
            return value
        
        resolved = {}
        for key, value in step.items():
            if isinstance(value, dict):
                resolved[key] = {k: replace_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                resolved[key] = [replace_value(item) for item in value]
            else:
                resolved[key] = replace_value(value)
        return resolved
