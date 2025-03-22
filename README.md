# Query Builder - Qt Python Version

This is a Qt Python implementation of the Query Builder application, providing a desktop interface for building and executing database queries with ease.

## Features

- Support for multiple database types (PostgreSQL, MySQL, MongoDB)
- SQL query editor with syntax highlighting
- Query templates management
- Query history tracking
- Table view for query results
- Read-only mode for safe query execution

## Requirements

- Python 3.8 or higher
- PyQt6
- Requests
- Pandas (for future data visualization)
- Matplotlib (for future chart visualization)

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python main.py
```

## Usage

### Database Connection

1. Select your database type from the dropdown (PostgreSQL, MySQL, or MongoDB)
2. Enter your connection string in the format shown in the placeholder
3. If your query uses table name placeholders (`{table_name}`), enter the table name

### Query Editor

1. Write your SQL query in the editor
2. Use the "Browse Templates" button to select from predefined query templates
3. Toggle "Read-only" mode to prevent modification queries (INSERT, UPDATE, DELETE)
4. Click "Run Query" to execute

### Templates

- Browse existing templates filtered by database type
- Create new templates from your current query
- Edit or delete existing templates

### History

- View your query history
- Filter to show only favorite queries
- Toggle favorite status for queries
- Reuse queries from history

