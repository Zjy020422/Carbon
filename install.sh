#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install --no-cache-dir Flask==3.1.0 flask-cors==5.0.0 numpy==1.26.4 pandas==2.2.0 gunicorn==21.2.0 matplotlib==3.8.3 Pillow==10.2.0

echo "Installing PyTorch CPU version..."
pip install --no-cache-dir torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu

echo "Installation complete!"
