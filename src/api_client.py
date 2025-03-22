import json
import requests
import logging

logger = logging.getLogger("QueryBuilder")

class ApiClient:
    def __init__(self, api_base_url):
        """
        Initialize the API client.
        
        Args:
            api_base_url (str): Base URL for the API
        """
        self.api_base_url = api_base_url
        logger.info(f"API client initialized with base URL: {api_base_url}")
    
    def execute_query(self, query, db_config, read_only=True):
        """
        Execute a database query via the API.
        
        Args:
            query (str): The query to execute
            db_config (dict): Database configuration
            read_only (bool): Whether the query is read-only
            
        Returns:
            dict: Query results
            
        Raises:
            requests.RequestException: If there's a connection error
            Exception: For other errors
        """
        try:
            # Process query for PostgreSQL table name substitution
            processed_query = query
            if db_config["type"] == "postgres" and "{table_name}" in query:
                # PostgreSQL doesn't support curly brace syntax directly
                # Replace {table_name} with properly quoted table name
                table_name = db_config.get("tableName", "")
                processed_query = query.replace("{table_name}", f'"{table_name}"')
                logger.info(f"Processed PostgreSQL query with table name substitution: {table_name}")
            
            # API endpoint for query execution
            api_url = f"{self.api_base_url}/api/queries/execute"
            logger.info(f"Sending request to API: {api_url}")
            
            # Prepare the database configuration to send
            config_to_send = db_config.copy()
            
            # Prepare the request payload
            payload = {
                "query": processed_query,
                "dbConfig": config_to_send,
                "readOnly": read_only
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
                return data
            else:
                error_message = f"API Error ({response.status_code}): {response.text}"
                logger.error(f"API error: {error_message}")
                raise Exception(error_message)
                
        except requests.RequestException as e:
            error_message = f"Connection Error: {str(e)}"
            logger.error(f"Connection error: {error_message}", exc_info=True)
            raise
    
    def run_test_query(self):
        """
        Run a test query to troubleshoot API responses.
        
        Returns:
            dict: Test query results
            
        Raises:
            Exception: If there's an error executing the test query
        """
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
                    
                return data
            else:
                error_message = f"API Error ({response.status_code}): {response.text}"
                logger.error(f"Test API error: {error_message}")
                raise Exception(error_message)
                
        except Exception as e:
            error_message = f"Test Connection Error: {str(e)}"
            logger.error(f"Test connection error: {error_message}", exc_info=True)
            raise
