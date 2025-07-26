#!/usr/bin/env python3
"""
Quick Database Fix Script for Minty
This script adds the missing balance field and portfolio table to existing databases.
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def fix_database():
    """Fix the database schema by adding missing fields and tables"""
    
    # XAMPP MySQL configuration
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'minty_db')
    MYSQL_SOCKET = os.getenv('MYSQL_SOCKET', '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock')
    
    try:
        # Connect to XAMPP MySQL using socket
        connection = pymysql.connect(
            unix_socket=MYSQL_SOCKET,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        print(f"Creating database '{MYSQL_DATABASE}' if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        cursor.execute(f"USE {MYSQL_DATABASE}")
        
        # Check if users table exists, if not create it
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            print("Creating users table...")
            cursor.execute("""
                CREATE TABLE users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(512) NOT NULL,
                    balance FLOAT DEFAULT 100000.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            # Check if balance column exists in users table
            cursor.execute("SHOW COLUMNS FROM users LIKE 'balance'")
            if not cursor.fetchone():
                print("Adding balance column to users table...")
                cursor.execute("ALTER TABLE users ADD COLUMN balance FLOAT DEFAULT 100000.0")
                # Update existing users to have the default balance
                cursor.execute("UPDATE users SET balance = 100000.0 WHERE balance IS NULL")
        
        # Check if portfolio table exists
        cursor.execute("SHOW TABLES LIKE 'portfolio'")
        if not cursor.fetchone():
            print("Creating portfolio table...")
            cursor.execute("""
                CREATE TABLE portfolio (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    quantity FLOAT NOT NULL,
                    avg_price FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_user_symbol (user_id, symbol)
                )
            """)
        
        # Check if orders table exists
        cursor.execute("SHOW TABLES LIKE 'orders'")
        if not cursor.fetchone():
            print("Creating orders table...")
            cursor.execute("""
                CREATE TABLE orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    side VARCHAR(4) NOT NULL,
                    qty FLOAT NOT NULL,
                    price FLOAT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    alpaca_order_id VARCHAR(50) NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        
        # Check if profiles table exists
        cursor.execute("SHOW TABLES LIKE 'profiles'")
        if not cursor.fetchone():
            print("Creating profiles table...")
            cursor.execute("""
                CREATE TABLE profiles (
                    user_id INT PRIMARY KEY,
                    preferences TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        
        # Commit changes
        connection.commit()
        
        print("✅ Database schema fixed successfully!")
        print(f"Database: {MYSQL_DATABASE}")
        
        # Show table structure
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # Show users table structure
        cursor.execute("DESCRIBE users")
        columns = cursor.fetchall()
        print(f"Users table columns: {[col[0] for col in columns]}")
        
    except pymysql.Error as e:
        print(f"❌ Error fixing database: {e}")
        return False
    
    finally:
        if connection:
            connection.close()
    
    return True

if __name__ == "__main__":
    print("🔧 Fixing Minty Database Schema...")
    print("=" * 50)
    
    if fix_database():
        print("\n✅ Database is now ready for login and registration!")
        print("You can now:")
        print("1. Start the Flask app: python3 backend/app.py")
        print("2. Test login/registration at: http://localhost:5001")
    else:
        print("\n❌ Failed to fix database. Please check XAMPP MySQL is running.") 