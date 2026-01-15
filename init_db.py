import mysql.connector
from scrapy.utils.project import get_project_settings
import sys
import os

def init_db():
    # Use default settings or hardcoded for init
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': 'root',
        'password': 'root', # Matches docker-compose
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS bid_data DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("Database 'bid_data' created or exists.")
        
        conn.database = 'bid_data'
        
        # Create tables from schema.sql
        with open('schema.sql', 'r') as f:
            sql_script = f.read()
            
        # Split by ;
        commands = sql_script.split(';')
        for cmd in commands:
            if cmd.strip():
                cursor.execute(cmd)
        
        print("Tables created.")
        
        conn.close()
    except mysql.connector.Error as err:
        print(f"Error initializing DB: {err}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()
