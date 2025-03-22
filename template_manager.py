import json
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QListWidget, QListWidgetItem, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# Default templates similar to the web version
DEFAULT_TEMPLATES = [
    {
        "id": "template_1",
        "name": "Select All Records",
        "description": "Retrieve all records from a table",
        "query": "SELECT * FROM {table_name}",
        "category": "Basic",
        "database_type": "postgres",
        "is_public": True
    },
    {
        "id": "template_2",
        "name": "Count Records",
        "description": "Count the number of records in a table",
        "query": "SELECT COUNT(*) FROM {table_name}",
        "category": "Basic",
        "database_type": "postgres",
        "is_public": True
    },
    {
        "id": "template_3",
        "name": "Find MongoDB Documents",
        "description": "Find documents in a MongoDB collection",
        "query": "{ \"find\": {} }",
        "category": "Basic",
        "database_type": "mongodb",
        "is_public": True
    }
]

class TemplateDialog(QDialog):
    """Dialog for creating or editing a query template"""
    template_saved = pyqtSignal(dict)
    
    def __init__(self, template=None, parent=None):
        super().__init__(parent)
        self.template = template or {
            "id": f"template_{id(self)}",
            "name": "",
            "description": "",
            "query": "",
            "category": "Custom",
            "database_type": "postgres",
            "is_public": False
        }
        
        self.setWindowTitle("Template Editor")
        self.setMinimumWidth(500)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout for template details
        form_layout = QFormLayout()
        
        # Template name
        self.name_input = QLineEdit(self.template.get("name", ""))
        form_layout.addRow("Name:", self.name_input)
        
        # Template description
        self.desc_input = QLineEdit(self.template.get("description", ""))
        form_layout.addRow("Description:", self.desc_input)
        
        # Template category
        self.category_input = QLineEdit(self.template.get("category", "Custom"))
        form_layout.addRow("Category:", self.category_input)
        
        # Query editor
        self.query_editor = QTextEdit()
        self.query_editor.setPlainText(self.template.get("query", ""))
        self.query_editor.setMinimumHeight(200)
        form_layout.addRow("Query:", self.query_editor)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Template")
        save_btn.clicked.connect(self.save_template)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
    def save_template(self):
        # Validate inputs
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Template name is required.")
            return
            
        if not self.query_editor.toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Query is required.")
            return
            
        # Update template with form values
        self.template["name"] = self.name_input.text()
        self.template["description"] = self.desc_input.text()
        self.template["category"] = self.category_input.text()
        self.template["query"] = self.query_editor.toPlainText()
        
        # Emit signal with updated template
        self.template_saved.emit(self.template)
        self.accept()


class TemplateManager:
    """Manages query templates"""
    def __init__(self):
        self.templates_file = "templates.json"
        self.templates = self.load_templates()
        
    def load_templates(self):
        """Load templates from file or use defaults"""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading templates: {e}")
                return DEFAULT_TEMPLATES
        return DEFAULT_TEMPLATES
    
    def save_templates(self):
        """Save templates to file"""
        try:
            with open(self.templates_file, "w") as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            print(f"Error saving templates: {e}")
    
    def add_template(self, template):
        """Add a new template"""
        self.templates.append(template)
        self.save_templates()
    
    def update_template(self, updated_template):
        """Update an existing template"""
        for i, template in enumerate(self.templates):
            if template["id"] == updated_template["id"]:
                self.templates[i] = updated_template
                self.save_templates()
                return True
        return False
    
    def delete_template(self, template_id):
        """Delete a template by ID"""
        self.templates = [t for t in self.templates if t["id"] != template_id]
        self.save_templates()
    
    def get_templates_by_db_type(self, db_type):
        """Get templates filtered by database type"""
        return [t for t in self.templates if t["database_type"] == db_type]


class TemplateManagerDialog(QDialog):
    """Dialog for browsing and managing templates"""
    template_selected = pyqtSignal(dict)
    
    def __init__(self, db_type="postgres", parent=None):
        super().__init__(parent)
        self.db_type = db_type
        self.template_manager = TemplateManager()
        
        self.setWindowTitle("Query Templates")
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_templates()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Query Templates")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Template list
        self.template_list = QListWidget()
        self.template_list.itemDoubleClicked.connect(self.on_template_double_clicked)
        layout.addWidget(self.template_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("New Template")
        self.new_btn.clicked.connect(self.create_template)
        
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_template)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_template)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def load_templates(self):
        """Load templates into the list widget"""
        self.template_list.clear()
        templates = self.template_manager.get_templates_by_db_type(self.db_type)
        
        for template in templates:
            item = QListWidgetItem(template["name"])
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)
    
    def on_template_double_clicked(self, item):
        """Handle double-click on a template item"""
        template = item.data(Qt.ItemDataRole.UserRole)
        self.template_selected.emit(template)
        self.accept()
    
    def create_template(self):
        """Create a new template"""
        new_template = {
            "id": f"template_{id(self)}",
            "name": "",
            "description": "",
            "query": "",
            "category": "Custom",
            "database_type": self.db_type,
            "is_public": False
        }
        
        dialog = TemplateDialog(new_template, self)
        dialog.template_saved.connect(self.on_template_saved)
        dialog.exec()
    
    def edit_template(self):
        """Edit the selected template"""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to edit.")
            return
            
        item = selected_items[0]
        template = item.data(Qt.ItemDataRole.UserRole)
        
        dialog = TemplateDialog(template, self)
        dialog.template_saved.connect(self.on_template_saved)
        dialog.exec()
    
    def delete_template(self):
        """Delete the selected template"""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Selection Required", "Please select a template to delete.")
            return
            
        item = selected_items[0]
        template = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete the template '{template['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.template_manager.delete_template(template["id"])
            self.load_templates()
    
    def on_template_saved(self, template):
        """Handle template save event"""
        # Check if this is a new template or update
        templates = self.template_manager.get_templates_by_db_type(self.db_type)
        existing = next((t for t in templates if t["id"] == template["id"]), None)
        
        if existing:
            self.template_manager.update_template(template)
        else:
            self.template_manager.add_template(template)
            
        self.load_templates()
