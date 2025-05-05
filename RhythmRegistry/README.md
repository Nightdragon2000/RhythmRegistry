# RhythmRegistry

![Dashboard](images/dashboard.png)

## Overview

RhythmRegistry is a Flask-based web application designed to manage and organize portraits, roles, and their relationships. It provides a comprehensive system for cataloging historical figures, their professions, and biographical information. The application features a user-friendly interface for adding, editing, and deleting records, as well as importing data from Wikipedia.

## Features

- **Portrait Management**: Add, edit, and delete portrait records with biographical information
- **Role Management**: Create and manage professional roles for historical figures
- **Relationship Management**: Associate portraits with multiple roles
- **Wikipedia Data Import**: Import portrait data from Wikipedia for specific dates
- **Database Management**: Tools for managing the PostgreSQL database
- **User Authentication**: Secure login and registration system
- **Search Functionality**: Search through portrait records
- **Responsive Design**: Mobile-friendly interface

## Prerequisites

- Python 3.6+
- PostgreSQL database server
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/RhythmRegistry.git
   cd RhythmRegistry
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up the PostgreSQL database:
   ```
   python setup_database.py
   ```
   Follow the prompts to configure your database connection. This will create a `.env.example` file with your database configuration.

   The application now uses environment variables for database connection. You can either:
   - Set the environment variables directly in your system
   - Create a `.env` file based on the `.env.example` template

4. Run the application:
   ```
   cd src
   python run.py
   ```

5. Access the application in your web browser at:
   ```
   http://localhost:5002
   ```

## Project Structure

```
├── images/                  # Application images
│   └── dashboard.png        # Dashboard screenshot
├── requirements.txt         # Python dependencies
├── setup_database.py        # Database setup script
└── src/                     # Source code
    ├── RhythmRegistryApp/   # Main application package
    │   ├── __init__.py      # Application initialization
    │   ├── forms.py         # Form definitions
    │   ├── models.py        # Database models
    │   ├── routes.py        # Application routes
    │   ├── static/          # Static files (CSS, JS, etc.)
    │   ├── templates/       # HTML templates
    │   └── utils.py         # Utility functions
    ├── data_import/         # Data import modules
    │   ├── wikipedia_data_importer.py
    │   └── wikipedia_scraper.py
    └── run.py               # Application entry point
```

## Usage

### Authentication

- Register a new account or log in with existing credentials
- The application requires authentication for all pages except login and registration

### Managing Portraits

1. Navigate to the "Manage Portraits" section
2. Add new portraits with biographical information
3. Edit or delete existing portraits
4. Search for specific portraits

### Managing Roles

1. Navigate to the "Manage Roles" section
2. Add new professional roles
3. Delete existing roles

### Managing Relationships

1. Navigate to the "Portrait Relationships" section
2. View and manage associations between portraits and roles

### Importing Data from Wikipedia

1. Navigate to the "Database Management" section
2. Select the date or date range for data import
3. Choose to import births, deaths, or both
4. Click "Import Data" to start the process

## Database Schema

- **role**: Stores professional roles
- **portrait**: Stores biographical information about historical figures
- **portraits_in_roles**: Junction table for the many-to-many relationship between portraits and roles
- **users**: Stores user authentication information

## Deployment to Render

To deploy this application to Render:

1. Create a new Web Service in your Render dashboard
2. Connect your GitHub repository
3. Configure the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd src && python run.py`
4. Add the following environment variables in the Render dashboard:
   - `DB_HOST`: Your PostgreSQL host (use Render's internal PostgreSQL service or external database)
   - `DB_PORT`: Database port (usually 5432)
   - `DB_NAME`: Your database name
   - `DB_USER`: Database username
   - `DB_PASSWORD`: Database password
   - `SECRET_KEY`: A secure random string for session encryption

> **Note**: When using Render's PostgreSQL service, the connection details will be provided in the `DATABASE_URL` environment variable. The application is now configured to automatically parse this URL, so you can simply add the Render PostgreSQL database as an add-on and the connection will be handled automatically. You only need to set the `SECRET_KEY` environment variable manually.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask and its extensions for the web framework
- PostgreSQL for the database
- Bootstrap for the frontend design
- Wikipedia for the data source