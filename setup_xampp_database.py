#!/usr/bin/env python3
"""
XAMPP MySQL Database Setup Script for Minty
This script helps set up the MySQL database for the Minty application using XAMPP.
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create the database and tables using XAMPP MySQL"""
    
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
        print("\n🔧 Troubleshooting:")
        print("1. Make sure XAMPP is running")
        print("2. Start MySQL in XAMPP Control Panel")
        print("3. Check if the socket file exists:")
        print(f"   ls -la {MYSQL_SOCKET}")
        return False
    
    finally:
        if connection:
            connection.close()
    
    return True

def create_sample_data():
    """Create sample data for testing"""
    
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'minty_db')
    MYSQL_SOCKET = os.getenv('MYSQL_SOCKET', '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock')
    
    try:
        connection = pymysql.connect(
            unix_socket=MYSQL_SOCKET,
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

def check_xampp_status():
    """Check if XAMPP MySQL is running"""
    import subprocess
    
    print("🔍 Checking XAMPP MySQL status...")
    
    # Check if XAMPP MySQL socket exists
    socket_path = '/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock'
    if os.path.exists(socket_path):
        print(f"✅ MySQL socket found: {socket_path}")
    else:
        print(f"❌ MySQL socket not found: {socket_path}")
        print("Please start MySQL in XAMPP Control Panel")
        return False
    
    # Check if port 3306 is listening
    try:
        result = subprocess.run(['lsof', '-i', ':3306'], capture_output=True, text=True)
        if result.stdout:
            print("✅ MySQL is listening on port 3306")
        else:
            print("⚠️  MySQL is not listening on port 3306 (this might be normal for socket connection)")
    except Exception as e:
        print(f"⚠️  Could not check port 3306: {e}")
    
    return True

if __name__ == "__main__":
    print("🚀 Setting up Minty Database with XAMPP MySQL...")
    print("=" * 60)
    
    # Check XAMPP status first
    if not check_xampp_status():
        print("\n❌ Please start XAMPP MySQL before running this script")
        print("1. Open XAMPP Control Panel")
        print("2. Click 'Start' next to MySQL")
        print("3. Run this script again")
        exit(1)
    
    # Create database and tables
    if create_database():
        # Ask if user wants to create sample data
        response = input("\nWould you like to create sample data? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            create_sample_data()
    
    print("\n📝 Next steps:")
    print("1. Your .env file is already configured for XAMPP")
    print("2. Install MySQL dependencies: pip install pymysql cryptography")
    print("3. Run the Flask application: python3 run_app.py")
    print("4. Test the signup page: http://localhost:5001/register.html") 