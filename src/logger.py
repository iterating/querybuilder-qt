import sys
import logging
import pathlib
from datetime import datetime

def setup_logging():
    """
    Configure and set up logging for the application.
    
    Returns:
        logging.Logger: Configured logger instance
    """
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
