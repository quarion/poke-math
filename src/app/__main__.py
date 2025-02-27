"""
Main entry point for running the PokeMath application.

This allows the app to be run with 'python -m src.app'.
"""

import os
from src.app.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development") 