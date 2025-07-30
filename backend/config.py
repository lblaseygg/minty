import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'mysql')  # 'mysql' or 'postgresql'

if DATABASE_TYPE == 'mysql':
    # MySQL Configuration
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'minty_db')
    MYSQL_SOCKET = os.getenv('MYSQL_SOCKET', None)
    
    # Build connection string with socket support for XAMPP
    if MYSQL_SOCKET and os.path.exists(MYSQL_SOCKET):
        # Use socket connection for XAMPP
        DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@localhost/{MYSQL_DATABASE}?unix_socket={MYSQL_SOCKET}"
    else:
        # Use TCP connection
        DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
else:
    # PostgreSQL Configuration (default)
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'blasey')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '0308')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'postgres')
    
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')

# Alpaca API Configuration
ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
ALPACA_BASE_URL = os.getenv('APCA_API_BASE_URL', 'https://paper-api.alpaca.markets')

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true' 