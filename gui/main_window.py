"""
Главное окно приложения
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTextEdit, QLabel, QLineEdit)
from PyQt5.QtCore import QThread, pyqtSignal
from monitor.ui_monitor import UIMonitor


class MonitorThread(QThread):
    """Поток для мониторинга UI элементов"""
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.monitor = UIMonitor()
        self.is_running = False
        
    def run(self):
        self.is_running = True
        self.monitor.start_monitoring(self.log_signal.emit)
        
    def stop(self):
        self.is_running = False
        self.monitor.stop_monitoring()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.monitor_thread = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("1С UI Monitor")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Панель управления
        control_layout = QHBoxLayout()
        
        self.process_label = QLabel("Имя процесса:")
        control_layout.addWidget(self.process_label)
        
        self.process_input = QLineEdit()
        self.process_input.setText("1cv8.exe")
        self.process_input.setPlaceholderText("Введите имя процесса 1С")
        control_layout.addWidget(self.process_input)
        
        self.start_btn = QPushButton("Начать мониторинг")
        self.start_btn.clicked.connect(self.start_monitoring)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.clicked.connect(self.stop_monitoring)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("Очистить лог")
        self.clear_btn.clicked.connect(self.clear_log)
        control_layout.addWidget(self.clear_btn)
        
        layout.addLayout(control_layout)
        
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
            
        self.monitor_thread = MonitorThread()
        self.monitor_thread.log_signal.connect(self.add_log)
        self.monitor_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.statusBar().showMessage(f"Мониторинг процесса: {process_name}")
        self.log_area.append(f"[СТАРТ] Начат мониторинг процесса {process_name}\n")
        
    def stop_monitoring(self):
        if self.monitor_thread:
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("Мониторинг остановлен")
        self.log_area.append("\n[СТОП] Мониторинг остановлен\n")
        
    def add_log(self, message):
        self.log_area.append(message)
        
    def clear_log(self):
        self.log_area.clear()
