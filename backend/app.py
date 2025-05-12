import os
from flask import Flask
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables from .env file - important for local development
load_dotenv()

# Import the blueprint from app.main
# Ensure app/main.py exists and defines main_bp
try:
    from app.main import main_bp
    print("Successfully imported main_bp from app.main")
except ImportError as e:
    print(f"FATAL ERROR: Could not import main_bp from app.main: {e}")
    # Decide how to handle this - maybe raise the error?
    raise e # Or sys.exit(1) after import sys


app = Flask(__name__)

# Apply CORS settings
# Allow requests from frontend origin (adjust port if your React app uses a different one locally)
# For deployment, you might restrict origins more specifically or use '*' for simplicity if security is not paramount
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "YOUR_DEPLOYED_FRONTEND_URL"]}}) # Replace YOUR_DEPLOYED_FRONTEND_URL or use "*"

# Register the blueprint that contains our robotics route
if main_bp:
    app.register_blueprint(main_bp)
    print("Registered main_bp blueprint.")
else:
    # This case shouldn't be reached if the import check above is strict
    print("Blueprint registration skipped as main_bp failed to import.")

# Basic root route for health check (optional but good practice)
@app.route('/')
def hello():
    return "Robotics Advisor Backend is running."

# Note: The entrypoint in app.yaml uses Gunicorn, so this __main__ block
# is mainly for direct local execution (python app.py)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=True)