import os
import sys
import getpass
import subprocess
from pathlib import Path
import random
import string

# Clear the screen
os.system('cls') 

print("\n" + "=" * 60)
print("RHYTHM REGISTRY - DATABASE SETUP".center(60))
print("=" * 60 + "\n")
print("Welcome to the RhythmRegistry Database Setup!")
print("This script will help you set up your PostgreSQL database.\n")

# Check if PostgreSQL is installed
try:
    subprocess.run(["psql", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except FileNotFoundError:
    print("ERROR: PostgreSQL is not installed or not in your PATH.")
    print("Please install PostgreSQL and make sure the 'psql' command is available.")
    sys.exit(1)

# Get database connection details
print("Please provide your PostgreSQL connection details.\nYou can press Enter to use the default values shown in brackets.\n")
host = input("Database Host [localhost]: ").strip() or "localhost"
port = input("Database Port [5432]: ").strip() or "5432"
username = input("Database Username [postgres]: ").strip() or "postgres"
password = getpass.getpass("Database Password: ") # Hide password input
db_name = input("Database Name [rhythm_registry]: ").strip() or "rhythm_registry"

# Store details in a dictionary for easy access
db_details = {
    "host": host,
    "port": port,
    "username": username,
    "password": password,
    "db_name": db_name
}

# Test the connection
print("\nTesting database connection...")
env = os.environ.copy() 
env["PGPASSWORD"] = password

try:
    cmd = ["psql", "-c", "SELECT 1", "-d", "postgres", 
           "-h", host, "-p", port, "-U", username]
    
    result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode == 0:
        print("Connection successful!")
    else:
        print(f"Connection failed: {result.stderr.decode()}")
        print("Setup aborted. Please check your PostgreSQL installation and credentials.")
        sys.exit(1)
except Exception as e:
    print(f"Error testing connection: {str(e)}")
    print("Setup aborted. Please check your PostgreSQL installation and credentials.")
    sys.exit(1)

# Create the database
print(f"\nCreating database '{db_name}'...")

try:
    # Check if database exists
    check_cmd = ["psql", "-h", host, "-p", port, 
                "-U", username, "-d", "postgres", 
                "-t", "-c", f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"]
    
    check_result = subprocess.run(check_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if check_result.stdout.strip():
        print(f"Database '{db_name}' already exists.")
        recreate = input("Do you want to drop and recreate the database? (y/N): ").lower() == 'y'
        if recreate:
            # Drop database
            drop_cmd = ["psql", "-h", host, "-p", port, 
                       "-U", username, "-d", "postgres", 
                       "-c", f"DROP DATABASE {db_name}"]
            
            subprocess.run(drop_cmd, env=env, check=True)
            print(f"Database '{db_name}' dropped.")
            
            # Create database
            create_cmd = ["psql", "-h", host, "-p", port, 
                         "-U", username, "-d", "postgres", 
                         "-c", f"CREATE DATABASE {db_name}"]
            
            subprocess.run(create_cmd, env=env, check=True)
            print(f"Database '{db_name}' created successfully.")
    else:
        # Create database
        create_cmd = ["psql", "-h", host, "-p", port, 
                     "-U", username, "-d", "postgres", 
                     "-c", f"CREATE DATABASE {db_name}"]
        
        subprocess.run(create_cmd, env=env, check=True)
        print(f"Database '{db_name}' created successfully.")
except Exception as e:
    print(f"Error creating database: {str(e)}")
    sys.exit(1)

# Create tables
print("\nCreating tables...")

# SQL script with our table definitions
sql_script = """
-- Create role table
CREATE TABLE IF NOT EXISTS role (
    id SERIAL PRIMARY KEY,
    role VARCHAR(100) NOT NULL
);

-- Create portrait table
CREATE TABLE IF NOT EXISTS portrait (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    main_role INTEGER REFERENCES role(id) NOT NULL,
    main_photo VARCHAR(500) NOT NULL UNIQUE,
    date_of_birth DATE NOT NULL,
    date_of_death DATE,
    short_bio VARCHAR(500) NOT NULL,
    long_bio TEXT NOT NULL,
    source VARCHAR(10) NOT NULL
);

-- Create portraits_in_roles table (junction table)
CREATE TABLE IF NOT EXISTS portraits_in_roles (
    id SERIAL PRIMARY KEY,
    portrait_id INTEGER REFERENCES portrait(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES role(id) ON DELETE CASCADE
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(25) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);
"""

try:
    # Write SQL to a temporary file
    temp_sql_file = "temp_create_tables.sql"
    with open(temp_sql_file, "w") as f:
        f.write(sql_script)
    
    # Execute SQL script
    cmd = ["psql", "-h", host, "-p", port, 
          "-U", username, "-d", db_name, 
          "-f", temp_sql_file]
    
    subprocess.run(cmd, env=env, check=True)
    
    # Clean up temporary file
    os.remove(temp_sql_file)
    
    print("Tables created successfully.")
except Exception as e:
    print(f"Error creating tables: {str(e)}")
    if os.path.exists(temp_sql_file):
        os.remove(temp_sql_file)
    sys.exit(1)

# Update application configuration
print("\nUpdating application configuration...")

# Find the config file
app_dir = Path("src/RhythmRegistryApp")
config_file = app_dir / "config.py"

# Create a random secret key
secret_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(24))

# Create config content
config_content = f"""# Database Configuration
DB_HOST = '{host}'
DB_PORT = '{port}'
DB_NAME = '{db_name}'
DB_USER = '{username}'
DB_PASSWORD = '{password}'

# Secret key for session
SECRET_KEY = '{secret_key}'
"""

try:
    # Make sure the directory exists
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Write the config file
    with open(config_file, "w") as f:
        f.write(config_content)
    
    print(f"Config file created successfully at {config_file}")
except Exception as e:
    print(f"Error updating configuration: {str(e)}")
    sys.exit(1)

# Success message
print("\n" + "=" * 60)
print("SETUP COMPLETED SUCCESSFULLY!".center(60))
print("=" * 60)
print("\nYour RhythmRegistry database has been set up and configured.")
print("You can now start the application.")