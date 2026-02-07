"""
Главное окно приложения
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QLineEdit, QComboBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from monitor.ui_monitor import UIMonitor


class MonitorThread(QThread):
    """Поток для мониторинга UI элементов"""
    log_signal = pyqtSignal(str)
    connection_signal = pyqtSignal(bool, str)  # (успех, сообщение)
    
    def __init__(self, process_name, monitor_mode):
        super().__init__()
        self.monitor = UIMonitor(process_name, monitor_mode)
        self.is_running = False
        
    def run(self):
        self.is_running = True
        self.monitor.start_monitoring(self.log_signal.emit, self.connection_signal.emit)
        
    def stop(self):
        self.is_running = False
        self.monitor.stop_monitoring()
    
    def set_mode(self, mode):
        """Изменить режим мониторинга"""
        self.monitor.set_mode(mode)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.monitor_thread = None
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
        
        self.mode_label = QLabel("Режим:")
        control_layout1.addWidget(self.mode_label)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Сканирование элементов", "scan")
        self.mode_combo.addItem("Только нажатия", "events")
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        control_layout1.addWidget(self.mode_combo)
        
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
        
        layout.addLayout(control_layout2)
        
        # Область логов
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # Статус бар
        self.statusBar().showMessage("Готов к работе")
        
    def start_monitoring(self):
        process_name = self.process_input.text()
        if not process_name:
            self.log_area.append("[ОШИБКА] Введите имя процесса")
            return
        
        monitor_mode = self.mode_combo.currentData()
        mode_text = self.mode_combo.currentText()
            
        self.log_area.append(f"[СТАРТ] Попытка подключения к процессу {process_name}...")
        self.log_area.append(f"[РЕЖИМ] {mode_text}")
        self.statusBar().showMessage(f"Подключение к {process_name}...")
            
        self.monitor_thread = MonitorThread(process_name, monitor_mode)
        self.monitor_thread.log_signal.connect(self.add_log)
        self.monitor_thread.connection_signal.connect(self.on_connection_status)
        self.monitor_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.mode_combo.setEnabled(False)
    
    def on_mode_changed(self):
        """Обработка изменения режима мониторинга"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            mode = self.mode_combo.currentData()
            mode_text = self.mode_combo.currentText()
            self.monitor_thread.set_mode(mode)
            self.log_area.append(f"\n[РЕЖИМ] Переключено на: {mode_text}\n")
        
    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.mode_combo.setEnabled(True)
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
        
    def clear_log(self):
        self.log_area.clear()
