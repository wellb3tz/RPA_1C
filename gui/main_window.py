"""
Главное окно приложения
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QLineEdit, QCheckBox, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from monitor.ui_monitor import UIMonitor
from datetime import datetime
import os


class MonitorThread(QThread):
    """Поток для мониторинга UI элементов"""
    log_signal = pyqtSignal(str)
    connection_signal = pyqtSignal(bool, str)  # (успех, сообщение)
    
    def __init__(self, process_name, log_focus, log_clicks, log_input):
        super().__init__()
        self.monitor = UIMonitor(process_name, log_focus, log_clicks, log_input)
        self.is_running = False
        
    def run(self):
        self.is_running = True
        self.monitor.start_monitoring(self.log_signal.emit, self.connection_signal.emit)
        
    def stop(self):
        self.is_running = False
        self.monitor.stop_monitoring()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.monitor_thread = None
        self.log_file_path = "logs/monitor_history.log"
        self.ensure_log_directory()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("1С UI Monitor")
        self.setGeometry(100, 100, 800, 600)
        
        # Окно поверх всех приложений
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Панель управления - строка 1
        control_layout1 = QHBoxLayout()
        
        self.process_label = QLabel("Процесс:")
        control_layout1.addWidget(self.process_label)
        
        self.process_input = QLineEdit()
        self.process_input.setText("1cv8c.exe")
        self.process_input.setPlaceholderText("Введите имя процесса 1С")
        control_layout1.addWidget(self.process_input)
        
        # Чекбоксы для выбора типов событий
        self.log_label = QLabel("Логировать:")
        control_layout1.addWidget(self.log_label)
        
        self.focus_checkbox = QCheckBox("ФОКУС")
        self.focus_checkbox.setChecked(True)
        self.focus_checkbox.stateChanged.connect(self.on_settings_changed)
        control_layout1.addWidget(self.focus_checkbox)
        
        self.click_checkbox = QCheckBox("КЛИКИ")
        self.click_checkbox.setChecked(True)
        self.click_checkbox.stateChanged.connect(self.on_settings_changed)
        control_layout1.addWidget(self.click_checkbox)
        
        self.input_checkbox = QCheckBox("ВВОД")
        self.input_checkbox.setChecked(True)
        self.input_checkbox.stateChanged.connect(self.on_settings_changed)
        control_layout1.addWidget(self.input_checkbox)
        
        layout.addLayout(control_layout1)
        
        # Панель управления - строка 2
        control_layout2 = QHBoxLayout()
        
        self.start_btn = QPushButton("Начать мониторинг")
        self.start_btn.clicked.connect(self.start_monitoring)
        control_layout2.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        control_layout2.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("Очистить лог")
        self.clear_btn.clicked.connect(self.clear_log)
        control_layout2.addWidget(self.clear_btn)
        
        self.export_btn = QPushButton("Экспорт в файл")
        self.export_btn.clicked.connect(self.export_log)
        control_layout2.addWidget(self.export_btn)
        
        layout.addLayout(control_layout2)
        
        # Область логов
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # Разделитель
        separator_label = QLabel("Расшифровка элементов:")
        layout.addWidget(separator_label)
        
        # Область расшифровки
        self.decode_area = QTextEdit()
        self.decode_area.setReadOnly(True)
        self.decode_area.setMaximumHeight(150)
        layout.addWidget(self.decode_area)
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе")
        
    def start_monitoring(self):
        process_name = self.process_input.text()
        if not process_name:
            self.log_area.append("[ОШИБКА] Введите имя процесса")
            return
        
        log_focus = self.focus_checkbox.isChecked()
        log_clicks = self.click_checkbox.isChecked()
        log_input = self.input_checkbox.isChecked()
        
        if not log_focus and not log_clicks and not log_input:
            self.log_area.append("[ОШИБКА] Выберите хотя бы один тип событий для логирования")
            return
        
        events = []
        if log_focus:
            events.append("ФОКУС")
        if log_clicks:
            events.append("КЛИКИ")
        if log_input:
            events.append("ВВОД")
        events_str = ", ".join(events)
            
        self.log_area.append(f"[СТАРТ] Попытка подключения к процессу {process_name}...")
        self.log_area.append(f"[НАСТРОЙКИ] Логирование: {events_str}")
        self.statusBar().showMessage(f"Подключение к {process_name}...")
            
        self.monitor_thread = MonitorThread(process_name, log_focus, log_clicks, log_input)
        self.monitor_thread.log_signal.connect(self.add_log)
        self.monitor_thread.connection_signal.connect(self.on_connection_status)
        self.monitor_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.focus_checkbox.setEnabled(False)
        self.click_checkbox.setEnabled(False)
        self.input_checkbox.setEnabled(False)
    
    def on_settings_changed(self):
        """Обработка изменения настроек логирования"""
        # Проверяем, что хотя бы один чекбокс включен
        if not self.focus_checkbox.isChecked() and not self.click_checkbox.isChecked() and not self.input_checkbox.isChecked():
            # Не даем отключить все
            self.sender().setChecked(True)
        
    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.focus_checkbox.setEnabled(True)
        self.click_checkbox.setEnabled(True)
        self.input_checkbox.setEnabled(True)
        self.statusBar().showMessage("Мониторинг остановлен")
        self.log_area.append("\n[СТОП] Мониторинг остановлен\n")
        
    def on_connection_status(self, success, message):
        """Обработка статуса подключения к процессу"""
        if success:
            self.log_area.append(f"[УСПЕХ] {message}\n")
            self.statusBar().showMessage(f"✓ Подключено: {message}")
        else:
            self.log_area.append(f"[ОШИБКА] {message}\n")
            self.statusBar().showMessage(f"✗ Ошибка подключения")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def add_log(self, message):
        self.log_area.append(message)
        # Автоматически сохраняем в файл истории
        self.save_to_history(message)
        # Обновляем расшифровку
        self.update_decode(message)
        
    def clear_log(self):
        self.log_area.clear()
        self.decode_area.clear()
    
    def ensure_log_directory(self):
        """Создать директорию для логов если её нет"""
        log_dir = os.path.dirname(self.log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def save_to_history(self, message):
        """Сохранить сообщение в файл истории"""
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(message + '\n')
        except Exception as e:
            pass  # Игнорируем ошибки записи
    
    def export_log(self):
        """Экспорт текущего лога в файл"""
        try:
            # Диалог сохранения файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"1c_monitor_log_{timestamp}.txt"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить лог",
                default_filename,
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                # Получаем текст из области логов
                log_text = self.log_area.toPlainText()
                
                # Сохраняем в файл
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"=== 1С UI Monitor Log ===\n")
                    f.write(f"Экспортировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"{'='*50}\n\n")
                    f.write(log_text)
                
                self.statusBar().showMessage(f"Лог сохранен: {file_path}", 3000)
                self.log_area.append(f"\n[ЭКСПОРТ] Лог сохранен в файл: {file_path}\n")
        except Exception as e:
            self.log_area.append(f"\n[ОШИБКА] Не удалось сохранить файл: {str(e)}\n")
    
    def update_decode(self, message):
        """Обновить расшифровку последнего события"""
        # Словарь расшифровки типов элементов
        type_decode = {
            'ButtonControl': '🔘 Кнопка',
            'EditControl': '📝 Поле ввода',
            'TextControl': '📄 Текст',
            'PaneControl': '🖼️ Панель',
            'WindowControl': '🪟 Окно',
            'MenuControl': '📋 Меню',
            'MenuItemControl': '📌 Пункт меню',
            'ToolBarControl': '🔧 Панель инструментов',
            'TabControl': '📑 Вкладки',
            'TabItemControl': '📄 Вкладка',
            'ListControl': '📜 Список',
            'ListItemControl': '• Элемент списка',
            'TreeControl': '🌲 Дерево',
            'TreeItemControl': '🌿 Узел дерева',
            'TableControl': '📊 Таблица',
            'DataItemControl': '📋 Ячейка данных',
            'ComboBoxControl': '🔽 Выпадающий список',
            'CheckBoxControl': '☑️ Чекбокс',
            'RadioButtonControl': '🔘 Радиокнопка',
            'GroupControl': '📦 Группа',
            'ImageControl': '🖼️ Изображение',
            'ScrollBarControl': '↕️ Полоса прокрутки',
            'SplitButtonControl': '⚡ Кнопка с меню',
            'DocumentControl': '📃 Документ',
            'HyperlinkControl': '🔗 Ссылка',
            'CalendarControl': '📅 Календарь',
            'SpinnerControl': '🔄 Счетчик',
            'ProgressBarControl': '⏳ Прогресс-бар',
            'SliderControl': '🎚️ Слайдер',
            'ThumbControl': '👆 Ползунок',
            'HeaderControl': '📌 Заголовок',
            'HeaderItemControl': '📍 Элемент заголовка',
            'StatusBarControl': '📊 Статус-бар',
            'TitleBarControl': '📋 Заголовок окна',
            'SeparatorControl': '➖ Разделитель',
            'ToolTipControl': '💬 Подсказка',
            'CustomControl': '⚙️ Пользовательский элемент',
        }
        
        # Словарь расшифровки типов событий
        event_decode = {
            'ФОКУС': '👁️ Переход на элемент',
            'КЛИК': '🖱️ Нажатие мыши',
            'ВВОД': '⌨️ Ввод текста',
        }
        
        try:
            # Пропускаем служебные сообщения
            if any(x in message for x in ['[СТАРТ]', '[СТОП]', '[ИНФО]', '[НАСТРОЙКИ]', '[УСПЕХ]', '[ОШИБКА]', '[ЭКСПОРТ]']):
                return
            
            # Извлекаем тип события
            event_type = None
            for event in event_decode.keys():
                if event in message:
                    event_type = event
                    break
            
            if not event_type:
                return
            
            # Извлекаем Type: из сообщения
            import re
            type_match = re.search(r'Type: (\w+)', message)
            
            if type_match:
                control_type = type_match.group(1)
                decoded_type = type_decode.get(control_type, f'❓ {control_type}')
                
                # Извлекаем Name: если есть
                name_match = re.search(r"Name: '([^']*)'", message)
                element_name = name_match.group(1) if name_match else "без имени"
                
                # Извлекаем путь к элементу
                path_match = re.search(r"Путь: (.+?)(?:\s*\||$)", message)
                element_path = ""
                if path_match:
                    raw_path = path_match.group(1).strip()
                    # Упрощаем путь - убираем технические названия типов
                    path_parts = raw_path.split(' → ')
                    simplified_path = []
                    for part in path_parts:
                        # Извлекаем имя из формата Type['Name']
                        part_name_match = re.search(r"\['([^']+)'\]", part)
                        if part_name_match:
                            simplified_path.append(part_name_match.group(1))
                        else:
                            # Если имени нет, берем тип и переводим
                            type_only = re.match(r'(\w+)', part)
                            if type_only:
                                type_name = type_only.group(1)
                                decoded = type_decode.get(type_name, type_name)
                                # Убираем эмодзи для пути
                                decoded = decoded.split(' ', 1)[-1] if ' ' in decoded else decoded
                                simplified_path.append(decoded)
                    
                    if simplified_path:
                        element_path = f"\n   📍 Расположение: {' ➜ '.join(simplified_path)}"
                
                # Извлекаем значения для ВВОД
                value_info = ""
                if event_type == 'ВВОД':
                    value_match = re.search(r"Было: '([^']*)' → Стало: '([^']*)'", message)
                    if value_match:
                        old_val = value_match.group(1)
                        new_val = value_match.group(2)
                        value_info = f"\n   Изменение: '{old_val}' ➜ '{new_val}'"
                
                # Формируем расшифровку
                decoded_message = f"{event_decode[event_type]}: {decoded_type}"
                if element_name != "без имени":
                    decoded_message += f" '{element_name}'"
                decoded_message += element_path
                decoded_message += value_info
                
                # Обновляем поле расшифровки (показываем только последние 10 событий)
                current_text = self.decode_area.toPlainText()
                lines = current_text.split('\n')
                
                # Добавляем новую строку
                lines.append(decoded_message)
                
                # Оставляем только последние 10 строк
                if len(lines) > 10:
                    lines = lines[-10:]
                
                self.decode_area.setPlainText('\n'.join(lines))
                
                # Прокручиваем вниз
                cursor = self.decode_area.textCursor()
                cursor.movePosition(cursor.End)
                self.decode_area.setTextCursor(cursor)
                
        except Exception as e:
            pass  # Игнорируем ошибки парсинга
