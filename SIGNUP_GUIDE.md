# 🚀 Minty Signup Guide

## New User Registration System

### ✅ **What's New**

1. **Signup Page** (`register.html`)
   - Clean, modern design matching the login page
   - Form validation for all fields
   - Password strength requirements
   - Real-time password confirmation validation

2. **Registration JavaScript** (`register.js`)
   - Client-side form validation
   - API integration with backend
   - Error handling and user feedback
   - Automatic redirect after successful registration

### 📋 **Registration Fields**

| Field | Requirements | Validation |
|-------|-------------|------------|
| **Username** | 3-50 characters | Unique, alphanumeric |
| **Email** | Valid email format | Unique, required |
| **Password** | Min 6 characters | Must contain uppercase, lowercase, number |
| **Confirm Password** | Must match password | Real-time validation |

### 🔐 **Security Features**

- ✅ **Password Hashing**: Passwords are securely hashed using Werkzeug
- ✅ **JWT Tokens**: Secure authentication tokens
- ✅ **Form Validation**: Both client and server-side validation
- ✅ **Duplicate Prevention**: Unique usernames and emails
- ✅ **Password Strength**: Enforced password requirements

### 🚀 **How to Use**

#### **1. Start the Application**
```bash
# From the project root directory
python3 run_app.py
```

#### **2. Access the Signup Page**
- Navigate to: `http://localhost:5001/register.html`
- Or click "Create account" from the login page

#### **3. Create a New Account**
1. Enter a unique username (3-50 characters)
2. Enter a valid email address
3. Create a strong password (min 6 chars, uppercase, lowercase, number)
4. Confirm your password
5. Click "Create Account"

#### **4. Automatic Login**
- After successful registration, you'll be automatically logged in
- Redirected to the main dashboard
- Your session is maintained with JWT tokens

### 🗄️ **Database Integration**

The registration system integrates with your MySQL database:

```sql
-- Users table stores all new registrations
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 🔧 **Backend API Endpoint**

The registration uses the existing `/auth/register` endpoint:

```python
@app.route('/auth/register', methods=['POST'])
def register():
    # Validates input
    # Checks for duplicate username/email
    # Hashes password securely
    # Creates user in database
    # Returns JWT token
```

### 🎨 **Design Features**

- **Consistent Styling**: Matches the existing login page design
- **Responsive Design**: Works on desktop and mobile
- **Loading States**: Visual feedback during registration
- **Error Messages**: Clear, user-friendly error handling
- **Success Feedback**: Confirmation messages and auto-redirect

### 🧪 **Testing the Signup**

1. **Valid Registration**:
   - Username: `testuser123`
   - Email: `test@example.com`
   - Password: `Password123`
   - Confirm: `Password123`

2. **Test Error Cases**:
   - Duplicate username/email
   - Weak password
   - Mismatched passwords
   - Invalid email format

### 🔄 **User Flow**

```
User visits register.html
         ↓
    Fills out form
         ↓
   Client validation
         ↓
   API call to /auth/register
         ↓
   Server validation & user creation
         ↓
   JWT token returned
         ↓
   User logged in & redirected to dashboard
```

### 🛠️ **Customization Options**

You can easily customize:

- **Password Requirements**: Modify the regex in `register.js`
- **Username Rules**: Change validation in the backend
- **Email Domains**: Add domain restrictions
- **Redirect Behavior**: Change where users go after registration
- **UI/UX**: Modify the CSS styling

### 🚨 **Important Notes**

1. **Database Setup**: Make sure your MySQL database is running
2. **Environment Variables**: Configure your `.env` file properly
3. **CORS**: The backend already has CORS enabled for localhost
4. **Port**: The Flask app runs on port 5001

### 🎯 **Next Steps**

After implementing signup, you might want to add:

- Email verification
- Username availability checking
- Password reset functionality
- Social login options
- Profile completion flow

---

**Ready to test?** Run `python3 run_app.py` and visit `http://localhost:5001/register.html`! 🚀 