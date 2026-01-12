"""
Парсер JSON сценариев
Загрузка, парсинг и базовая валидация структуры сценариев
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple


class ScenarioParser:
    """Парсер для загрузки и парсинга JSON сценариев"""
    
    # Поддерживаемые действия для базовой проверки
    VALID_ACTIONS = [
        'navigate', 'click', 'type', 'wait', 'scroll',
        'get_text', 'get_attribute', 'screenshot',
        'repeat'
    ]
    
    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """
        Загрузка сценария из JSON файла
        
        Args:
            file_path: Путь к файлу сценария
            
        Returns:
            Словарь с данными сценария
            
        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если ошибка парсинга JSON или формат некорректен
            json.JSONDecodeError: Если JSON невалиден
        """
        # Проверка существования файла
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл сценария не найден: {file_path}")
        
        # Проверка расширения файла
        if not file_path.lower().endswith('.json'):
            raise ValueError(f"Файл должен иметь расширение .json: {file_path}")
        
        try:
            # Загрузка и парсинг JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Базовая проверка формата JSON (должен быть объект, не массив или примитив)
            if not isinstance(data, dict):
                raise ValueError("JSON файл должен содержать объект (dict), а не массив или примитив")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {str(e)}. Файл должен содержать валидный JSON.")
        except UnicodeDecodeError as e:
            raise ValueError(f"Ошибка декодирования файла: {str(e)}. Файл должен быть в кодировке UTF-8.")
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке файла: {str(e)}")
    
    @staticmethod
    def parse(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсинг JSON данных в структуру сценария
        Выполняет базовую проверку обязательных полей
        
        Args:
            json_data: JSON данные сценария
            
        Returns:
            Распарсенный сценарий
            
        Raises:
            ValueError: Если структура некорректна
        """
        # Проверка, что это словарь
        if not isinstance(json_data, dict):
            raise ValueError("Сценарий должен быть объектом JSON (dict)")
        
        # Проверка обязательного поля 'name'
        if 'name' not in json_data:
            raise ValueError("Сценарий должен содержать обязательное поле 'name'")
        
        if not isinstance(json_data['name'], str):
            raise ValueError("Поле 'name' должно быть строкой")
        
        if not json_data['name'].strip():
            raise ValueError("Поле 'name' не может быть пустым")
        
        # Проверка обязательного поля 'steps'
        if 'steps' not in json_data:
            raise ValueError("Сценарий должен содержать обязательное поле 'steps'")
        
        if not isinstance(json_data['steps'], list):
            raise ValueError("Поле 'steps' должно быть массивом (list)")
        
        if len(json_data['steps']) == 0:
            raise ValueError("Поле 'steps' должно содержать хотя бы один шаг")
        
        # Проверка, что каждый шаг - это словарь
        for i, step in enumerate(json_data['steps']):
            if not isinstance(step, dict):
                raise ValueError(f"Шаг {i + 1} должен быть объектом JSON (dict)")
        
        # Возвращаем распарсенный сценарий
        # Детальная валидация будет в ScenarioValidator
        return json_data
    
    @staticmethod
    def validate(scenario: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Базовая валидация структуры сценария
        Проверяет обязательные поля, типы данных и структуру циклов
        
        Args:
            scenario: Сценарий для валидации
            
        Returns:
            Tuple[bool, Optional[str]]: (валиден ли, сообщение об ошибке)
        """
        # Проверка типа
        if not isinstance(scenario, dict):
            return False, "Сценарий должен быть объектом JSON"
        
        # Проверка обязательных полей
        required_fields = ['name', 'steps']
        for field in required_fields:
            if field not in scenario:
                return False, f"Сценарий должен содержать обязательное поле '{field}'"
        
        # Проверка типа поля 'name'
        if not isinstance(scenario['name'], str):
            return False, "Поле 'name' должно быть строкой"
        
        if not scenario['name'].strip():
            return False, "Поле 'name' не может быть пустым"
        
        # Проверка типа поля 'steps'
        if not isinstance(scenario['steps'], list):
            return False, "Поле 'steps' должно быть массивом"
        
        if len(scenario['steps']) == 0:
            return False, "Поле 'steps' должно содержать хотя бы один шаг"
        
        # Базовая валидация действий и структуры циклов
        for i, step in enumerate(scenario['steps']):
            if not isinstance(step, dict):
                return False, f"Шаг {i + 1} должен быть объектом JSON"
            
            if 'action' not in step:
                return False, f"Шаг {i + 1} должен содержать поле 'action'"
            
            action = step['action']
            
            # Проверка, что действие поддерживается
            if action not in ScenarioParser.VALID_ACTIONS:
                return False, f"Шаг {i + 1}: неизвестное действие '{action}'"
            
            # Проверка структуры циклов
            if action == 'repeat':
                is_valid, error = ScenarioParser._validate_repeat_structure(step, step_index=i + 1)
                if not is_valid:
                    return False, error
        
        return True, None
    
    @staticmethod
    def _validate_repeat_structure(repeat_step: Dict[str, Any], step_index: int) -> Tuple[bool, Optional[str]]:
        """
        Базовая проверка структуры блока repeat
        
        Args:
            repeat_step: Блок repeat
            step_index: Индекс шага (для сообщений об ошибках)
            
        Returns:
            Tuple[bool, Optional[str]]: (валидна ли структура, сообщение об ошибке)
        """
        # Проверка наличия поля 'type'
        if 'type' not in repeat_step:
            return False, f"Шаг {step_index} (repeat): должен содержать поле 'type'"
        
        repeat_type = repeat_step['type']
        valid_types = ['until_stopped', 'count', 'while']
        
        if repeat_type not in valid_types:
            return False, f"Шаг {step_index} (repeat): неизвестный тип '{repeat_type}'. Допустимые: {', '.join(valid_types)}"
        
        # Проверка типа 'count'
        if repeat_type == 'count':
            if 'times' not in repeat_step:
                return False, f"Шаг {step_index} (repeat): тип 'count' требует поле 'times'"
            if not isinstance(repeat_step['times'], int) or repeat_step['times'] < 1:
                return False, f"Шаг {step_index} (repeat): поле 'times' должно быть положительным числом"
        
        # Проверка типа 'while'
        if repeat_type == 'while':
            if 'condition' not in repeat_step:
                return False, f"Шаг {step_index} (repeat): тип 'while' требует поле 'condition'"
            if 'selector' not in repeat_step:
                return False, f"Шаг {step_index} (repeat): тип 'while' требует поле 'selector'"
        
        # Проверка наличия вложенных шагов
        if 'steps' not in repeat_step:
            return False, f"Шаг {step_index} (repeat): должен содержать поле 'steps' с вложенными шагами"
        
        if not isinstance(repeat_step['steps'], list):
            return False, f"Шаг {step_index} (repeat): поле 'steps' должно быть массивом"
        
        if len(repeat_step['steps']) == 0:
            return False, f"Шаг {step_index} (repeat): должен содержать хотя бы один вложенный шаг"
        
        # Проверка, что вложенные шаги - объекты
        for i, nested_step in enumerate(repeat_step['steps']):
            if not isinstance(nested_step, dict):
                return False, f"Шаг {step_index} (repeat): вложенный шаг {i + 1} должен быть объектом JSON"
            if 'action' not in nested_step:
                return False, f"Шаг {step_index} (repeat): вложенный шаг {i + 1} должен содержать поле 'action'"
        
        return True, None
