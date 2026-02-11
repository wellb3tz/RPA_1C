"""
Редактор операций - GUI для создания и настройки паттернов операций
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QLabel, QLineEdit, QTextEdit, 
                             QGroupBox, QFormLayout, QMessageBox, QListWidgetItem,
                             QCheckBox)
from PyQt5.QtCore import Qt
import json
import os


class OperationEditor(QDialog):
    def __init__(self, parent=None, analyzer=None):
        super().__init__(parent)
        self.analyzer = analyzer
        self.patterns_file = "config/operation_patterns.json"
        self.current_pattern_key = None
        self.init_ui()
        self.load_patterns()
        
    def init_ui(self):
        self.setWindowTitle("Редактор операций")
        self.setGeometry(200, 200, 900, 600)
        self.setWindowFlags(Qt.Window)
        
        layout = QHBoxLayout(self)
        
        # Левая панель - список операций
        left_panel = QVBoxLayout()
        
        list_label = QLabel("Список операций:")
        left_panel.addWidget(list_label)
        
        self.operations_list = QListWidget()
        self.operations_list.itemClicked.connect(self.on_operation_selected)
        left_panel.addWidget(self.operations_list)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.add_operation)
        buttons_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.delete_operation)
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)
        
        left_panel.addLayout(buttons_layout)
        
        layout.addLayout(left_panel, 1)
        
        # Правая панель - редактор операции
        right_panel = QVBoxLayout()
        
        # Группа основных настроек
        main_group = QGroupBox("Основные настройки")
        main_layout = QFormLayout()
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("operation_key")
        main_layout.addRow("Ключ операции:", self.key_input)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название операции")
        main_layout.addRow("Название:", self.name_input)
        
        main_group.setLayout(main_layout)
        right_panel.addWidget(main_group)
        
        # Группа триггеров начала
        start_group = QGroupBox("Триггеры начала операции")
        start_layout = QVBoxLayout()
        
        # Чекбокс для включения/отключения триггеров начала
        self.use_start_triggers = QCheckBox("Использовать триггеры начала")
        self.use_start_triggers.setChecked(True)
        self.use_start_triggers.stateChanged.connect(self.on_start_triggers_toggle)
        start_layout.addWidget(self.use_start_triggers)
        
        start_help = QLabel("Укажите слова/фразы, которые запускают операцию.\nКаждый триггер с новой строки.")
        start_help.setStyleSheet("color: gray; font-size: 10px;")
        start_layout.addWidget(start_help)
        
        self.start_triggers = QTextEdit()
        self.start_triggers.setPlaceholderText("Создать\nДобавить\nНовый")
        self.start_triggers.setMaximumHeight(100)
        start_layout.addWidget(self.start_triggers)
        
        start_group.setLayout(start_layout)
        right_panel.addWidget(start_group)
        
        # Группа промежуточных триггеров
        middle_group = QGroupBox("Промежуточные триггеры (опционально)")
        middle_layout = QVBoxLayout()
        
        middle_help = QLabel("Укажите слова/фразы, которые должны произойти во время операции.\nДостаточно ХОТЯ БЫ ОДНОГО совпадения для успешного завершения.\nКаждый триггер с новой строки.")
        middle_help.setStyleSheet("color: gray; font-size: 10px;")
        middle_layout.addWidget(middle_help)
        
        self.middle_triggers = QTextEdit()
        self.middle_triggers.setPlaceholderText("ВВОД\nВыбрать\nДобавить строку")
        self.middle_triggers.setMaximumHeight(100)
        middle_layout.addWidget(self.middle_triggers)
        
        middle_group.setLayout(middle_layout)
        right_panel.addWidget(middle_group)
        
        # Группа триггеров завершения
        end_group = QGroupBox("Триггеры завершения операции")
        end_layout = QVBoxLayout()
        
        end_help = QLabel("Укажите слова/фразы, которые завершают операцию.\nКаждый триггер с новой строки.")
        end_help.setStyleSheet("color: gray; font-size: 10px;")
        end_layout.addWidget(end_help)
        
        self.end_triggers = QTextEdit()
        self.end_triggers.setPlaceholderText("Записать\nОК\nПровести")
        self.end_triggers.setMaximumHeight(100)
        end_layout.addWidget(self.end_triggers)
        
        end_group.setLayout(end_layout)
        right_panel.addWidget(end_group)
        
        # Группа дополнительных настроек
        advanced_group = QGroupBox("Дополнительные настройки")
        advanced_layout = QFormLayout()
        
        self.timeout_input = QLineEdit()
        self.timeout_input.setText("30")
        self.timeout_input.setPlaceholderText("30")
        advanced_layout.addRow("Таймаут (сек):", self.timeout_input)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Описание операции для справки")
        self.description_input.setMaximumHeight(60)
        advanced_layout.addRow("Описание:", self.description_input)
        
        advanced_group.setLayout(advanced_layout)
        right_panel.addWidget(advanced_group)
        
        # Кнопки сохранения
        save_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.save_current_pattern)
        self.save_btn.setEnabled(False)
        save_layout.addWidget(self.save_btn)
        
        self.test_btn = QPushButton("🧪 Тест")
        self.test_btn.clicked.connect(self.test_pattern)
        self.test_btn.setEnabled(False)
        save_layout.addWidget(self.test_btn)
        
        right_panel.addLayout(save_layout)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        right_panel.addWidget(close_btn)
        
        layout.addLayout(right_panel, 2)
        
    def load_patterns(self):
        """Загрузить паттерны из файла или из анализатора"""
        self.operations_list.clear()
        
        if self.analyzer:
            for key, pattern in self.analyzer.patterns.items():
                item = QListWidgetItem(f"{pattern['name']} ({key})")
                item.setData(Qt.UserRole, key)
                self.operations_list.addItem(item)
    
    def on_operation_selected(self, item):
        """Обработка выбора операции из списка"""
        pattern_key = item.data(Qt.UserRole)
        self.current_pattern_key = pattern_key
        
        if self.analyzer and pattern_key in self.analyzer.patterns:
            pattern = self.analyzer.patterns[pattern_key]
            
            # Заполняем поля
            self.key_input.setText(pattern_key)
            self.key_input.setEnabled(False)  # Ключ нельзя менять
            
            self.name_input.setText(pattern['name'])
            
            # Триггеры начала
            start_triggers_list = pattern.get('triggers', [])
            if start_triggers_list:
                self.use_start_triggers.setChecked(True)
                start_triggers = '\n'.join(start_triggers_list)
                self.start_triggers.setPlainText(start_triggers)
                self.start_triggers.setEnabled(True)
            else:
                self.use_start_triggers.setChecked(False)
                self.start_triggers.clear()
                self.start_triggers.setEnabled(False)
            
            # Промежуточные триггеры
            middle_triggers = '\n'.join(pattern.get('middle_triggers', []))
            self.middle_triggers.setPlainText(middle_triggers)
            
            # Триггеры завершения
            end_triggers = '\n'.join(pattern.get('completion_triggers', []))
            self.end_triggers.setPlainText(end_triggers)
            
            # Дополнительные настройки
            self.timeout_input.setText(str(pattern.get('timeout', 30)))
            self.description_input.setPlainText(pattern.get('description', ''))
            
            self.save_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
    
    def add_operation(self):
        """Добавить новую операцию"""
        # Очищаем поля
        self.current_pattern_key = None
        self.key_input.clear()
        self.key_input.setEnabled(True)
        self.name_input.clear()
        self.use_start_triggers.setChecked(True)
        self.start_triggers.clear()
        self.start_triggers.setEnabled(True)
        self.middle_triggers.clear()
        self.end_triggers.clear()
        self.timeout_input.setText("30")
        self.description_input.clear()
        
        self.save_btn.setEnabled(True)
        self.test_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
        # Фокус на ключ
        self.key_input.setFocus()
    
    def on_start_triggers_toggle(self):
        """Обработка переключения чекбокса триггеров начала"""
        enabled = self.use_start_triggers.isChecked()
        self.start_triggers.setEnabled(enabled)
        if not enabled:
            self.start_triggers.clear()
    
    def save_current_pattern(self):
        """Сохранить текущий паттерн"""
        # Валидация
        key = self.key_input.text().strip()
        name = self.name_input.text().strip()
        
        if not key:
            QMessageBox.warning(self, "Ошибка", "Укажите ключ операции")
            return
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Укажите название операции")
            return
        
        # Проверка на дубликат ключа при создании новой операции
        if not self.current_pattern_key and key in self.analyzer.patterns:
            QMessageBox.warning(self, "Ошибка", f"Операция с ключом '{key}' уже существует")
            return
        
        # Собираем триггеры
        start_triggers = []
        if self.use_start_triggers.isChecked():
            start_triggers = [t.strip() for t in self.start_triggers.toPlainText().split('\n') if t.strip()]
            if not start_triggers:
                QMessageBox.warning(self, "Ошибка", "Если используются триггеры начала, укажите хотя бы один")
                return
        
        middle_triggers = [t.strip() for t in self.middle_triggers.toPlainText().split('\n') if t.strip()]
        end_triggers = [t.strip() for t in self.end_triggers.toPlainText().split('\n') if t.strip()]
        
        if not end_triggers:
            QMessageBox.warning(self, "Ошибка", "Укажите хотя бы один триггер завершения")
            return
        
        # Создаем паттерн
        pattern = {
            'name': name,
            'triggers': start_triggers,
            'middle_triggers': middle_triggers,
            'completion_triggers': end_triggers,
            'timeout': int(self.timeout_input.text() or 30),
            'description': self.description_input.toPlainText().strip()
        }
        
        # Сохраняем в анализатор
        if self.current_pattern_key:
            # Обновляем существующий
            self.analyzer.patterns[self.current_pattern_key] = pattern
        else:
            # Добавляем новый
            self.analyzer.patterns[key] = pattern
            self.current_pattern_key = key
        
        # Сохраняем в файл
        self.save_patterns_to_file()
        
        # Обновляем список
        self.load_patterns()
        
        QMessageBox.information(self, "Успех", f"Операция '{name}' сохранена")
        
        self.key_input.setEnabled(False)
        self.test_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
    
    def delete_operation(self):
        """Удалить операцию"""
        if not self.current_pattern_key:
            return
        
        pattern_name = self.analyzer.patterns[self.current_pattern_key]['name']
        
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            f"Удалить операцию '{pattern_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.analyzer.patterns[self.current_pattern_key]
            self.save_patterns_to_file()
            self.load_patterns()
            
            # Очищаем поля
            self.current_pattern_key = None
            self.key_input.clear()
            self.name_input.clear()
            self.use_start_triggers.setChecked(True)
            self.start_triggers.clear()
            self.start_triggers.setEnabled(True)
            self.middle_triggers.clear()
            self.end_triggers.clear()
            self.description_input.clear()
            
            self.save_btn.setEnabled(False)
            self.test_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            
            QMessageBox.information(self, "Успех", "Операция удалена")
    
    def test_pattern(self):
        """Тестировать паттерн"""
        if not self.current_pattern_key:
            return
        
        pattern = self.analyzer.patterns[self.current_pattern_key]
        
        test_info = f"Операция: {pattern['name']}\n\n"
        
        if pattern.get('triggers'):
            test_info += f"Триггеры начала ({len(pattern['triggers'])}):\n"
            test_info += "  • " + "\n  • ".join(pattern['triggers']) + "\n\n"
        else:
            test_info += "Триггеры начала: не используются\n"
            test_info += "  ℹ️ Операция начинается сразу при запуске мониторинга\n\n"
        
        if pattern.get('middle_triggers'):
            test_info += f"Промежуточные триггеры ({len(pattern['middle_triggers'])}):\n"
            test_info += "  • " + "\n  • ".join(pattern['middle_triggers'])
            test_info += "\n  ℹ️ Достаточно хотя бы одного совпадения\n\n"
        
        test_info += f"Триггеры завершения ({len(pattern['completion_triggers'])}):\n"
        test_info += "  • " + "\n  • ".join(pattern['completion_triggers']) + "\n\n"
        test_info += f"Таймаут: {pattern.get('timeout', 30)} секунд\n\n"
        
        if pattern.get('description'):
            test_info += f"Описание:\n{pattern['description']}"
        
        QMessageBox.information(self, "Тест паттерна", test_info)
    
    def save_patterns_to_file(self):
        """Сохранить паттерны в JSON файл"""
        try:
            # Создаем директорию если нужно
            os.makedirs(os.path.dirname(self.patterns_file), exist_ok=True)
            
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.analyzer.patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить файл: {str(e)}")
    
    def load_patterns_from_file(self):
        """Загрузить паттерны из JSON файла"""
        try:
            if os.path.exists(self.patterns_file):
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                    if self.analyzer:
                        self.analyzer.patterns = patterns
                        return True
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")
        
        return False
