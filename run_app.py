#!/usr/bin/env python3
"""
Simple script to run the Minty Flask application
"""

import os
import sys
import subprocess

def main():
    # Change to the backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found!")
        print("Make sure you're in the correct project directory.")
        return
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Check if app.py exists
    if not os.path.exists('app.py'):
        print("❌ app.py not found in backend directory!")
        return
    
    print("🚀 Starting Minty Flask Application...")
    print(f"📁 Working directory: {os.getcwd()}")
    print("🌐 Server will be available at: http://localhost:5001")
    print("=" * 50)
    
    try:
        # Run the Flask app
        subprocess.run([sys.executable, 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

if __name__ == "__main__":
    main() 