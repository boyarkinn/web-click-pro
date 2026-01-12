"""
Валидатор сценариев
Проверяет корректность структуры и параметров сценария
"""

from typing import Dict, Any, Tuple, Optional, List


class ScenarioValidator:
    """Валидатор для проверки корректности сценариев"""
    
    # Поддерживаемые действия
    VALID_ACTIONS = [
        'navigate', 'click', 'type', 'wait', 'scroll',
        'get_text', 'get_attribute', 'screenshot',
        'repeat'
    ]
    
    # Методы селекторов
    VALID_METHODS = ['css', 'xpath', 'id', 'name', 'class', 'tag', 'text']
    
    # Типы циклов
    VALID_REPEAT_TYPES = ['until_stopped', 'count', 'while']
    
    # Направления прокрутки
    VALID_SCROLL_DIRECTIONS = ['up', 'down', 'top', 'bottom', 'to_element']
    
    # Условия для циклов while
    VALID_WHILE_CONDITIONS = ['element_exists', 'element_not_exists']
    
    @staticmethod
    def validate(scenario: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Полная валидация сценария
        
        Args:
            scenario: Сценарий для валидации
            
        Returns:
            Tuple[bool, Optional[str]]: (валиден ли, сообщение об ошибке)
        """
        # Проверка структуры
        if not isinstance(scenario, dict):
            return False, "Сценарий должен быть объектом JSON"
        
        if 'steps' not in scenario:
            return False, "Сценарий должен содержать поле 'steps'"
        
        if not isinstance(scenario['steps'], list):
            return False, "Поле 'steps' должно быть массивом"
        
        if len(scenario['steps']) == 0:
            return False, "Сценарий должен содержать хотя бы один шаг"
        
        # Валидация каждого шага
        errors = []
        for i, step in enumerate(scenario['steps']):
            is_valid, error = ScenarioValidator.validate_step(step, step_index=i)
            if not is_valid:
                errors.append(f"Шаг {i + 1}: {error}")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, None
    
    @staticmethod
    def validate_step(step: Dict[str, Any], step_index: int = 0) -> Tuple[bool, Optional[str]]:
        """
        Валидация одного шага
        
        Args:
            step: Шаг для валидации
            step_index: Индекс шага (для сообщений об ошибках)
            
        Returns:
            Tuple[bool, Optional[str]]: (валиден ли, сообщение об ошибке)
        """
        if not isinstance(step, dict):
            return False, "Шаг должен быть объектом JSON"
        
        if 'action' not in step:
            return False, "Шаг должен содержать поле 'action'"
        
        action = step['action']
        
        if action not in ScenarioValidator.VALID_ACTIONS:
            return False, f"Неизвестное действие: {action}"
        
        # Валидация действия 'repeat'
        if action == 'repeat':
            return ScenarioValidator.validate_repeat(step)
        
        # Валидация обычных действий
        return ScenarioValidator.validate_regular_action(step, action)
    
    @staticmethod
    def validate_repeat(step: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Валидация блока repeat (цикл)
        
        Args:
            step: Шаг типа 'repeat'
            
        Returns:
            Tuple[bool, Optional[str]]: (валиден ли, сообщение об ошибке)
        """
        if 'type' not in step:
            return False, "Блок 'repeat' должен содержать поле 'type'"
        
        repeat_type = step['type']
        if repeat_type not in ScenarioValidator.VALID_REPEAT_TYPES:
            return False, f"Неизвестный тип цикла: {repeat_type}. Допустимые: {', '.join(ScenarioValidator.VALID_REPEAT_TYPES)}"
        
        # Проверка типа 'count'
        if repeat_type == 'count':
            if 'times' not in step:
                return False, "Тип цикла 'count' требует поле 'times'"
            if not isinstance(step['times'], int) or step['times'] < 1:
                return False, "Поле 'times' должно быть положительным числом"
        
        # Проверка типа 'while'
        if repeat_type == 'while':
            if 'condition' not in step:
                return False, "Тип цикла 'while' требует поле 'condition'"
            
            condition = step['condition']
            if not isinstance(condition, str):
                return False, "Поле 'condition' должно быть строкой"
            
            if condition not in ScenarioValidator.VALID_WHILE_CONDITIONS:
                return False, f"Неизвестное условие: {condition}. Допустимые: {', '.join(ScenarioValidator.VALID_WHILE_CONDITIONS)}"
            
            if 'selector' not in step:
                return False, "Тип цикла 'while' требует поле 'selector'"
            
            selector = step['selector']
            if not isinstance(selector, str):
                return False, "Поле 'selector' должно быть строкой"
            
            if not selector.strip():
                return False, "Поле 'selector' не может быть пустым"
            
            # Проверка метода селектора (если указан)
            if 'method' in step:
                method = step['method']
                if not isinstance(method, str):
                    return False, "Поле 'method' должно быть строкой"
                if method not in ScenarioValidator.VALID_METHODS:
                    return False, f"Неизвестный метод селектора: {method}"
        
        # Проверка вложенных шагов
        if 'steps' not in step:
            return False, "Блок 'repeat' должен содержать поле 'steps' с вложенными шагами"
        
        if not isinstance(step['steps'], list):
            return False, "Поле 'steps' в блоке 'repeat' должно быть массивом"
        
        if len(step['steps']) == 0:
            return False, "Блок 'repeat' должен содержать хотя бы один вложенный шаг"
        
        # Валидация вложенных шагов
        for i, nested_step in enumerate(step['steps']):
            is_valid, error = ScenarioValidator.validate_step(nested_step, step_index=i)
            if not is_valid:
                return False, f"Ошибка во вложенном шаге {i + 1}: {error}"
        
        return True, None
    
    @staticmethod
    def validate_regular_action(step: Dict[str, Any], action: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация обычного действия (не repeat)
        Проверяет наличие и типы всех необходимых параметров
        
        Args:
            step: Шаг для валидации
            action: Тип действия
            
        Returns:
            Tuple[bool, Optional[str]]: (валиден ли, сообщение об ошибке)
        """
        # Валидация метода селектора (если требуется)
        if 'method' in step:
            method = step['method']
            if not isinstance(method, str):
                return False, "Поле 'method' должно быть строкой"
            if method not in ScenarioValidator.VALID_METHODS:
                return False, f"Неизвестный метод селектора: {method}. Допустимые: {', '.join(ScenarioValidator.VALID_METHODS)}"
        
        # Специфичная валидация для каждого действия
        if action == 'navigate':
            if 'url' not in step:
                return False, "Действие 'navigate' требует поле 'url'"
            
            url = step['url']
            if not isinstance(url, str):
                return False, "Поле 'url' должно быть строкой"
            
            if not url.strip():
                return False, "Поле 'url' не может быть пустым"
            
            # Проверка формата URL (должен начинаться с http://, https:// или быть "back")
            if url != "back" and not url.startswith(("http://", "https://", "/")):
                return False, "Поле 'url' должно начинаться с http://, https://, / или быть 'back'"
        
        elif action == 'click':
            if 'selector' not in step:
                return False, "Действие 'click' требует поле 'selector'"
            
            selector = step['selector']
            if not isinstance(selector, str):
                return False, "Поле 'selector' должно быть строкой"
            
            if not selector.strip():
                return False, "Поле 'selector' не может быть пустым"
        
        elif action == 'type':
            # Проверка наличия field или selector
            if 'field' not in step and 'selector' not in step:
                return False, "Действие 'type' требует поле 'field' или 'selector'"
            
            # Проверка field (если указан)
            if 'field' in step:
                field = step['field']
                if not isinstance(field, str):
                    return False, "Поле 'field' должно быть строкой"
                if not field.strip():
                    return False, "Поле 'field' не может быть пустым"
            
            # Проверка selector (если указан)
            if 'selector' in step:
                selector = step['selector']
                if not isinstance(selector, str):
                    return False, "Поле 'selector' должно быть строкой"
                if not selector.strip():
                    return False, "Поле 'selector' не может быть пустым"
            
            # Проверка value
            if 'value' not in step:
                return False, "Действие 'type' требует поле 'value'"
            
            value = step['value']
            if not isinstance(value, str):
                return False, "Поле 'value' должно быть строкой"
        
        elif action == 'wait':
            seconds = step.get('seconds')
            wait_for_element = step.get('wait_for_element', False)
            
            if seconds is None and not wait_for_element:
                return False, "Действие 'wait' требует поле 'seconds' или 'wait_for_element'"
            
            # Проверка seconds
            if seconds is not None:
                if not isinstance(seconds, (int, float)):
                    return False, "Поле 'seconds' должно быть числом"
                if seconds < 0:
                    return False, "Поле 'seconds' должно быть положительным числом"
            
            # Проверка wait_for_element
            if wait_for_element:
                if not isinstance(wait_for_element, bool):
                    return False, "Поле 'wait_for_element' должно быть булевым значением"
                
                if 'selector' not in step:
                    return False, "Ожидание элемента требует поле 'selector'"
                
                selector = step['selector']
                if not isinstance(selector, str):
                    return False, "Поле 'selector' должно быть строкой"
                if not selector.strip():
                    return False, "Поле 'selector' не может быть пустым"
        
        elif action == 'scroll':
            if 'direction' not in step:
                return False, "Действие 'scroll' требует поле 'direction'"
            
            direction = step['direction']
            if not isinstance(direction, str):
                return False, "Поле 'direction' должно быть строкой"
            
            if direction not in ScenarioValidator.VALID_SCROLL_DIRECTIONS:
                return False, f"Неизвестное направление прокрутки: {direction}. Допустимые: {', '.join(ScenarioValidator.VALID_SCROLL_DIRECTIONS)}"
            
            # Если прокрутка к элементу, нужен селектор
            if direction == 'to_element':
                if 'selector' not in step:
                    return False, "Прокрутка к элементу требует поле 'selector'"
                
                selector = step['selector']
                if not isinstance(selector, str):
                    return False, "Поле 'selector' должно быть строкой"
                if not selector.strip():
                    return False, "Поле 'selector' не может быть пустым"
            
            # Проверка pixels (опционально)
            if 'pixels' in step:
                pixels = step['pixels']
                if not isinstance(pixels, int):
                    return False, "Поле 'pixels' должно быть целым числом"
        
        elif action == 'get_text':
            if 'selector' not in step:
                return False, "Действие 'get_text' требует поле 'selector'"
            
            selector = step['selector']
            if not isinstance(selector, str):
                return False, "Поле 'selector' должно быть строкой"
            
            if not selector.strip():
                return False, "Поле 'selector' не может быть пустым"
        
        elif action == 'get_attribute':
            if 'selector' not in step:
                return False, "Действие 'get_attribute' требует поле 'selector'"
            
            selector = step['selector']
            if not isinstance(selector, str):
                return False, "Поле 'selector' должно быть строкой"
            
            if not selector.strip():
                return False, "Поле 'selector' не может быть пустым"
            
            if 'attribute' not in step:
                return False, "Действие 'get_attribute' требует поле 'attribute'"
            
            attribute = step['attribute']
            if not isinstance(attribute, str):
                return False, "Поле 'attribute' должно быть строкой"
            
            if not attribute.strip():
                return False, "Поле 'attribute' не может быть пустым"
        
        elif action == 'screenshot':
            # Screenshot может не требовать параметров
            # Но если указан filename, проверяем его
            if 'filename' in step:
                filename = step['filename']
                if not isinstance(filename, str):
                    return False, "Поле 'filename' должно быть строкой"
                if not filename.strip():
                    return False, "Поле 'filename' не может быть пустым"
        
        return True, None
