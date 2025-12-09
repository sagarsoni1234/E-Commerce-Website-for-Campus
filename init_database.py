"""
Standalone database initialization script
Run this if tables are not being created automatically
"""

from app import init_db, get_db_connection
import mysql.connector
from mysql.connector import Error

if __name__ == '__main__':
    print("=" * 50)
    print("Campus Marketplace - Database Initialization")
    print("=" * 50)
    print()
    
    # Test connection first
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=''
        )
        print("[OK] MySQL connection successful")
        conn.close()
    except Error as e:
        print(f"[ERROR] Cannot connect to MySQL: {e}")
        print("\nPlease ensure:")
        print("  1. MySQL is running (XAMPP or standalone)")
        print("  2. MySQL credentials are correct")
        exit(1)
    
    print()
    print("Initializing database and tables...")
    print()
    
    # Initialize database
    init_db()
    
    # Verify tables were created
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print()
        print("=" * 50)
        print("Database Initialization Complete!")
        print("=" * 50)
        print(f"\nTables created: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        print()
        print("You can now run: python app.py")
    else:
        print("[ERROR] Could not verify tables")

