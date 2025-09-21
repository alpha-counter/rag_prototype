import logging
import psycopg2
from psycopg2 import sql

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_if_not_exists(DATABASE_URL, dbname):
    # Correcting the connection string to be compatible with psycopg2
    DATABASE_URL = DATABASE_URL.replace('postgresql+psycopg2', 'postgresql')
    
    try:
        # Connect to the existing database using connection string URL
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        # Check if the target database exists
        cur.execute(
            sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"),
            [dbname]
        )

        exists = cur.fetchone()
        if not exists:
            # Create the target database if it does not exist
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            logger.info(f" Database '{dbname}' created successfully.")
        else:
            logger.info(f" Database '{dbname}' already exists.")

        # Close communication with the PostgreSQL database server
        cur.close()
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.info(f"Error: {error}")