import json
import logging
import os

logger = logging.getLogger("QueryBuilder")

class DbManager:
    def __init__(self):

        self.db_config = {
            "type": "postgres",
            "url": "",
            "tableName": ""
        }
        self.db_type_map = {
            "PostgreSQL": "postgres",
            "MySQL": "mysql",
            "MongoDB": "mongodb"
        }
        self.load_config()
        
    def load_config(self):

        try:
            with open("db_config.json", "r") as f:
                self.db_config = json.load(f)
                logger.info(f"Loaded database configuration: {self.db_config['type']}")
        except FileNotFoundError:
            logger.info("No saved database configuration found, using defaults")
            pass
    
    def save_config(self):
        try:
            with open("db_config.json", "w") as f:
                json.dump(self.db_config, f)
                logger.info("Database configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def update_db_type(self, display_name):
        """
        Update database type based on display name.
        
        Args:
            display_name (str): Display name of the database type
        """
        self.db_config["type"] = self.db_type_map[display_name]
        self.save_config()
        logger.info(f"Database type changed to: {self.db_config['type']}")
    
    def update_table_name(self, table_name):
        """
        Update table name in configuration.
        
        Args:
            table_name (str): Table name
        """
        self.db_config["tableName"] = table_name
        self.save_config()
        logger.info(f"Table name changed to: {self.db_config['tableName']}")
    
    def update_connection_string(self, connection_string):
        """
        Update database connection string.
        
        Args:
            connection_string (str): Connection string
        """
        self.db_config["url"] = connection_string
        self.save_config()
        logger.info("Connection string updated")
    
    def get_connection_placeholder(self):
        """
        Get placeholder text for connection string based on database type.
        
        Returns:
            str: Placeholder text
        """
        db_type = self.db_config["type"]
        if db_type == "postgres":
            return "postgresql://username:password@hostname:5432/database"
        elif db_type == "mysql":
            return "mysql://username:password@hostname:3306/database"
        elif db_type == "mongodb":
            return "mongodb://username:password@hostname:27017/database"
        return "Database connection string"
    
    def get_test_query(self):
        """
        Get a test query for the current database type.
        
        Returns:
            str: Test query
        """
        if self.db_config["type"] == "postgres":
            # Simple query to test PostgreSQL connection
            return "SELECT current_database() as database, current_user as user, version() as version;"
        elif self.db_config["type"] == "mysql":
            return "SELECT database() as database, user() as user, version() as version;"
        elif self.db_config["type"] == "mongodb":
            return "{ find: 'system.version', limit: 1 }"
        else:
            return "-- Please select a database type"
