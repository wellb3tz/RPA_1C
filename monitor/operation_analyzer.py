"""
Анализатор операций - преобразует последовательности действий в бизнес-операции
"""
from datetime import datetime, timedelta
from collections import deque


class Operation:
    """Класс для представления бизнес-операции"""
    def __init__(self, operation_type, start_time, pattern_key=None):
        self.operation_type = operation_type
        self.pattern_key = pattern_key  # Ключ паттерна для идентификации
        self.start_time = start_time
        self.end_time = None
        self.actions = []
        self.context = {}
        self.completed = False
        self.middle_triggers_matched = False  # Флаг: были ли промежуточные триггеры
        self.matched_middle_triggers = []  # Список сработавших промежуточных триггеров
        self.unrelated_actions_count = 0  # Счетчик посторонних действий
        self.alternative_operations = []  # Альтернативные операции при конфликте триггеров
    
    def add_action(self, action):
        """Добавить действие в операцию"""
        self.actions.append(action)
        self.end_time = action.get('timestamp')
    
    def get_duration(self):
        """Получить длительность операции"""
        if self.start_time and self.end_time:
            try:
                start = datetime.strptime(self.start_time, "%H:%M:%S.%f")
                end = datetime.strptime(self.end_time, "%H:%M:%S.%f")
                return (end - start).total_seconds()
            except:
                return 0
        return 0
    
    def to_string(self):
        """Преобразовать операцию в строку для отображения"""
        duration = self.get_duration()
        actions_count = len(self.actions)
        
        result = f"🎯 {self.operation_type}"
        
        if self.context:
            context_str = ", ".join([f"{k}: '{v}'" for k, v in self.context.items()])
            result += f" ({context_str})"
        
        result += f" | ⏱️ {duration:.1f}с | 📊 {actions_count} действий"
        
        if self.completed:
            result += " | ✅ Завершено"
        
        return result


class OperationAnalyzer:
    """Анализатор для распознавания бизнес-операций"""
    
    def __init__(self):
        self.recent_actions = deque(maxlen=50)  # Последние 50 действий
        self.current_operation = None
        self.completed_operations = []
        self.operation_timeout = 30  # Таймаут операции в секундах
        self.max_unrelated_actions = 5  # Максимум посторонних действий
        
        # Паттерны операций (загружаются из файла или создаются в редакторе)
        self.patterns = {}
    
    def parse_action(self, log_message):
        """Разобрать лог-сообщение в структурированное действие"""
        try:
            # Пропускаем служебные сообщения
            if any(x in log_message for x in ['[СТАРТ]', '[СТОП]', '[ИНФО]', '[НАСТРОЙКИ]', '[УСПЕХ]', '[ОШИБКА]', '[ЭКСПОРТ]']):
                return None
            
            action = {}
            
            # Извлекаем timestamp
            import re
            timestamp_match = re.search(r'\[(\d{2}:\d{2}:\d{2}\.\d{3})\]', log_message)
            if timestamp_match:
                action['timestamp'] = timestamp_match.group(1)
            
            # Извлекаем тип события
            if 'ФОКУС' in log_message:
                action['event_type'] = 'ФОКУС'
            elif 'КЛИК' in log_message:
                action['event_type'] = 'КЛИК'
            elif 'ВВОД' in log_message:
                action['event_type'] = 'ВВОД'
            else:
                return None
            
            # Извлекаем тип элемента
            type_match = re.search(r'Type: (\w+)', log_message)
            if type_match:
                action['control_type'] = type_match.group(1)
            
            # Извлекаем имя элемента
            name_match = re.search(r"Name: '([^']*)'", log_message)
            if name_match:
                action['element_name'] = name_match.group(1)
            
            # Извлекаем путь
            path_match = re.search(r"Путь: (.+?)(?:\s*$)", log_message)
            if path_match:
                action['path'] = path_match.group(1).strip()
            
            # Для ввода - извлекаем значения
            if action['event_type'] == 'ВВОД':
                value_match = re.search(r"Было: '([^']*)' → Стало: '([^']*)'", log_message)
                if value_match:
                    action['old_value'] = value_match.group(1)
                    action['new_value'] = value_match.group(2)
            
            return action
            
        except Exception as e:
            return None
    
    def match_trigger(self, trigger, text):
        """Проверить соответствие триггера тексту с учетом границ слов"""
        if not text:
            return False
        
        # Убираем лишние пробелы из текста
        text = text.strip()
        
        # Если триггер - это тип события (ВВОД, КЛИК, ФОКУС), проверяем точное совпадение
        if trigger in ['ВВОД', 'КЛИК', 'ФОКУС']:
            return trigger == text
        
        # Для остальных триггеров проверяем как отдельное слово
        import re
        # Создаем паттерн для поиска слова с границами
        pattern = r'\b' + re.escape(trigger) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def detect_operation_start(self, action):
        """Определить начало новой операции"""
        element_name = action.get('element_name', '')
        event_type = action.get('event_type', '')
        path = action.get('path', '')
        
        matched_operations = []
        
        for pattern_key, pattern in self.patterns.items():
            # Если триггеров начала нет - операция всегда активна
            if not pattern.get('triggers'):
                # Проверяем, нет ли уже активной операции этого типа
                if self.current_operation and self.current_operation.operation_type == pattern['name']:
                    continue
                matched_operations.append((pattern_key, pattern['name']))
                continue
            
            # Если триггеры начала есть - проверяем их
            for trigger in pattern['triggers']:
                if self.match_trigger(trigger, element_name) or self.match_trigger(trigger, event_type) or self.match_trigger(trigger, path):
                    matched_operations.append((pattern_key, pattern['name']))
                    break  # Достаточно одного совпадения для этого паттерна
        
        if len(matched_operations) == 0:
            return None, None, []
        elif len(matched_operations) == 1:
            return matched_operations[0][0], matched_operations[0][1], matched_operations
        else:
            # Несколько операций могут начаться - возвращаем первую, но передаем список всех
            return matched_operations[0][0], matched_operations[0][1], matched_operations
    
    def check_middle_triggers(self, action):
        """Проверить соответствие промежуточным триггерам"""
        if not self.current_operation:
            return False, None
        
        element_name = action.get('element_name', '')
        event_type = action.get('event_type', '')
        path = action.get('path', '')
        
        # Если есть альтернативные операции, проверяем возможность переключения
        if self.current_operation.alternative_operations:
            switch_result = self.check_operation_switch(action, element_name, event_type, path)
            if switch_result:
                return True, switch_result
        
        # Получаем паттерн текущей операции
        pattern = self.patterns.get(self.current_operation.pattern_key)
        if not pattern:
            return True, None
        
        middle_triggers = pattern.get('middle_triggers', [])
        
        if not middle_triggers:
            # Если промежуточных триггеров нет, считаем что они всегда выполнены
            self.current_operation.middle_triggers_matched = True
            # НО все равно считаем посторонние действия для отмены
            self.current_operation.unrelated_actions_count += 1
            return True, None
        
        # Проверяем соответствие хотя бы одному промежуточному триггеру
        matched = False
        for trigger in middle_triggers:
            if self.match_trigger(trigger, element_name) or self.match_trigger(trigger, event_type) or self.match_trigger(trigger, path):
                matched = True
                # Проверяем, не был ли этот триггер уже зафиксирован
                if trigger not in self.current_operation.matched_middle_triggers:
                    # Отмечаем, что промежуточный триггер сработал
                    self.current_operation.middle_triggers_matched = True
                    # Добавляем триггер в список сработавших
                    self.current_operation.matched_middle_triggers.append(trigger)
                    # Сбрасываем счетчик посторонних действий
                    self.current_operation.unrelated_actions_count = 0
                    # Возвращаем сообщение о срабатывании триггера
                    return True, f"   🔄 Промежуточный триггер: {trigger}"
                # Триггер уже был, но это релевантное действие - сбрасываем счетчик
                self.current_operation.unrelated_actions_count = 0
                return True, None
        
        # Действие не соответствует промежуточным триггерам
        if not matched:
            # Увеличиваем счетчик посторонних действий
            self.current_operation.unrelated_actions_count += 1
        
        return True, None
    
    def check_operation_switch(self, action, element_name, event_type, path):
        """Проверить возможность переключения на альтернативную операцию"""
        # Проверяем промежуточные триггеры всех альтернативных операций
        for alt_pattern_key in self.current_operation.alternative_operations:
            alt_pattern = self.patterns.get(alt_pattern_key)
            if not alt_pattern:
                continue
            
            alt_middle_triggers = alt_pattern.get('middle_triggers', [])
            
            # Если у альтернативной операции нет промежуточных триггеров
            # проверяем триггеры завершения - возможно это она
            if not alt_middle_triggers:
                for trigger in alt_pattern.get('completion_triggers', []):
                    if self.match_trigger(trigger, element_name):
                        # Найдено соответствие триггеру завершения - переключаемся
                        old_operation_name = self.current_operation.operation_type
                        new_operation_name = alt_pattern['name']
                        
                        # Обновляем текущую операцию
                        self.current_operation.operation_type = new_operation_name
                        self.current_operation.pattern_key = alt_pattern_key
                        self.current_operation.alternative_operations = []
                        self.current_operation.middle_triggers_matched = True
                        self.current_operation.unrelated_actions_count = 0
                        
                        return f"   🔀 Переключение: {old_operation_name} → {new_operation_name} (по триггеру завершения)"
                continue
            
            # Проверяем соответствие промежуточным триггерам альтернативной операции
            for trigger in alt_middle_triggers:
                if self.match_trigger(trigger, element_name) or self.match_trigger(trigger, event_type) or self.match_trigger(trigger, path):
                    # Найдено соответствие - переключаемся на эту операцию
                    old_operation_name = self.current_operation.operation_type
                    new_operation_name = alt_pattern['name']
                    
                    # Обновляем текущую операцию
                    self.current_operation.operation_type = new_operation_name
                    self.current_operation.pattern_key = alt_pattern_key
                    self.current_operation.alternative_operations = []  # Очищаем альтернативы
                    self.current_operation.middle_triggers_matched = True
                    self.current_operation.matched_middle_triggers.append(trigger)
                    self.current_operation.unrelated_actions_count = 0
                    
                    return f"   🔀 Переключение: {old_operation_name} → {new_operation_name}\n   🔄 Промежуточный триггер: {trigger}"
        
        return None
    
    def detect_operation_completion(self, action):
        """Определить завершение текущей операции"""
        if not self.current_operation:
            return False
        
        element_name = action.get('element_name', '')
        
        # Получаем паттерн текущей операции по ключу
        pattern = self.patterns.get(self.current_operation.pattern_key)
        if not pattern:
            return False
        
        # Проверяем триггеры завершения
        for trigger in pattern['completion_triggers']:
            if self.match_trigger(trigger, element_name):
                # Проверяем, были ли промежуточные триггеры (если они требуются)
                middle_triggers = pattern.get('middle_triggers', [])
                
                if middle_triggers and not self.current_operation.middle_triggers_matched:
                    # Промежуточные триггеры требуются, но не были выполнены
                    return False
                
                # Все условия выполнены - операция завершена
                return True
        
        return False
    
    def check_operation_timeout(self, current_time):
        """Проверить таймаут текущей операции"""
        if not self.current_operation or not self.current_operation.end_time:
            return False
        
        try:
            last_action_time = datetime.strptime(self.current_operation.end_time, "%H:%M:%S.%f")
            current = datetime.strptime(current_time, "%H:%M:%S.%f")
            
            # Если прошло больше таймаута - операция прервана
            if (current - last_action_time).total_seconds() > self.operation_timeout:
                return True
        except:
            pass
        
        return False
    
    def extract_context(self, actions):
        """Извлечь контекст операции из действий"""
        context = {}
        
        # Ищем заполненные поля для операций ввода
        filled_fields = []
        for action in actions:
            if action.get('event_type') == 'ВВОД':
                element_name = action.get('element_name', '')
                new_value = action.get('new_value', '')
                if element_name and new_value:
                    filled_fields.append(f"{element_name}={new_value}")
        
        if filled_fields:
            context['Заполнено полей'] = len(filled_fields)
        
        return context
    
    def analyze_action(self, log_message):
        """Анализировать действие и обновить состояние операций"""
        action = self.parse_action(log_message)
        
        if not action:
            return None
        
        self.recent_actions.append(action)
        
        current_time = action.get('timestamp')
        
        # Проверяем таймаут текущей операции
        if self.current_operation and current_time:
            if self.check_operation_timeout(current_time):
                # Операция прервана по таймауту
                self.current_operation.context = self.extract_context(self.current_operation.actions)
                self.completed_operations.append(self.current_operation)
                result = self.current_operation.to_string() + " | ⚠️ Прервано"
                self.current_operation = None
                return result
        
        # Инициализируем переменную для сообщения о промежуточном триггере
        middle_trigger_msg = None
        
        # Проверяем завершение текущей операции
        if self.current_operation:
            # Проверяем промежуточные триггеры (не прерываем, просто отмечаем)
            _, middle_trigger_msg = self.check_middle_triggers(action)
            
            # Проверяем превышение лимита посторонних действий
            if self.current_operation.unrelated_actions_count > self.max_unrelated_actions:
                # Операция отменена из-за слишком большого количества посторонних действий
                self.current_operation.context = self.extract_context(self.current_operation.actions)
                self.completed_operations.append(self.current_operation)
                result = self.current_operation.to_string() + f" | ❌ Отменено (>{self.max_unrelated_actions} посторонних действий)"
                self.current_operation = None
                return result
            
            # Если сработал новый промежуточный триггер - выводим сообщение
            if middle_trigger_msg:
                result = middle_trigger_msg
            
            self.current_operation.add_action(action)
            
            if self.detect_operation_completion(action):
                # Операция завершена
                self.current_operation.completed = True
                self.current_operation.context = self.extract_context(self.current_operation.actions)
                self.completed_operations.append(self.current_operation)
                result = self.current_operation.to_string()
                self.current_operation = None
                return result
        
        # Возвращаем сообщение о промежуточном триггере если оно было
        if self.current_operation and middle_trigger_msg:
            return middle_trigger_msg
        
        # Проверяем начало новой операции
        pattern_key, operation_name, all_operations = self.detect_operation_start(action)
        
        if pattern_key and operation_name:
            # Если есть незавершенная операция - завершаем её
            if self.current_operation:
                self.current_operation.context = self.extract_context(self.current_operation.actions)
                self.completed_operations.append(self.current_operation)
            
            # Начинаем новую операцию
            self.current_operation = Operation(operation_name, current_time, pattern_key)
            self.current_operation.add_action(action)
            
            # Сохраняем альтернативные операции для возможного переключения
            if len(all_operations) > 1:
                # Сохраняем ключи паттернов альтернативных операций
                self.current_operation.alternative_operations = [
                    key for key, name in all_operations if name != operation_name
                ]
            
            # Проверяем, есть ли триггеры начала
            pattern = self.patterns.get(pattern_key, {})
            if pattern.get('triggers'):
                # Если несколько операций могут начаться - показываем все варианты
                if len(all_operations) > 1:
                    operations_str = " или ".join([name for _, name in all_operations])
                    return f"▶️ Начало операции: {operations_str}"
                else:
                    return f"▶️ Начало операции: {operation_name}"
            else:
                # Операция без триггеров начала - не выводим сообщение о начале
                return None
        
        return None
    
    def get_statistics(self):
        """Получить статистику по операциям"""
        if not self.completed_operations:
            return "Нет завершенных операций"
        
        total = len(self.completed_operations)
        completed = sum(1 for op in self.completed_operations if op.completed)
        interrupted = total - completed
        
        avg_duration = sum(op.get_duration() for op in self.completed_operations) / total
        
        return f"📈 Статистика: {total} операций | ✅ {completed} завершено | ⚠️ {interrupted} прервано | ⏱️ Средняя длительность: {avg_duration:.1f}с"
