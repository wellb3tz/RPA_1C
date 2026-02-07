"""
Модуль для мониторинга UI элементов через UI Automation
"""
import time
import uiautomation as auto
from datetime import datetime
import pythoncom


class UIMonitor:
    def __init__(self, process_name="1cv8c.exe", monitor_mode="scan"):
        self.is_monitoring = False
        self.target_process = process_name
        self.monitor_mode = monitor_mode  # "scan" или "events"
        self.last_focused_element = None
        
    def start_monitoring(self, log_callback, connection_callback):
        """Начать мониторинг UI элементов"""
        self.is_monitoring = True
        self.log_callback = log_callback
        self.connection_callback = connection_callback
        
        # Инициализация COM для работы с UI Automation
        pythoncom.CoInitialize()
        
        try:
            # Поиск окна 1С по имени процесса
            window = auto.WindowControl(searchDepth=1, ClassName="V8TopLevelFrameSDI")
            
            if not window.Exists(0, 0):
                self.connection_callback(False, f"Окно процесса {self.target_process} не найдено. Убедитесь, что 1С запущена.")
                return
            
            # Проверяем, что это нужный процесс
            process_id = window.ProcessId
            window_title = window.Name
            
            self.connection_callback(True, f"Процесс {self.target_process} (PID: {process_id}, Окно: '{window_title}')")
            
            if self.monitor_mode == "scan":
                self.log_callback(f"[ИНФО] Начинаем сканирование элементов...\n")
            else:
                self.log_callback(f"[ИНФО] Отслеживаем события нажатий...\n")
            
            # Основной цикл мониторинга
            while self.is_monitoring:
                if self.monitor_mode == "scan":
                    self.scan_element(window, depth=0, max_depth=3)
                    time.sleep(2)  # Интервал сканирования
                else:
                    self.monitor_events(window)
                    time.sleep(0.1)  # Быстрее для событий
                
        except Exception as e:
            self.log_callback(f"[ОШИБКА] {str(e)}")
        finally:
            # Освобождаем COM
            pythoncom.CoUninitialize()
            
    def scan_element(self, element, depth=0, max_depth=3):
        """Рекурсивное сканирование элементов UI"""
        if depth > max_depth or not self.is_monitoring:
            return
            
        try:
            # Получаем информацию об элементе
            element_info = self.get_element_info(element)
            
            if element_info:
                timestamp = datetime.now().strftime("%H:%M:%S")
                indent = "  " * depth
                self.log_callback(f"[{timestamp}] {indent}{element_info}")
            
            # Сканируем дочерние элементы
            children = element.GetChildren()
            for child in children[:5]:  # Ограничиваем количество для начала
                self.scan_element(child, depth + 1, max_depth)
                
        except Exception as e:
            pass  # Игнорируем ошибки отдельных элементов
            
    def get_element_info(self, element):
        """Получить информацию об элементе (как в Inspect.exe)"""
        try:
            info_parts = []
            
            # Тип элемента
            control_type = element.ControlTypeName
            if control_type:
                info_parts.append(f"Type: {control_type}")
            
            # Имя элемента
            name = element.Name
            if name:
                info_parts.append(f"Name: '{name}'")
            
            # Значение (для полей ввода)
            if hasattr(element, 'CurrentValue'):
                value = element.CurrentValue()
                if value:
                    info_parts.append(f"Value: '{value}'")
            
            # AutomationId
            automation_id = element.AutomationId
            if automation_id:
                info_parts.append(f"AutomationId: '{automation_id}'")
            
            # ClassName
            class_name = element.ClassName
            if class_name:
                info_parts.append(f"ClassName: '{class_name}'")
            
            if info_parts:
                return " | ".join(info_parts)
                
        except Exception:
            pass
            
        return None
        
    def monitor_events(self, window):
        """Мониторинг событий нажатий и фокуса"""
        try:
            # Получаем элемент в фокусе
            focused = auto.GetFocusedControl()
            
            if not focused:
                return
            
            # Проверяем, что элемент принадлежит процессу 1С
            try:
                focused_pid = focused.ProcessId
                window_pid = window.ProcessId
                
                # Игнорируем элементы не из процесса 1С
                if focused_pid != window_pid:
                    return
            except:
                return
            
            # Проверяем, что это новый элемент (не тот же самый)
            try:
                current_id = (focused.ControlTypeName, focused.Name, focused.AutomationId)
                
                if current_id == self.last_focused_element:
                    return
                    
                self.last_focused_element = current_id
            except:
                return
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            element_info = []
            
            # Тип элемента
            control_type = focused.ControlTypeName
            if control_type:
                element_info.append(f"Type: {control_type}")
            
            # Имя
            name = focused.Name
            if name:
                element_info.append(f"Name: '{name}'")
            
            # AutomationId
            automation_id = focused.AutomationId
            if automation_id:
                element_info.append(f"AutomationId: '{automation_id}'")
            
            # ClassName
            class_name = focused.ClassName
            if class_name:
                element_info.append(f"ClassName: '{class_name}'")
            
            # Значение
            try:
                if hasattr(focused, 'GetValuePattern'):
                    value_pattern = focused.GetValuePattern()
                    if value_pattern:
                        value = value_pattern.Value
                        if value:
                            element_info.append(f"Value: '{value}'")
            except:
                pass
            
            if element_info:
                info_str = " | ".join(element_info)
                self.log_callback(f"[{timestamp}] ФОКУС → {info_str}")
                    
        except Exception as e:
            pass  # Игнорируем ошибки
    
    def set_mode(self, mode):
        """Изменить режим мониторинга"""
        self.monitor_mode = mode
        self.last_focused_element = None
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.is_monitoring = False
