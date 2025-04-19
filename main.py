# Import the Flask app from app.py
from app import app

# This is a minimal main.py that imports the app from app.py
# Replit will use this file to run the application

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
