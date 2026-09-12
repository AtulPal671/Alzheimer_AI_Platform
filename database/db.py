"""
Database Utility Module for NeuroScan AI Platform

Provides parameterized MySQL connection management, query execution,
and schema initialization helpers using PyMySQL and python-dotenv.
"""

import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

# Load environment configuration from .env file
load_dotenv()

class DatabaseConnectionError(Exception):
    """Custom exception raised when MySQL connection fails."""
    pass

def get_db_credentials():
    """Retrieve MySQL configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'alzheimer_ai'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True
    }

def get_db_connection(include_db=True):
    """
    Establishes and returns a PyMySQL database connection.
    
    :param include_db: If True, connects directly to DB_NAME. If False, connects to MySQL server without selecting a DB.
    """
    creds = get_db_credentials()
    if not include_db:
        creds.pop('database', None)

    try:
        connection = pymysql.connect(**creds)
        return connection
    except pymysql.MySQLError as e:
        raise DatabaseConnectionError(f"Failed to connect to MySQL database at {creds['host']}:{creds['port']} - Error: {e}")

def query_one(sql, params=None):
    """
    Executes a parameterized SELECT query and returns a single row dictionary.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        conn.close()

def query_all(sql, params=None):
    """
    Executes a parameterized SELECT query and returns all matching row dictionaries.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()

def execute_db(sql, params=None):
    """
    Executes a parameterized INSERT, UPDATE, or DELETE statement.
    Returns the inserted row ID (if applicable) or affected row count.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.lastrowid
    finally:
        conn.close()

def check_db_health():
    """
    Utility function to verify if MySQL database connection is operational.
    """
    try:
        result = query_one("SELECT 1 AS status")
        return result and result.get('status') == 1
    except Exception as e:
        print(f"[DB HEALTH CHECK WARNING] {e}")
        return False
