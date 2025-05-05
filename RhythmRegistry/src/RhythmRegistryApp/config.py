# Database Configuration
import os
import re
from urllib.parse import urlparse

# Check if DATABASE_URL is provided (common in deployment platforms like Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    # Parse the DATABASE_URL
    result = urlparse(DATABASE_URL)
    
    # Extract connection details from the parsed URL
    DB_USER = result.username
    DB_PASSWORD = result.password
    DB_HOST = result.hostname
    DB_PORT = str(result.port) if result.port else '5432'
    DB_NAME = result.path[1:]  # Remove the leading slash
else:
    # Get database connection details from individual environment variables with fallbacks
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'rhythm_registry')
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')

# Secret key for session
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-change-in-production')