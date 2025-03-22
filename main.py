import sys
import pathlib
from PyQt6.QtWidgets import QApplication

# Add the src directory to the path to make imports work
sys.path.insert(0, str(pathlib.Path(__file__).parent / "src"))

# Import logger first to set up logging
from src.logger import setup_logging
# Create logger
logger = setup_logging()

# Import the main application class
from src.app import QueryBuilder


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
