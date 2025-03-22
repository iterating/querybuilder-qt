import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QApplication
)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt6agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd


class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding charts in Qt"""
    def __init__(self, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.fig.tight_layout()


class DataVisualizer(QWidget):
    """Widget for visualizing query results as tables and charts"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.df = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.view_selector = QComboBox()
        self.view_selector.addItems(["Table View", "Chart View"])
        self.view_selector.currentIndexChanged.connect(self.on_view_changed)
        
        self.row_count_label = QLabel("0 rows")
        
        controls_layout.addWidget(QLabel("View:"))
        controls_layout.addWidget(self.view_selector)
        controls_layout.addStretch()
        controls_layout.addWidget(self.row_count_label)
        
        layout.addLayout(controls_layout)
        
        # Tab widget for different views
        self.tabs = QTabWidget()
        
        # Table view
        self.table_view = QTableWidget()
        self.tabs.addTab(self.table_view, "Table")
        
        # Chart view
        self.chart_widget = QWidget()
        chart_layout = QVBoxLayout(self.chart_widget)
        
        # Chart type selector
        chart_controls = QHBoxLayout()
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart"])
        self.chart_type.currentIndexChanged.connect(self.update_chart)
        
        self.x_axis = QComboBox()
        self.y_axis = QComboBox()
        self.x_axis.currentIndexChanged.connect(self.update_chart)
        self.y_axis.currentIndexChanged.connect(self.update_chart)
        
        chart_controls.addWidget(QLabel("Chart Type:"))
        chart_controls.addWidget(self.chart_type)
        chart_controls.addWidget(QLabel("X Axis:"))
        chart_controls.addWidget(self.x_axis)
        chart_controls.addWidget(QLabel("Y Axis:"))
        chart_controls.addWidget(self.y_axis)
        
        chart_layout.addLayout(chart_controls)
        
        # Matplotlib canvas
        self.canvas = MplCanvas(width=5, height=4, dpi=100)
        chart_layout.addWidget(self.canvas)
        
        self.tabs.addTab(self.chart_widget, "Chart")
        
        layout.addWidget(self.tabs)
        
        # Initially hide chart view until we have numeric data
        self.tabs.setTabEnabled(1, False)
        
    def on_view_changed(self, index):
        """Handle view selector change"""
        self.tabs.setCurrentIndex(index)
        
    def set_data(self, data):
        """Set the data to visualize"""
        self.data = data
        
        if not data or not isinstance(data, list) or len(data) == 0:
            self.clear_views()
            self.row_count_label.setText("0 rows")
            return
            
        # Update row count
        self.row_count_label.setText(f"{len(data)} rows")
        
        # Convert to pandas DataFrame for easier manipulation
        self.df = pd.DataFrame(data)
        
        # Update table view
        self.update_table()
        
        # Check if we have numeric columns for charts
        numeric_columns = self.df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_columns) > 0:
            self.tabs.setTabEnabled(1, True)
            
            # Update axis selectors
            self.update_axis_selectors()
            
            # Update chart
            self.update_chart()
        else:
            self.tabs.setTabEnabled(1, False)
            
    def clear_views(self):
        """Clear all views"""
        # Clear table
        self.table_view.clear()
        self.table_view.setRowCount(0)
        self.table_view.setColumnCount(0)
        
        # Clear chart
        self.canvas.axes.clear()
        self.canvas.draw()
        
        # Clear axis selectors
        self.x_axis.clear()
        self.y_axis.clear()
        
    def update_table(self):
        """Update the table view with current data"""
        if self.df is None or self.df.empty:
            self.clear_views()
            return
            
        # Get headers
        headers = self.df.columns.tolist()
        
        # Set up table
        self.table_view.setRowCount(len(self.df))
        self.table_view.setColumnCount(len(headers))
        self.table_view.setHorizontalHeaderLabels(headers)
        
        # Populate table
        for row_idx, (_, row) in enumerate(self.df.iterrows()):
            for col_idx, header in enumerate(headers):
                value = row[header]
                # Convert to string for display
                if value is None:
                    display_value = ""
                else:
                    display_value = str(value)
                    
                item = QTableWidgetItem(display_value)
                self.table_view.setItem(row_idx, col_idx, item)
                
        # Resize columns to content
        self.table_view.resizeColumnsToContents()
        
    def update_axis_selectors(self):
        """Update the axis selectors with available columns"""
        if self.df is None:
            return
            
        # Save current selections if possible
        current_x = self.x_axis.currentText() if self.x_axis.count() > 0 else ""
        current_y = self.y_axis.currentText() if self.y_axis.count() > 0 else ""
        
        # Clear selectors
        self.x_axis.clear()
        self.y_axis.clear()
        
        # All columns for X axis
        all_columns = self.df.columns.tolist()
        self.x_axis.addItems(all_columns)
        
        # Only numeric columns for Y axis
        numeric_columns = self.df.select_dtypes(include=['number']).columns.tolist()
        self.y_axis.addItems(numeric_columns)
        
        # Restore selections if possible
        if current_x in all_columns:
            self.x_axis.setCurrentText(current_x)
        
        if current_y in numeric_columns:
            self.y_axis.setCurrentText(current_y)
        elif numeric_columns:
            self.y_axis.setCurrentText(numeric_columns[0])
            
    def update_chart(self):
        """Update the chart with current data and settings"""
        if self.df is None or self.df.empty:
            return
            
        if self.y_axis.count() == 0:
            # No numeric columns available
            return
            
        # Get current settings
        chart_type = self.chart_type.currentText()
        x_column = self.x_axis.currentText()
        y_column = self.y_axis.currentText()
        
        if not x_column or not y_column:
            return
            
        # Clear previous chart
        self.canvas.axes.clear()
        
        # Create chart based on type
        if chart_type == "Bar Chart":
            self.df.plot(
                kind='bar', 
                x=x_column, 
                y=y_column, 
                ax=self.canvas.axes,
                legend=True
            )
        elif chart_type == "Line Chart":
            self.df.plot(
                kind='line', 
                x=x_column, 
                y=y_column, 
                ax=self.canvas.axes,
                legend=True
            )
        elif chart_type == "Scatter Plot":
            self.df.plot(
                kind='scatter', 
                x=x_column, 
                y=y_column, 
                ax=self.canvas.axes,
                legend=True
            )
        elif chart_type == "Pie Chart":
            # For pie charts, we need to ensure values are positive
            if (self.df[y_column] >= 0).all():
                self.df.plot(
                    kind='pie',
                    y=y_column,
                    labels=self.df[x_column],
                    ax=self.canvas.axes,
                    legend=False,
                    autopct='%1.1f%%'
                )
            else:
                self.canvas.axes.text(
                    0.5, 0.5, 
                    "Cannot create pie chart with negative values",
                    horizontalalignment='center',
                    verticalalignment='center'
                )
        
        # Set title and labels
        self.canvas.axes.set_title(f"{y_column} by {x_column}")
        if chart_type != "Pie Chart":
            self.canvas.axes.set_xlabel(x_column)
            self.canvas.axes.set_ylabel(y_column)
        
        # Adjust layout and redraw
        self.canvas.fig.tight_layout()
        self.canvas.draw()


# Test the component if run directly
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Sample data
    sample_data = [
        {"id": 1, "name": "Product A", "value": 100, "quantity": 5},
        {"id": 2, "name": "Product B", "value": 200, "quantity": 3},
        {"id": 3, "name": "Product C", "value": 150, "quantity": 7},
        {"id": 4, "name": "Product D", "value": 300, "quantity": 2},
        {"id": 5, "name": "Product E", "value": 250, "quantity": 4}
    ]
    
    widget = DataVisualizer()
    widget.set_data(sample_data)
    widget.show()
    
    sys.exit(app.exec())
