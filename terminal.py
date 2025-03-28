import sys
import os
import sqlite3
from datetime import datetime
import subprocess
import logging
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QApplication, QMenuBar, QMessageBox, QFileDialog, QInputDialog, QStatusBar, QComboBox,
    QDialog, QTableWidget, QTableWidgetItem, QCompleter
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QStringListModel

# Configuración de logging
logging.basicConfig(filename="command_tool.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Directorio para la base de datos
DATABASE_DIR = "database"
DATABASE_PATH = os.path.join(DATABASE_DIR, "commands.db")

class CommandWorker(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, command, working_dir):
        super().__init__()
        self.command = command
        self.working_dir = working_dir

    def run(self):
        try:
            if self.command.lower() in ["clear", "cls"]:
                self.output_signal.emit("CLEAR_TERMINAL")
            else:
                result = subprocess.run(self.command, shell=True, capture_output=True, text=True, cwd=self.working_dir)
                output = result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
                self.output_signal.emit(output if output else "(No output)")
        except Exception as e:
            self.output_signal.emit(f"Error inesperado: {str(e)}")
        self.finished_signal.emit()

class CommandCompleter(QCompleter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchContains)

    def update_suggestions(self, aliases, history, working_dir):
        model = QStringListModel()
        dir_contents = [f for f in os.listdir(working_dir) if not f.startswith('.')]  # Files and dirs in current directory
        suggestions = list(set(aliases + history + dir_contents))
        model.setStringList(suggestions)
        self.setModel(model)

class ThemeManager:
    THEMES = {
        "Dark": {
            "background": "#1e1e1e",
            "text": "#d4d4d4",
            "highlight": "#007acc",
            "input_bg": "#252526",
            "border": "#3c3f41"
        },
        "Light": {
            "background": "#ffffff",
            "text": "#000000",
            "highlight": "#1e90ff",
            "input_bg": "#f0f0f0",
            "border": "#d0d0d0"
        },
        "Solarized": {
            "background": "#002b36",
            "text": "#839496",
            "highlight": "#268bd2",
            "input_bg": "#073642",
            "border": "#586e75"
        }
    }

    @classmethod
    def apply_theme(cls, widget, theme_name):
        theme = cls.THEMES.get(theme_name, cls.THEMES["Dark"])
        style_sheet = f"""
            QWidget {{ 
                background-color: {theme['background']}; 
                color: {theme['text']}; 
                font-family: Arial; 
            }}
            QLineEdit, QComboBox, QTextEdit {{ 
                background-color: {theme['input_bg']}; 
                border: 1px solid {theme['border']}; 
                color: {theme['text']}; 
                padding: 5px; 
            }}
            QPushButton {{ 
                background-color: {theme['highlight']}; 
                border: none; 
                padding: 8px; 
                border-radius: 4px; 
                color: white; 
            }}
            QPushButton:hover {{ background-color: {theme['highlight']}CC; }}
            QPushButton:disabled {{ background-color: {theme['border']}; }}
            QTreeWidget, QTableWidget {{ 
                background-color: {theme['input_bg']}; 
                border: 1px solid {theme['border']}; 
            }}
            QStatusBar {{ 
                background-color: {theme['background']}; 
                color: {theme['text']}; 
            }}
        """
        widget.setStyleSheet(style_sheet)

class SavedCommandsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Comandos Guardados")
        self.setMinimumSize(800, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.search_entry = QLineEdit()
        self.search_entry.setPlaceholderText("Buscar comandos...")
        self.search_entry.textChanged.connect(self.filter_commands)
        layout.addWidget(self.search_entry)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Alias", "Comando", "Descripción"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 300)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        run_btn = QPushButton("Ejecutar Seleccionado")
        run_btn.clicked.connect(self.run_selected)
        btn_layout.addWidget(run_btn)
        edit_btn = QPushButton("Editar Seleccionado")
        edit_btn.clicked.connect(self.edit_selected)
        btn_layout.addWidget(edit_btn)
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_commands()

    def load_commands(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT alias, command, description FROM saved_commands ORDER BY alias")
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(len(rows))
        for row_idx, (alias, command, description) in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(alias))
            self.table.setItem(row_idx, 1, QTableWidgetItem(command))
            self.table.setItem(row_idx, 2, QTableWidgetItem(description or ""))
        self.table.resizeColumnsToContents()

    def filter_commands(self):
        search_term = self.search_entry.text().lower()
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT alias, command, description FROM saved_commands WHERE alias LIKE ? OR command LIKE ? OR description LIKE ? ORDER BY alias",
                      (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(len(rows))
        for row_idx, (alias, command, description) in enumerate(rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(alias))
            self.table.setItem(row_idx, 1, QTableWidgetItem(command))
            self.table.setItem(row_idx, 2, QTableWidgetItem(description or ""))

    def run_selected(self):
        selected = self.table.selectedItems()
        if selected:
            alias = selected[0].text()
            self.parent().command_entry.setCurrentText(
                self.parent().execute_sql("SELECT command FROM saved_commands WHERE alias = ?", (alias,))[0][0]
            )
            self.parent().show_command_section()
            self.parent().execute_command()
            self.close()

    def edit_selected(self):
        selected = self.table.selectedItems()
        if selected:
            old_alias = selected[0].text()
            old_command = selected[1].text()
            old_description = selected[2].text()
            
            new_alias, ok1 = QInputDialog.getText(self, "Editar Alias", "Nuevo alias:", text=old_alias)
            if not ok1:
                return
            new_command, ok2 = QInputDialog.getText(self, "Editar Comando", "Nuevo comando:", text=old_command)
            if not ok2:
                return
            new_description, ok3 = QInputDialog.getText(self, "Editar Descripción", "Nueva descripción:", text=old_description)
            if not ok3:
                return
                
            if new_alias != old_alias or new_command != old_command or new_description != old_description:
                try:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE saved_commands SET alias = ?, command = ?, description = ? WHERE alias = ?",
                                 (new_alias, new_command, new_description, old_alias))
                    conn.commit()
                    conn.close()
                    self.load_commands()
                    self.parent().load_aliases()
                    self.parent().status_bar.showMessage(f"Alias '{old_alias}' editado.", 5000)
                except sqlite3.IntegrityError:
                    QMessageBox.critical(self, "Error", "El nuevo alias ya existe.")

class CommandToolApp(QWidget):
    def __init__(self):
        super().__init__()
        if not os.path.exists(DATABASE_DIR):
            os.makedirs(DATABASE_DIR)
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.create_tables()
        self.working_dir = os.getcwd()
        self.current_theme = "Dark"
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Terminal Avanzada")
        self.setGeometry(100, 100, 1000, 750)
        ThemeManager.apply_theme(self, self.current_theme)

        main_layout = QVBoxLayout()

        menubar = QMenuBar(self)
        view_menu = menubar.addMenu("Vistas")
        view_menu.addAction("Terminal", self.show_command_section)
        view_menu.addAction("Alias", self.show_alias_section)
        view_menu.addAction("Historial", self.show_history_section)
        tools_menu = menubar.addMenu("Herramientas")
        tools_menu.addAction("Mostrar Comandos Guardados", self.show_saved_commands)
        tools_menu.addAction("Importar Alias", self.import_aliases)
        tools_menu.addAction("Exportar Alias", self.export_aliases)
        theme_menu = menubar.addMenu("Temas")
        for theme in ThemeManager.THEMES.keys():
            theme_menu.addAction(theme, lambda t=theme: self.change_theme(t))
        help_menu = menubar.addMenu("Ayuda")
        help_menu.addAction("Acerca de", self.show_about)
        main_layout.addWidget(menubar)

        self.command_frame = QWidget()
        self.alias_frame = QWidget()
        self.history_frame = QWidget()

        # Command Section
        command_layout = QVBoxLayout()
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Ruta de ejecución:"))
        self.path_entry = QLineEdit(self.working_dir)
        self.path_entry.returnPressed.connect(self.update_working_dir)
        path_layout.addWidget(self.path_entry)
        path_btn = QPushButton("📂 Cambiar")
        path_btn.clicked.connect(self.change_working_dir)
        path_layout.addWidget(path_btn)
        command_layout.addLayout(path_layout)

        command_input_layout = QHBoxLayout()
        command_input_layout.addWidget(QLabel("Comando:"))
        self.command_entry = QComboBox()
        self.command_entry.setEditable(True)
        self.command_entry.setMinimumWidth(500)
        self.command_entry.addItems(self.get_history_commands())
        self.completer = CommandCompleter(self.command_entry)
        self.command_entry.setCompleter(self.completer)
        self.command_entry.lineEdit().returnPressed.connect(self.execute_command)
        command_input_layout.addWidget(self.command_entry)
        command_layout.addLayout(command_input_layout)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ Ejecutar")
        self.run_btn.clicked.connect(self.execute_command)
        btn_layout.addWidget(self.run_btn)
        save_btn = QPushButton("💾 Guardar Alias")
        save_btn.clicked.connect(self.save_command)
        btn_layout.addWidget(save_btn)
        script_btn = QPushButton("📜 Ejecutar Script")
        script_btn.clicked.connect(self.run_script)
        btn_layout.addWidget(script_btn)
        external_btn = QPushButton("↗ En Nueva Ventana")
        external_btn.clicked.connect(self.run_in_external_terminal)
        btn_layout.addWidget(external_btn)
        clear_btn = QPushButton("🗑 Limpiar")
        clear_btn.clicked.connect(self.clear_output)
        btn_layout.addWidget(clear_btn)
        command_layout.addLayout(btn_layout)

        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 11))
        self.output_text.setMinimumHeight(400)
        command_layout.addWidget(self.output_text)
        self.command_frame.setLayout(command_layout)

        # Alias Section
        alias_layout = QVBoxLayout()
        alias_layout.addWidget(QLabel("Buscar Alias:"))
        self.alias_search_entry = QLineEdit()
        self.alias_search_entry.textChanged.connect(self.filter_aliases)
        alias_layout.addWidget(self.alias_search_entry)
        self.alias_tree = QTreeWidget()
        self.alias_tree.setHeaderLabels(["Alias", "Comando"])
        self.alias_tree.setColumnWidth(0, 200)
        alias_layout.addWidget(self.alias_tree)
        alias_btn_layout = QHBoxLayout()
        alias_btn_layout.addWidget(QPushButton("▶ Ejecutar", clicked=self.run_alias))
        alias_btn_layout.addWidget(QPushButton("✏ Editar", clicked=self.edit_alias))
        alias_btn_layout.addWidget(QPushButton("🗑 Eliminar", clicked=self.delete_alias))
        alias_layout.addLayout(alias_btn_layout)
        self.alias_frame.setLayout(alias_layout)
        self.load_aliases()

        # History Section
        history_layout = QVBoxLayout()
        history_layout.addWidget(QLabel("Buscar en Historial:"))
        self.history_search_entry = QLineEdit()
        self.history_search_entry.textChanged.connect(self.search_history)
        history_layout.addWidget(self.history_search_entry)
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Favorito", "Comando", "Fecha y Hora"])
        self.history_tree.setColumnWidth(0, 50)
        self.history_tree.setColumnWidth(1, 400)
        self.history_tree.itemDoubleClicked.connect(self.run_history_command)
        self.history_tree.itemClicked.connect(self.toggle_favorite)
        history_layout.addWidget(self.history_tree)
        history_layout.addWidget(QPushButton("📤 Exportar Historial", clicked=self.export_history))
        self.history_frame.setLayout(history_layout)
        self.load_history()

        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

        main_layout.addWidget(self.command_frame)
        main_layout.addWidget(self.alias_frame)
        main_layout.addWidget(self.history_frame)
        self.setLayout(main_layout)
        self.show_command_section()
        self.update_completer()

    def create_tables(self):
        self.execute_sql('''CREATE TABLE IF NOT EXISTS saved_commands 
                           (id INTEGER PRIMARY KEY, alias TEXT UNIQUE, command TEXT, description TEXT)''')
        self.execute_sql('''CREATE TABLE IF NOT EXISTS history 
                           (id INTEGER PRIMARY KEY, command TEXT, timestamp TEXT, favorite INTEGER DEFAULT 0)''')

    def execute_sql(self, query, params=None):
        with self.conn:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall() if cursor.description else None

    def is_valid_command(self, command):
        forbidden = ['rm -rf', 'format', 'del']
        return not any(cmd in command.lower() for cmd in forbidden)

    def execute_command(self):
        try:
            command = self.command_entry.currentText().strip()
            if not command:
                raise ValueError("El comando no puede estar vacío")
            
            if not self.is_valid_command(command):
                raise ValueError("Comando potencialmente peligroso detectado")

            alias_result = self.execute_sql("SELECT command FROM saved_commands WHERE alias = ?", (command,))
            if alias_result:
                command = alias_result[0][0]
                self.command_entry.setCurrentText(command)

            if any(c in command for c in ['|', '&', ';']) and QMessageBox.question(self, "Advertencia", 
                "El comando contiene caracteres potencialmente peligrosos. ¿Continuar?") != QMessageBox.Yes:
                return
            
            prompt = f"{self.working_dir}> {command}"
            self.output_text.append(f"\n{prompt}")
            self.run_btn.setEnabled(False)
            self.status_bar.showMessage("Ejecutando comando...")
            
            self.worker = CommandWorker(command, self.working_dir)
            self.worker.output_signal.connect(self.display_output)
            self.worker.finished_signal.connect(self.command_finished)
            self.worker.start()

            self.execute_sql("INSERT INTO history (command, timestamp) VALUES (?, ?)", 
                           (command, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.load_history()
            self.update_completer()
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}", 5000)
            logging.error(f"Command execution failed: {str(e)}")
            self.run_btn.setEnabled(True)

    def display_output(self, output):
        if output == "CLEAR_TERMINAL":
            self.clear_output()
        else:
            self.output_text.append(output)

    def command_finished(self):
        self.run_btn.setEnabled(True)
        self.command_entry.clearEditText()
        self.status_bar.showMessage("Comando ejecutado.", 5000)
        logging.info(f"Comando ejecutado desde {self.working_dir}: {self.command_entry.currentText()}")

    def save_command(self):
        command = self.command_entry.currentText().strip()
        if not command:
            self.status_bar.showMessage("Error: El comando no puede estar vacío.", 5000)
            return
        alias, ok1 = QInputDialog.getText(self, "Alias", "Ingrese un alias para el comando:")
        if not ok1:
            return
        description, ok2 = QInputDialog.getText(self, "Descripción", "Ingrese una descripción para el comando:")
        if not ok2:
            return
        if ok1 and alias:
            try:
                self.execute_sql("INSERT INTO saved_commands (alias, command, description) VALUES (?, ?, ?)", 
                               (alias, command, description))
                self.load_aliases()
                self.update_completer()
                self.status_bar.showMessage(f"Alias '{alias}' guardado.", 5000)
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Error", "El alias ya existe. Use uno diferente.")

    def load_aliases(self):
        self.alias_tree.clear()
        rows = self.execute_sql("SELECT alias, command FROM saved_commands")
        for row in rows or []:
            QTreeWidgetItem(self.alias_tree, list(row))

    def filter_aliases(self):
        search_term = self.alias_search_entry.text().lower()
        self.alias_tree.clear()
        rows = self.execute_sql("SELECT alias, command FROM saved_commands WHERE alias LIKE ?", (f"%{search_term}%",))
        for row in rows:
            QTreeWidgetItem(self.alias_tree, list(row))

    def run_alias(self):
        selected = self.alias_tree.selectedItems()
        if selected:
            alias = selected[0].text(0)
            command = self.execute_sql("SELECT command FROM saved_commands WHERE alias = ?", (alias,))[0][0]
            self.command_entry.setCurrentText(command)
            self.show_command_section()
            self.execute_command()

    def edit_alias(self):
        selected = self.alias_tree.selectedItems()
        if selected:
            old_alias = selected[0].text(0)
            old_command = selected[0].text(1)
            new_alias, ok1 = QInputDialog.getText(self, "Editar Alias", "Nuevo alias:", text=old_alias)
            if not ok1:
                return
            new_command, ok2 = QInputDialog.getText(self, "Editar Comando", "Nuevo comando:", text=old_command)
            if not ok2:
                return
            new_description, ok3 = QInputDialog.getText(self, "Editar Descripción", "Nueva descripción:")
            if not ok3:
                return
            if new_alias != old_alias or new_command != old_command:
                try:
                    self.execute_sql("UPDATE saved_commands SET alias = ?, command = ?, description = ? WHERE alias = ?", 
                                   (new_alias, new_command, new_description, old_alias))
                    self.load_aliases()
                    self.update_completer()
                    self.status_bar.showMessage(f"Alias editado: {old_alias} -> {new_alias}", 5000)
                except sqlite3.IntegrityError:
                    QMessageBox.critical(self, "Error", "El nuevo alias ya existe.")

    def delete_alias(self):
        selected = self.alias_tree.selectedItems()
        if selected and QMessageBox.question(self, "Confirmar", "¿Eliminar el alias seleccionado?") == QMessageBox.Yes:
            alias = selected[0].text(0)
            self.execute_sql("DELETE FROM saved_commands WHERE alias = ?", (alias,))
            self.load_aliases()
            self.update_completer()
            self.status_bar.showMessage(f"Alias '{alias}' eliminado.", 5000)

    def load_history(self):
        self.history_tree.clear()
        rows = self.execute_sql("SELECT favorite, command, timestamp FROM history ORDER BY favorite DESC, timestamp DESC LIMIT 100")
        for row in rows or []:
            item = QTreeWidgetItem(self.history_tree, ["★" if row[0] else "", row[1], row[2]])
            item.setTextAlignment(0, Qt.AlignCenter)

    def search_history(self):
        search_term = self.history_search_entry.text().lower()
        self.history_tree.clear()
        rows = self.execute_sql("SELECT favorite, command, timestamp FROM history WHERE command LIKE ? ORDER BY favorite DESC, timestamp DESC", 
                               (f"%{search_term}%",))
        for row in rows:
            item = QTreeWidgetItem(self.history_tree, ["★" if row[0] else "", row[1], row[2]])
            item.setTextAlignment(0, Qt.AlignCenter)

    def run_history_command(self, item, column):
        command = item.text(1)
        self.command_entry.setCurrentText(command)
        self.show_command_section()
        self.execute_command()

    def toggle_favorite(self, item, column):
        if column == 0:
            command = item.text(1)
            current_fav = 1 if item.text(0) == "★" else 0
            new_fav = 0 if current_fav else 1
            self.execute_sql("UPDATE history SET favorite = ? WHERE command = ? AND timestamp = ?", 
                            (new_fav, command, item.text(2)))
            self.load_history()

    def export_history(self):
        file_path = QFileDialog.getSaveFileName(self, "Exportar Historial", "", "Text files (*.txt)")[0]
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                rows = self.execute_sql("SELECT command, timestamp FROM history ORDER BY timestamp DESC")
                for row in rows:
                    file.write(f"{row[1]}: {row[0]}\n")
            self.status_bar.showMessage("Historial exportado correctamente.", 5000)

    def export_aliases(self):
        file_path = QFileDialog.getSaveFileName(self, "Exportar Alias", "", "JSON files (*.json)")[0]
        if file_path:
            rows = self.execute_sql("SELECT alias, command, description FROM saved_commands")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({row[0]: {"command": row[1], "description": row[2]} for row in rows}, f)
            self.status_bar.showMessage("Alias exportados correctamente.", 5000)

    def import_aliases(self):
        file_path = QFileDialog.getOpenFileName(self, "Importar Alias", "", "JSON files (*.json)")[0]
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                aliases = json.load(f)
            for alias, data in aliases.items():
                try:
                    self.execute_sql("INSERT INTO saved_commands (alias, command, description) VALUES (?, ?, ?)", 
                                   (alias, data["command"], data.get("description", "")))
                except sqlite3.IntegrityError:
                    continue
            self.load_aliases()
            self.update_completer()
            self.status_bar.showMessage("Alias importados correctamente.", 5000)

    def change_working_dir(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Seleccionar Directorio", self.working_dir)
        if new_dir:
            self.working_dir = new_dir
            self.path_entry.setText(new_dir)
            self.update_completer()
            self.status_bar.showMessage(f"Directorio cambiado a: {new_dir}", 5000)

    def update_working_dir(self):
        new_dir = self.path_entry.text().strip()
        if os.path.isdir(new_dir):
            self.working_dir = new_dir
            self.update_completer()
            self.status_bar.showMessage(f"Directorio actualizado a: {new_dir}", 5000)
        else:
            self.status_bar.showMessage("Error: Directorio inválido.", 5000)
            self.path_entry.setText(self.working_dir)

    def run_script(self):
        script_path = QFileDialog.getOpenFileName(self, "Seleccionar Script", "", "Scripts (*.sh *.py *.bat)")[0]
        if script_path:
            command = f"bash {script_path}" if script_path.endswith(".sh") else f"python {script_path}" if script_path.endswith(".py") else script_path
            self.command_entry.setCurrentText(command)
            self.execute_command()

    def run_in_external_terminal(self):
        command = self.command_entry.currentText().strip()
        if command:
            if sys.platform == "win32":
                subprocess.Popen(f"cmd /k cd /d {self.working_dir} && {command}", creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(f"cd {self.working_dir} && {command}", shell=True, executable="/bin/bash")
            self.status_bar.showMessage("Comando ejecutado en terminal externa.", 5000)

    def clear_output(self):
        self.output_text.clear()
        self.status_bar.showMessage("Terminal limpiada.", 5000)

    def get_history_commands(self):
        rows = self.execute_sql("SELECT DISTINCT command FROM history ORDER BY timestamp DESC LIMIT 20")
        return [row[0] for row in rows] if rows else []

    def update_completer(self):
        aliases = [row[0] for row in self.execute_sql("SELECT alias FROM saved_commands") or []]
        history = self.get_history_commands()
        self.completer.update_suggestions(aliases, history, self.working_dir)

    def show_command_section(self):
        self.alias_frame.hide()
        self.history_frame.hide()
        self.command_frame.show()

    def show_alias_section(self):
        self.command_frame.hide()
        self.history_frame.hide()
        self.alias_frame.show()

    def show_history_section(self):
        self.command_frame.hide()
        self.alias_frame.hide()
        self.history_frame.show()

    def show_saved_commands(self):
        dialog = SavedCommandsDialog(self)
        dialog.exec_()

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        ThemeManager.apply_theme(self, theme_name)
        self.status_bar.showMessage(f"Tema cambiado a: {theme_name}", 5000)

    def show_about(self):
        QMessageBox.information(self, "Acerca de", "Terminal Avanzada\nVersión 1.0\nCreado con PyQt5")

    def save_config(self):
        config = {
            'working_dir': self.working_dir,
            'window_geometry': self.geometry().getRect(),
            'theme': self.current_theme
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.working_dir = config.get('working_dir', os.getcwd())
                self.path_entry.setText(self.working_dir)
                self.setGeometry(*config.get('window_geometry', (100, 100, 1000, 750)))
                self.change_theme(config.get('theme', 'Dark'))
        except FileNotFoundError:
            pass

    def closeEvent(self, event):
        self.save_config()
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommandToolApp()
    window.load_config()
    window.show()
    sys.exit(app.exec_())
