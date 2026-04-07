#!/bin/bash
# Construction Management System — startup script

echo "Installing dependencies..."
pip install -r requirements.txt --break-system-packages -q

echo "Starting CMS on http://localhost:5001"
python app.py
