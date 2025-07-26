# 🚀 XAMPP MySQL Setup Guide for Minty

## Connecting Your XAMPP MySQL Database to Minty

### ✅ **What's Been Configured**

1. **Updated `.env` file** with XAMPP MySQL settings
2. **Modified `backend/config.py`** to support XAMPP socket connection
3. **Updated `backend/app.py`** to use the new configuration
4. **Created `setup_xampp_database.py`** for easy database setup

### 🔧 **Step-by-Step Setup**

#### **Step 1: Start XAMPP MySQL**
1. Open XAMPP Control Panel
2. Click "Start" next to MySQL
3. Wait for MySQL to start (green status)

#### **Step 2: Install Python Dependencies**
```bash
cd /Users/blasey/Developer/minty
pip3 install pymysql cryptography
```

#### **Step 3: Set Up the Database**
```bash
# Run the XAMPP-specific setup script
python3 setup_xampp_database.py
```

This script will:
- ✅ Check if XAMPP MySQL is running
- ✅ Create the `minty_db` database
- ✅ Create all required tables (users, orders, profiles)
- ✅ Set up indexes for performance
- ✅ Optionally create sample data

#### **Step 4: Start the Application**
```bash
# Use the helper script to run the Flask app
python3 run_app.py
```

#### **Step 5: Test the Signup Page**
- Navigate to: `http://localhost:5001/register.html`
- Create a new account to test the database connection

### 🗄️ **Database Configuration**

Your `.env` file is now configured for XAMPP:

```env
# Database Configuration
DATABASE_TYPE=mysql

# XAMPP MySQL Configuration
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=minty_db
MYSQL_SOCKET=/Applications/XAMPP/xamppfiles/var/mysql/mysql.sock
```

### 🔍 **Troubleshooting**

#### **Issue: "Can't connect to local MySQL server"**
```bash
# Check if XAMPP MySQL is running
ls -la /Applications/XAMPP/xamppfiles/var/mysql/mysql.sock

# If the socket doesn't exist, start MySQL in XAMPP Control Panel
```

#### **Issue: "Access denied"**
```bash
# Connect to XAMPP MySQL directly
/Applications/XAMPP/xamppfiles/bin/mysql -u root -p

# If no password is set, just press Enter
# If you have a password, enter it
```

#### **Issue: "Module not found: pymysql"**
```bash
# Install the required packages
pip3 install pymysql cryptography
```

#### **Issue: "Database doesn't exist"**
```bash
# Run the setup script
python3 setup_xampp_database.py
```

### 📊 **Database Schema**

The setup creates these tables:

```sql
-- Users table (for authentication)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table (for trading history)
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
);

-- Profiles table (for user preferences)
CREATE TABLE profiles (
    user_id INT PRIMARY KEY,
    preferences TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 🧪 **Testing the Connection**

#### **1. Test Database Setup**
```bash
python3 setup_xampp_database.py
```

#### **2. Test Flask Application**
```bash
python3 run_app.py
```

#### **3. Test User Registration**
- Go to `http://localhost:5001/register.html`
- Create a new account
- Check if the user appears in the database

#### **4. Test User Login**
- Go to `http://localhost:5001/login.html`
- Login with the account you just created

### 🔐 **Security Features**

- ✅ **Password Hashing**: All passwords are securely hashed
- ✅ **JWT Authentication**: Secure session management
- ✅ **Input Validation**: Both client and server-side validation
- ✅ **SQL Injection Protection**: Using parameterized queries
- ✅ **CORS Configuration**: Proper cross-origin settings

### 📱 **User Flow**

```
User visits register.html
         ↓
   Fills out signup form
         ↓
   Client-side validation
         ↓
   API call to /auth/register
         ↓
   Server creates user in XAMPP MySQL
         ↓
   JWT token returned
         ↓
   User automatically logged in
         ↓
   Redirected to dashboard
```

### 🎯 **Next Steps**

After successful setup, you can:

1. **Create multiple user accounts** for testing
2. **Test the portfolio functionality** with different users
3. **Add more features** like email verification
4. **Deploy to production** with proper security settings

### 🚨 **Important Notes**

1. **XAMPP MySQL**: Make sure MySQL is running in XAMPP Control Panel
2. **Socket Connection**: The app uses Unix socket for better performance
3. **No Password**: Default XAMPP MySQL has no root password
4. **Port 5001**: Flask app runs on port 5001, not 5000
5. **CORS**: Backend allows requests from localhost:5001

---

**Ready to test?** Start XAMPP MySQL and run `python3 setup_xampp_database.py`! 🚀 