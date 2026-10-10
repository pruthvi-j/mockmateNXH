"""
NextHire - Database Connection Module
Provides PyMySQL connection management for MySQL 8.x.
"""
import pymysql
from pymysql.cursors import DictCursor
from backend.config import Config

def get_db_connection():
    """
    Establish and return a connection to the NextHire MySQL database.
    Returns a PyMySQL Connection with DictCursor for dictionary-based rows.
    """
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            cursorclass=DictCursor,
            autocommit=True,
            charset="utf8mb4"
        )
        return connection
    except pymysql.MySQLError as err:
        # Provide meaningful error messages for development
        print(f"[Database Error] Connection failed to {Config.DB_NAME}@{Config.DB_HOST}: {err}")
        raise err

def check_db_health():
    """
    Check if the database server is reachable and database exists.
    Returns a dict with status and details.
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 AS alive")
            row = cursor.fetchone()
        conn.close()
        return {"connected": True, "message": "Database is healthy and reachable", "result": row}
    except Exception as e:
        return {"connected": False, "message": str(e)}
