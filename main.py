import sys
import json
import requests
import os
import pathlib
import logging
from datetime import datetime
from dotenv import load_dotenv
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QComboBox, QTextEdit, QCheckBox, QPushButton, 
    QTabWidget, QTableWidget, QTableWidgetItem, QSplitter, QMessageBox,
    QGroupBox, QScrollArea, QGridLayout, QToolButton, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QColor, QAction
from template_manager import TemplateManagerDialog
from query_history import QueryHistoryDialog, QueryHistoryManager
from data_visualizer import DataVisualizer

# Configure logging
def setup_logging():
    logs_dir = pathlib.Path("logs")
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"querybuilder_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger
    logger = logging.getLogger("QueryBuilder")
    logger.info(f"Log file created at: {log_file}")
    return logger

# Create logger
logger = setup_logging()

class QueryBuilder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Query Builder")
        self.setMinimumSize(1200, 800)
        
        logger.info("Initializing QueryBuilder application")
        
        parent_env_path = pathlib.Path(__file__).parent.parent / '.env'
        if parent_env_path.exists():
            load_dotenv(dotenv_path=parent_env_path)
            logger.info(f"Loaded environment variables from: {parent_env_path}")
        else:
            load_dotenv() 
            logger.info("Attempted to load environment variables from current directory")
            
        # Set API base URL with fallback to production URL if env var not found
        self.api_base_url = os.getenv("VITE_API_URL", "https://querybuilder.vercel.app")
        logger.info(f"API base URL set to: {self.api_base_url}")
        
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
        
        # Add test query button
        self.test_query_button = QPushButton("Load Test Query")
        self.test_query_button.clicked.connect(self.load_test_query)
        
        templates_layout.addWidget(templates_label)
        templates_layout.addWidget(self.templates_button)
        templates_layout.addWidget(self.test_query_button)
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
        
        # Use the DataVisualizer component instead of a table
        self.data_visualizer = DataVisualizer()
        results_layout.addWidget(self.data_visualizer)
        
        right_layout.addWidget(results_group)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([500, 700])
        
        # Footer
        footer_layout = QHBoxLayout()
        footer = QLabel("Designed and Built by Jonathan Young (iterating)")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add export logs button
        self.export_logs_button = QPushButton("Export Logs")
        self.export_logs_button.clicked.connect(self.export_logs)
        
        # Add test query button for troubleshooting
        self.test_api_button = QPushButton("Test API")
        self.test_api_button.clicked.connect(self.run_test_query)
        
        footer_layout.addWidget(self.export_logs_button)
        footer_layout.addWidget(self.test_api_button)
        footer_layout.addStretch()
        footer_layout.addWidget(footer)
        footer_layout.addStretch()
        
        main_layout.addLayout(footer_layout)
        
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
        logger.info(f"Database type changed to: {self.db_config['type']}")
    
    def on_table_name_changed(self, text):
        self.db_config["tableName"] = text
        self.save_config()
        logger.info(f"Table name changed to: {self.db_config['tableName']}")
    
    def on_connection_changed(self, text):
        self.db_config["url"] = text
        self.save_config()
        logger.info(f"Connection string updated")
    
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
            logger.warning("Query submission attempted with empty query")
            return
        
        # Check if query contains {table_name} but no tableName is set
        if "{table_name}" in self.query and not self.db_config.get("tableName"):
            QMessageBox.warning(
                self, 
                "Table Name Required", 
                "Table name is required when using {table_name} placeholders."
            )
            logger.warning("Query with {table_name} placeholder attempted without table name set")
            return
        
        logger.info(f"Executing query for database type: {self.db_config['type']}")
        logger.info(f"Read-only mode: {self.read_only}")
        
        self.loading = True
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")
        self.error = None
        
        # Clear previous results
        self.data_visualizer.set_data(None)
        
        try:
            # Execute the query via API
            self.execute_query()
            
            # Only save to history if no error occurred
            if not self.error:
                history_manager = QueryHistoryManager()
                history_manager.add_query(self.query, self.db_config["type"])
                logger.info("Query executed successfully and saved to history")
        except Exception as e:
            self.error = str(e)
            logger.error(f"Error executing query: {self.error}", exc_info=True)
            QMessageBox.critical(self, "Query Error", f"Error executing query: {self.error}")
        finally:
            self.loading = False
            self.run_button.setEnabled(True)
            self.run_button.setText("Run Query")
    
    def execute_query(self):
        try:
            # Process query for PostgreSQL table name substitution
            processed_query = self.query
            if self.db_config["type"] == "postgres" and "{table_name}" in self.query:
                # PostgreSQL doesn't support curly brace syntax directly
                # Replace {table_name} with properly quoted table name
                table_name = self.db_config.get("tableName", "")
                processed_query = self.query.replace("{table_name}", f'"{table_name}"')
                logger.info(f"Processed PostgreSQL query with table name substitution: {table_name}")
            
            # API endpoint for query execution
            api_url = f"{self.api_base_url}/api/queries/execute"
            logger.info(f"Sending request to API: {api_url}")
            
            # Prepare the database configuration to send
            config_to_send = self.db_config.copy()
            
            # Prepare the request payload
            payload = {
                "query": processed_query,
                "dbConfig": config_to_send,
                "readOnly": self.read_only
            }
            
            # Make the API request with proper headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Log the request for debugging
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            # Add more detailed logging
            logger.info(f"Sending request to: {api_url}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            logger.info(f"API response status code: {response.status_code}")
            
            # Log full response for debugging
            logger.info(f"API response headers: {dict(response.headers)}")
            logger.info(f"API response content: {response.text[:500]}...")  # Log first 500 chars to avoid huge logs
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Query returned {len(data.get('data', [])) if isinstance(data, dict) and 'data' in data else 0} results")
                logger.info(f"Response data type: {type(data)}")
                if isinstance(data, dict):
                    logger.info(f"Response data keys: {list(data.keys())}")
                self.display_results(data)
            else:
                error_message = f"API Error ({response.status_code}): {response.text}"
                logger.error(f"API error: {error_message}")
                self.error = error_message
                QMessageBox.critical(self, "API Error", error_message)
                
        except requests.RequestException as e:
            error_message = f"Connection Error: {str(e)}"
            logger.error(f"Connection error: {error_message}", exc_info=True)
            self.error = error_message
            QMessageBox.critical(self, "Connection Error", error_message)
            
            # For demonstration purposes, show mock data when API is not available
            logger.info("Showing mock data due to connection error")
            self.display_mock_results()
    
    def display_mock_results(self):
        mock_data = [
            {"id": 1, "name": "Sample 1", "value": 100},
            {"id": 2, "name": "Sample 2", "value": 200},
            {"id": 3, "name": "Sample 3", "value": 300},
        ]
        self.display_results(mock_data)
    
    def display_results(self, data):
        logger.info(f"display_results received data of type: {type(data)}")
        
        # Handle different response formats
        if isinstance(data, dict) and 'data' in data:
            # API might return data in a nested 'data' field
            logger.info("Extracting data from 'data' field in response")
            actual_data = data['data']
        else:
            actual_data = data
            
        # Check if we have valid data to display
        if not actual_data or (isinstance(actual_data, list) and len(actual_data) == 0):
            self.data_visualizer.set_data(None)
            logger.info("Query executed successfully but returned no data")
            QMessageBox.information(self, "Query Result", "Query executed successfully, but returned no data.")
            return
        
        # Use the data visualizer to display the results
        logger.info(f"Sending data to visualizer: {type(actual_data)}, sample: {str(actual_data)[:200]}...")
        self.data_visualizer.set_data(actual_data)
        
        # Calculate row count based on data type
        if isinstance(actual_data, list):
            row_count = len(actual_data)
        elif isinstance(actual_data, dict):
            row_count = 1
        else:
            row_count = 0
            
        logger.info(f"Displayed {row_count} rows of data in the visualizer")
        
        # Show success message
        QMessageBox.information(
            self, 
            "Query Success", 
            f"Query executed successfully. Returned {row_count} rows."
        )
    
    def show_templates(self):
        db_type = self.db_config["type"]
        dialog = TemplateManagerDialog(db_type, self)
        dialog.template_selected.connect(self.apply_template)
        dialog.exec()
    
    def apply_template(self, template):
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
        dialog = QueryHistoryDialog(self)
        dialog.query_selected.connect(self.apply_history_query)
        dialog.exec()
    
    def apply_history_query(self, query):
        self.query_editor.setPlainText(query)
        self.query = query
    
    def save_query(self):
        if not self.query.strip():
            QMessageBox.warning(self, "Empty Query", "Please enter a query to save.")
            return
        
        # Save to history
        history_manager = QueryHistoryManager()
        history_manager.add_query(self.query, self.db_config["type"])
        
        QMessageBox.information(self, "Save Query", "Query saved to history successfully!")
    
    def load_test_query(self):
        if self.db_config["type"] == "postgres":
            # Simple query to test PostgreSQL connection
            test_query = "SELECT current_database() as database, current_user as user, version() as version;"
        elif self.db_config["type"] == "mysql":
            test_query = "SELECT database() as database, user() as user, version() as version;"
        elif self.db_config["type"] == "mongodb":
            test_query = "{ find: 'system.version', limit: 1 }"
        else:
            test_query = "-- Please select a database type"
            
        self.query_editor.setPlainText(test_query)
        self.query = test_query
        logger.info(f"Loaded test query for {self.db_config['type']}")
        
    def export_logs(self):
        try:
            logs_dir = pathlib.Path("logs")
            if logs_dir.exists() and any(logs_dir.iterdir()):
                # Get the most recent log file
                log_files = sorted(logs_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
                if log_files:
                    latest_log = log_files[0]
                    
                    # Ask user where to save the log file
                    file_dialog = QFileDialog()
                    save_path, _ = file_dialog.getSaveFileName(
                        self, 
                        "Save Log File", 
                        f"querybuilder_log_{datetime.now().strftime('%Y%m%d')}.log",
                        "Log Files (*.log);;All Files (*)"
                    )
                    
                    if save_path:
                        # Copy the log file to the selected location
                        with open(latest_log, 'r') as src, open(save_path, 'w') as dst:
                            dst.write(src.read())
                        logger.info(f"Exported log file to: {save_path}")
                        QMessageBox.information(self, "Log Export", f"Log file exported to: {save_path}")
                else:
                    QMessageBox.warning(self, "No Logs", "No log files found to export.")
            else:
                QMessageBox.warning(self, "No Logs", "No log files found to export.")
        except Exception as e:
            logger.error(f"Error exporting logs: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"Error exporting logs: {str(e)}")
            
    def run_test_query(self):
        logger.info("Running test query to troubleshoot API responses")
        
        # Simple test query
        test_query = "SELECT 1 as test"
        
        # Set up a basic configuration
        test_config = {
            "type": "postgres",
            "url": "",  
            "tableName": ""
        }
        
        # API endpoint for query execution
        api_url = f"{self.api_base_url}/api/queries/execute"
        logger.info(f"Sending test request to API: {api_url}")
        
        # Prepare the request payload
        payload = {
            "query": test_query,
            "dbConfig": test_config,
            "readOnly": True
        }
        
        # Make the API request with proper headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            # Log the request for debugging
            logger.info(f"Test payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            logger.info(f"Test API response status code: {response.status_code}")
            
            # Log full response for debugging
            logger.info(f"Test API response headers: {dict(response.headers)}")
            logger.info(f"Test API response content (full): {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Test query response data type: {type(data)}")
                logger.info(f"Test query response data: {data}")
                
                if isinstance(data, dict):
                    logger.info(f"Test query response data keys: {list(data.keys())}")
                    
                QMessageBox.information(
                    self,
                    "Test Query Result",
                    f"Test query executed successfully. Check logs for details."
                )
            else:
                error_message = f"API Error ({response.status_code}): {response.text}"
                logger.error(f"Test API error: {error_message}")
                QMessageBox.critical(self, "Test API Error", error_message)
                
        except Exception as e:
            error_message = f"Test Connection Error: {str(e)}"
            logger.error(f"Test connection error: {error_message}", exc_info=True)
            QMessageBox.critical(self, "Test Connection Error", error_message)


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
