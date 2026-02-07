"""
Модуль для мониторинга UI элементов через UI Automation
"""
import time
import uiautomation as auto
from datetime import datetime


class UIMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.target_process = "1cv8.exe"
        
    def start_monitoring(self, log_callback):
        """Начать мониторинг UI элементов"""
        self.is_monitoring = True
        self.log_callback = log_callback
        
        try:
            # Поиск окна 1С
            window = auto.WindowControl(searchDepth=1, ClassName="V8TopLevelFrameSDI")
            
            if not window.Exists(0, 0):
                self.log_callback("[ОШИБКА] Окно 1С не найдено")
                return
                
            self.log_callback(f"[ИНФО] Найдено окно: {window.Name}")
            
            # Основной цикл мониторинга
            while self.is_monitoring:
                self.scan_element(window, depth=0, max_depth=3)
                time.sleep(2)  # Интервал сканирования
                
        except Exception as e:
            self.log_callback(f"[ОШИБКА] {str(e)}")
            
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
        
    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.is_monitoring = False
