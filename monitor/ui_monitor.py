"""
Модуль для мониторинга UI элементов через UI Automation
"""
import time
import uiautomation as auto
from datetime import datetime
import pythoncom
import ctypes
from ctypes import wintypes
from comtypes import client


class UIMonitor:
    def __init__(self, process_name="1cv8c.exe", log_focus=True, log_clicks=True):
        self.is_monitoring = False
        self.target_process = process_name
        self.log_focus = log_focus
        self.log_clicks = log_clicks
        self.last_focused_element = None
        self.last_invoke_time = 0
        
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
            
            events = []
            if self.log_focus:
                events.append("ФОКУС")
            if self.log_clicks:
                events.append("КЛИКИ")
            self.log_callback(f"[ИНФО] Отслеживаем: {', '.join(events)}\n")
            
            # Основной цикл мониторинга
            while self.is_monitoring:
                if self.log_clicks:
                    self.check_for_clicks(window)
                if self.log_focus:
                    self.monitor_events(window)
                time.sleep(0.05)
                
        except Exception as e:
            self.log_callback(f"[ОШИБКА] {str(e)}")
        finally:
            # Освобождаем COM
            pythoncom.CoUninitialize()
        
    def check_for_clicks(self, window):
        """Проверка кликов мыши на элементах"""
        try:
            # Получаем позицию курсора
            point = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
            
            # Проверяем состояние левой кнопки мыши
            left_button_state = ctypes.windll.user32.GetAsyncKeyState(0x01)
            
            # Если кнопка нажата (старший бит установлен)
            if left_button_state & 0x8000:
                current_time = time.time()
                
                # Минимальная защита от дублирования (50мс)
                if current_time - self.last_invoke_time < 0.05:
                    return
                
                self.last_invoke_time = current_time
                
                # Получаем элемент под курсором
                try:
                    element = auto.ControlFromPoint(point.x, point.y)
                    
                    if not element:
                        return
                    
                    # Проверяем, что элемент из процесса 1С
                    if element.ProcessId != window.ProcessId:
                        return
                    
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    element_info = []
                    
                    control_type = element.ControlTypeName
                    if control_type:
                        element_info.append(f"Type: {control_type}")
                    
                    name = element.Name
                    if name:
                        element_info.append(f"Name: '{name}'")
                    
                    automation_id = element.AutomationId
                    if automation_id:
                        element_info.append(f"AutomationId: '{automation_id}'")
                    
                    class_name = element.ClassName
                    if class_name:
                        element_info.append(f"ClassName: '{class_name}'")
                    
                    if element_info:
                        info_str = " | ".join(element_info)
                        self.log_callback(f"[{timestamp}] КЛИК → {info_str}")
                        
                except:
                    pass
                    
        except Exception as e:
            pass
    
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
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.is_monitoring = False
