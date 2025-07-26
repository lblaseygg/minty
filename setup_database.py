#!/usr/bin/env python3
"""
Database Setup Script for Minty
This script helps set up the MySQL database for the Minty application.
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create the database and tables"""
    
    # Database configuration
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'minty_db')
    
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        print(f"Creating database '{MYSQL_DATABASE}' if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        cursor.execute(f"USE {MYSQL_DATABASE}")
        
        # Create tables
        print("Creating tables...")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(512) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
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
        
        # Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INT PRIMARY KEY,
                preferences TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        
        # Commit changes
        connection.commit()
        
        print("✅ Database setup completed successfully!")
        print(f"Database: {MYSQL_DATABASE}")
        print("Tables created: users, orders, profiles")
        
        # Show table structure
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
    except pymysql.Error as e:
        print(f"❌ Error setting up database: {e}")
        return False
    
    finally:
        if connection:
            connection.close()
    
    return True

def create_sample_data():
    """Create sample data for testing"""
    
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'minty_db')
    
    try:
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Check if sample user already exists
        cursor.execute("SELECT id FROM users WHERE email = 'test4@example.com'")
        if cursor.fetchone():
            print("Sample user already exists, skipping sample data creation.")
            return True
        
        # Create sample user
        print("Creating sample user...")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash) VALUES 
            ('testuser', 'test4@example.com', 'pbkdf2:sha256:600000$sample_hash_here')
        """)
        
        user_id = cursor.lastrowid
        
        # Create sample orders
        print("Creating sample orders...")
        sample_orders = [
            (user_id, 'NVDA', 'buy', 10.0, 150.50, 'completed', None),
            (user_id, 'AMD', 'buy', 5.0, 120.25, 'completed', None),
            (user_id, 'AAPL', 'sell', 2.0, 180.75, 'completed', None),
            (user_id, 'GOOGL', 'buy', 3.0, 2800.00, 'completed', None)
        ]
        
        cursor.executemany("""
            INSERT INTO orders (user_id, symbol, side, qty, price, status, alpaca_order_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, sample_orders)
        
        # Create sample profile
        print("Creating sample profile...")
        cursor.execute("""
            INSERT INTO profiles (user_id, preferences) VALUES 
            (%s, '{"risk_tolerance": "moderate", "investment_goals": ["growth", "income"], "preferred_sectors": ["technology", "healthcare"]}')
        """, (user_id,))
        
        connection.commit()
        print("✅ Sample data created successfully!")
        
    except pymysql.Error as e:
        print(f"❌ Error creating sample data: {e}")
        return False
    
    finally:
        if connection:
            connection.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Minty Database...")
    print("=" * 50)
    
    # Create database and tables
    if create_database():
        # Ask if user wants to create sample data
        response = input("\nWould you like to create sample data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            create_sample_data()
    
    print("\n📝 Next steps:")
    print("1. Update your .env file with MySQL credentials")
    print("2. Set DATABASE_TYPE=mysql in your .env file")
    print("3. Install MySQL dependencies: pip install pymysql cryptography")
    print("4. Run the Flask application: python app.py") 