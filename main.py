import sys
import json
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QComboBox, QTextEdit, QCheckBox, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QSplitter, QMessageBox,
    QGroupBox, QScrollArea, QGridLayout, QToolButton, QMenu
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QAction
from template_manager import TemplateManagerDialog
from query_history import QueryHistoryDialog, QueryHistoryManager
from data_visualizer import DataVisualizer

class QueryBuilder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Query Builder")
        self.setMinimumSize(1200, 800)
        
        # Initialize state
        self.query = ""
        self.results = None
        self.loading = False
        self.error = None
        self.db_config = {
            "type": "postgres",
            "url": "",
            "tableName": ""
        }
        self.read_only = True
        
        # Load saved config from file if exists
        try:
            with open("db_config.json", "r") as f:
                self.db_config = json.load(f)
        except FileNotFoundError:
            pass
        
        # Setup UI
        self.init_ui()
        
    def init_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        
        # Header
        header = QLabel("Query Builder")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Build and execute database queries with ease")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        main_layout.addWidget(subtitle)
        
        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)
        
        # Left panel (config and query)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Database config group
        db_config_group = QGroupBox("Database Connection")
        db_config_layout = QVBoxLayout(db_config_group)
        
        # Database type and table name
        db_type_layout = QHBoxLayout()
        db_type_label = QLabel("Database Type:")
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["PostgreSQL", "MySQL", "MongoDB"])
        
        # Map display names to internal values
        self.db_type_map = {
            "PostgreSQL": "postgres",
            "MySQL": "mysql",
            "MongoDB": "mongodb"
        }
        
        # Set initial selection
        for display_name, internal_value in self.db_type_map.items():
            if internal_value == self.db_config["type"]:
                self.db_type_combo.setCurrentText(display_name)
                break
                
        self.db_type_combo.currentTextChanged.connect(self.on_db_type_changed)
        
        table_name_label = QLabel("Table Name:")
        self.table_name_input = QLineEdit()
        self.table_name_input.setText(self.db_config.get("tableName", ""))
        self.table_name_input.textChanged.connect(self.on_table_name_changed)
        
        db_type_layout.addWidget(db_type_label)
        db_type_layout.addWidget(self.db_type_combo)
        db_type_layout.addWidget(table_name_label)
        db_type_layout.addWidget(self.table_name_input)
        
        # Connection string
        conn_layout = QVBoxLayout()
        conn_label = QLabel("Connection String:")
        self.conn_input = QLineEdit()
        self.conn_input.setText(self.db_config.get("url", ""))
        self.conn_input.setPlaceholderText(self.get_connection_placeholder())
        self.conn_input.textChanged.connect(self.on_connection_changed)
        
        conn_layout.addWidget(conn_label)
        conn_layout.addWidget(self.conn_input)
        
        # Add to db config layout
        db_config_layout.addLayout(db_type_layout)
        db_config_layout.addLayout(conn_layout)
        
        # Query editor group
        query_group = QGroupBox("Query Editor")
        query_layout = QVBoxLayout(query_group)
        
        # Add templates button
        templates_layout = QHBoxLayout()
        templates_label = QLabel("Templates:")
        self.templates_button = QPushButton("Browse Templates")
        self.templates_button.clicked.connect(self.show_templates)
        templates_layout.addWidget(templates_label)
        templates_layout.addWidget(self.templates_button)
        templates_layout.addStretch()
        query_layout.addLayout(templates_layout)
        
        self.query_editor = QTextEdit()
        self.query_editor.setPlaceholderText("Enter your SQL query here...")
        self.query_editor.setFont(QFont("Courier New", 10))
        self.query_editor.textChanged.connect(self.on_query_changed)
        
        query_layout.addWidget(self.query_editor)
        
        # Query controls
        query_controls = QHBoxLayout()
        
        self.read_only_check = QCheckBox("Read-only")
        self.read_only_check.setChecked(self.read_only)
        self.read_only_check.stateChanged.connect(self.on_read_only_changed)
        
        # Add history button
        self.history_button = QPushButton("History")
        self.history_button.clicked.connect(self.show_history)
        
        # Add save button
        self.save_button = QPushButton("Save Query")
        self.save_button.clicked.connect(self.save_query)
        
        self.run_button = QPushButton("Run Query")
        self.run_button.clicked.connect(self.handle_query_submit)
        
        query_controls.addWidget(self.read_only_check)
        query_controls.addWidget(self.history_button)
        query_controls.addWidget(self.save_button)
        query_controls.addStretch()
        query_controls.addWidget(self.run_button)
        
        query_layout.addLayout(query_controls)
        
        # Add groups to left panel
        left_layout.addWidget(db_config_group)
        left_layout.addWidget(query_group, 1)
        
        # Right panel (results)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        # Use the DataVisualizer component instead of just a table
        self.data_visualizer = DataVisualizer()
        results_layout.addWidget(self.data_visualizer)
        
        right_layout.addWidget(results_group)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 700])
        
        # Footer
        footer = QLabel("Designed and Built by Jonathan Young (iterating)")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer)
        
    def get_connection_placeholder(self):
        db_type = self.db_config["type"]
        if db_type == "postgres":
            return "postgresql://username:password@hostname:5432/database"
        elif db_type == "mysql":
            return "mysql://username:password@hostname:3306/database"
        elif db_type == "mongodb":
            return "mongodb://username:password@hostname:27017/database"
        return "Database connection string"
    
    def on_db_type_changed(self, text):
        self.db_config["type"] = self.db_type_map[text]
        self.conn_input.setPlaceholderText(self.get_connection_placeholder())
        self.save_config()
    
    def on_table_name_changed(self, text):
        self.db_config["tableName"] = text
        self.save_config()
    
    def on_connection_changed(self, text):
        self.db_config["url"] = text
        self.save_config()
    
    def on_query_changed(self):
        self.query = self.query_editor.toPlainText()
    
    def on_read_only_changed(self, state):
        self.read_only = state == Qt.CheckState.Checked
    
    def save_config(self):
        try:
            with open("db_config.json", "w") as f:
                json.dump(self.db_config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def handle_query_submit(self):
        if not self.query.strip():
            QMessageBox.warning(self, "Empty Query", "Please enter a query to execute.")
            return
        
        # Check if query contains {table_name} but no tableName is set
        if "{table_name}" in self.query and not self.db_config.get("tableName"):
            QMessageBox.warning(
                self, 
                "Table Name Required", 
                "Table name is required when using {table_name} placeholders."
            )
            return
        
        self.loading = True
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")
        self.error = None
        
        # Clear previous results
        self.data_visualizer.set_data(None)
        
        try:
            # In a real implementation, we would call the API
            # For now, we'll use a mock implementation
            self.execute_query()
            
            # Save successful query to history
            history_manager = QueryHistoryManager()
            history_manager.add_query(self.query, self.db_config["type"])
        except Exception as e:
            self.error = str(e)
            QMessageBox.critical(self, "Query Error", f"Error executing query: {self.error}")
        finally:
            self.loading = False
            self.run_button.setEnabled(True)
            self.run_button.setText("Run Query")
    
    def execute_query(self):
        """
        Execute the query by calling the backend API
        """
        try:
            # In a real implementation, this would be an API call
            # For demonstration, we'll use a direct request to the API
            api_url = "http://localhost:3000/api/queries/execute"
            
            # Extract readOnly flag from dbConfig
            config_to_send = self.db_config.copy()
            
            # Prepare the request payload
            payload = {
                "query": self.query,
                "dbConfig": config_to_send,
                "readOnly": self.read_only
            }
            
            # Make the API request
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                self.display_results(data)
            else:
                error_message = f"API Error ({response.status_code}): {response.text}"
                self.error = error_message
                QMessageBox.critical(self, "API Error", error_message)
                
        except requests.RequestException as e:
            error_message = f"Connection Error: {str(e)}"
            self.error = error_message
            QMessageBox.critical(self, "Connection Error", error_message)
            
            # For demonstration purposes, show mock data when API is not available
            self.display_mock_results()
    
    def display_mock_results(self):
        """Display mock results for demonstration purposes"""
        mock_data = [
            {"id": 1, "name": "Sample 1", "value": 100},
            {"id": 2, "name": "Sample 2", "value": 200},
            {"id": 3, "name": "Sample 3", "value": 300},
        ]
        self.display_results(mock_data)
    
    def display_results(self, data):
        """Display query results in the table view"""
        if not data or not isinstance(data, list) or len(data) == 0:
            self.data_visualizer.set_data(None)
            QMessageBox.information(self, "Query Result", "Query executed successfully, but returned no data.")
            return
        
        # Use the data visualizer to display the results
        self.data_visualizer.set_data(data)
        
        # Show success message
        QMessageBox.information(
            self, 
            "Query Success", 
            f"Query executed successfully. Returned {len(data)} rows."
        )
    
    def show_templates(self):
        """Show the template manager dialog"""
        db_type = self.db_config["type"]
        dialog = TemplateManagerDialog(db_type, self)
        dialog.template_selected.connect(self.apply_template)
        dialog.exec()
    
    def apply_template(self, template):
        """Apply the selected template to the query editor"""
        # Convert query to string if it's an object/array
        query_string = template["query"]
        if not isinstance(query_string, str):
            query_string = json.dumps(query_string, indent=2)
            
        self.query_editor.setPlainText(query_string)
        self.query = query_string
        
        # Only update the database type from the template
        # while preserving the existing URL and tableName
        if "database_type" in template:
            self.db_config["type"] = template["database_type"]
            
            # Update the UI to reflect the new database type
            for display_name, internal_value in self.db_type_map.items():
                if internal_value == self.db_config["type"]:
                    self.db_type_combo.setCurrentText(display_name)
                    break
    
    def show_history(self):
        """Show the query history dialog"""
        dialog = QueryHistoryDialog(self)
        dialog.query_selected.connect(self.apply_history_query)
        dialog.exec()
    
    def apply_history_query(self, query):
        """Apply a query from history"""
        self.query_editor.setPlainText(query)
        self.query = query
    
    def save_query(self):
        """Save the current query to history"""
        if not self.query.strip():
            QMessageBox.warning(self, "Empty Query", "Please enter a query to save.")
            return
        
        # Save to history
        history_manager = QueryHistoryManager()
        history_manager.add_query(self.query, self.db_config["type"])
        
        QMessageBox.information(self, "Save Query", "Query saved to history successfully!")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Set application-wide stylesheet for dark theme
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        QGroupBox {
            border: 1px solid #3e3e3e;
            border-radius: 5px;
            margin-top: 1ex;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 5px;
        }
        QTextEdit, QLineEdit, QTableWidget, QComboBox {
            background-color: #2d2d2d;
            border: 1px solid #3e3e3e;
            border-radius: 3px;
            color: #e0e0e0;
        }
        QPushButton {
            background-color: #8a2be2;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 5px 15px;
        }
        QPushButton:hover {
            background-color: #9b30ff;
        }
        QPushButton:disabled {
            background-color: #4a4a4a;
            color: #7a7a7a;
        }
        QTableWidget {
            gridline-color: #3e3e3e;
        }
        QHeaderView::section {
            background-color: #3e3e3e;
            color: #e0e0e0;
            padding: 5px;
            border: 1px solid #2d2d2d;
        }
        QTabWidget::pane {
            border: 1px solid #3e3e3e;
        }
        QTabBar::tab {
            background-color: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3e3e3e;
            padding: 5px 10px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #3e3e3e;
        }
        QCheckBox {
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 15px;
            height: 15px;
        }
        QCheckBox::indicator:unchecked {
            background-color: #2d2d2d;
            border: 1px solid #3e3e3e;
        }
        QCheckBox::indicator:checked {
            background-color: #8a2be2;
            border: 1px solid #3e3e3e;
        }
    """)
    
    window = QueryBuilder()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
