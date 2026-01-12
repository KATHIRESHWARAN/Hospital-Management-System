"""
Vercel serverless function entry point for Hospital Management System.
Routes all requests to the Flask app.
"""

import sys
import os

# Add the parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app
from app import app as flask_app

# WSGI application for Vercel
app = flask_app

# Health check endpoint
@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "Hospital Management System API"}

# For Vercel
if __name__ == "__main__":
    pass
