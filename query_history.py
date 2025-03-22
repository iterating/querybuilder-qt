import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

class QueryHistoryItem:
    """Represents a single query history item"""
    def __init__(self, query, db_type, timestamp=None, is_favorite=False):
        self.id = f"query_{int(datetime.now().timestamp())}"
        self.query = query
        self.db_type = db_type
        self.timestamp = timestamp or datetime.now().isoformat()
        self.is_favorite = is_favorite
    
    @classmethod
    def from_dict(cls, data):
        """Create a QueryHistoryItem from a dictionary"""
        item = cls(
            query=data.get("query", ""),
            db_type=data.get("db_type", "postgres"),
            timestamp=data.get("timestamp"),
            is_favorite=data.get("is_favorite", False)
        )
        item.id = data.get("id", item.id)
        return item
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "query": self.query,
            "db_type": self.db_type,
            "timestamp": self.timestamp,
            "is_favorite": self.is_favorite
        }
    
    def __str__(self):
        """String representation for display"""
        dt = datetime.fromisoformat(self.timestamp)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        return f"{'★ ' if self.is_favorite else ''}{formatted_time} - {self.query[:50]}{'...' if len(self.query) > 50 else ''}"


class QueryHistoryManager:
    """Manages query history"""
    def __init__(self):
        self.history_file = "query_history.json"
        self.history = self.load_history()
    
    def load_history(self):
        """Load history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    return [QueryHistoryItem.from_dict(item) for item in data]
            except Exception as e:
                print(f"Error loading history: {e}")
                return []
        return []
    
    def save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, "w") as f:
                data = [item.to_dict() for item in self.history]
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_query(self, query, db_type):
        """Add a query to history"""
        # Check if this exact query already exists
        for item in self.history:
            if item.query == query and item.db_type == db_type:
                # Move to top of history
                self.history.remove(item)
                self.history.insert(0, item)
                self.save_history()
                return item
        
        # Add new query
        item = QueryHistoryItem(query, db_type)
        self.history.insert(0, item)
        self.save_history()
        return item
    
    def toggle_favorite(self, query_id):
        """Toggle favorite status of a query"""
        for item in self.history:
            if item.id == query_id:
                item.is_favorite = not item.is_favorite
                self.save_history()
                return item.is_favorite
        return False
    
    def delete_query(self, query_id):
        """Delete a query from history"""
        self.history = [item for item in self.history if item.id != query_id]
        self.save_history()
    
    def get_history(self, filter_favorites=False):
        """Get all history items, optionally filtered to favorites"""
        if filter_favorites:
            return [item for item in self.history if item.is_favorite]
        return self.history


class QueryHistoryDialog(QDialog):
    """Dialog for viewing and managing query history"""
    query_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_manager = QueryHistoryManager()
        
        self.setWindowTitle("Query History")
        self.setMinimumSize(700, 500)
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Query History")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        self.show_all_btn = QPushButton("All Queries")
        self.show_all_btn.setCheckable(True)
        self.show_all_btn.setChecked(True)
        self.show_all_btn.clicked.connect(lambda: self.filter_history(False))
        
        self.show_favorites_btn = QPushButton("Favorites")
        self.show_favorites_btn.setCheckable(True)
        self.show_favorites_btn.clicked.connect(lambda: self.filter_history(True))
        
        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_favorites_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.on_item_clicked)
        self.history_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.history_list)
        
        # Query preview
        preview_label = QLabel("Query Preview:")
        layout.addWidget(preview_label)
        
        self.query_preview = QTextEdit()
        self.query_preview.setReadOnly(True)
        self.query_preview.setMaximumHeight(150)
        layout.addWidget(self.query_preview)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.favorite_btn = QPushButton("Toggle Favorite")
        self.favorite_btn.clicked.connect(self.toggle_favorite)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_query)
        
        self.use_btn = QPushButton("Use Query")
        self.use_btn.clicked.connect(self.use_query)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.favorite_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.use_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_history(self, filter_favorites=False):
        """Load history items into the list widget"""
        self.history_list.clear()
        history_items = self.history_manager.get_history(filter_favorites)
        
        for item in history_items:
            list_item = QListWidgetItem(str(item))
            list_item.setData(Qt.ItemDataRole.UserRole, item.id)
            self.history_list.addItem(list_item)
    
    def filter_history(self, show_favorites):
        """Filter history to show all or only favorites"""
        self.show_all_btn.setChecked(not show_favorites)
        self.show_favorites_btn.setChecked(show_favorites)
        self.load_history(show_favorites)
    
    def on_item_clicked(self, item):
        """Handle click on a history item"""
        query_id = item.data(Qt.ItemDataRole.UserRole)
        history_items = self.history_manager.get_history()
        
        for history_item in history_items:
            if history_item.id == query_id:
                self.query_preview.setPlainText(history_item.query)
                break
    
    def on_item_double_clicked(self, item):
        """Handle double-click on a history item"""
        self.use_query()
    
    def toggle_favorite(self):
        """Toggle favorite status of selected query"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        query_id = item.data(Qt.ItemDataRole.UserRole)
        
        is_favorite = self.history_manager.toggle_favorite(query_id)
        
        # Update the item text
        history_items = self.history_manager.get_history()
        for history_item in history_items:
            if history_item.id == query_id:
                item.setText(str(history_item))
                break
    
    def delete_query(self):
        """Delete selected query from history"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        query_id = item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this query from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history_manager.delete_query(query_id)
            row = self.history_list.row(item)
            self.history_list.takeItem(row)
            self.query_preview.clear()
    
    def use_query(self):
        """Use the selected query"""
        selected_items = self.history_list.selectedItems()
        if not selected_items:
            return
            
        item = selected_items[0]
        query_id = item.data(Qt.ItemDataRole.UserRole)
        
        history_items = self.history_manager.get_history()
        for history_item in history_items:
            if history_item.id == query_id:
                self.query_selected.emit(history_item.query)
                self.accept()
                break
