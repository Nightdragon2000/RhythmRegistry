# Rhythm Registry

## Overview

RhythmRegistry is a Flask-based web application designed to manage and catalog portraits, roles, and their relationships. It provides a comprehensive system for organizing historical figures, their professions, and biographical information with a user-friendly interface.

## Screenshots

![Dashboard](images/dashboard.png)
*RhythmRegistry main dashboard interface*

## Features
- **Portrait Management**:  Add, edit, and delete portrait records with biographical information
- **Role Management**:  Create and manage professional roles for historical figures
- **Relationship System**:  Associate portraits with multiple roles
- **Wikipedia Integration**:  Import portrait data directly from Wikipedia for specific dates
- **Search Functionality**:  Find portraits through comprehensive search options
- **User Authentication**:  Secure login and registration system
- **Responsive Design**:  Mobile-friendly interface that adapts to all devices
- **Database Tools**:  Utilities for managing the PostgreSQL database

## Installation

### Prerequisites

- Python 3.x
- PostgreSQL database

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Nightdragon2000/RhythmRegistry.git
cd RhythmRegistry
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```
3. Install dependencies::
```bash
pip install -r requirements.txt
```

4. Run database setup:
```bash
python setup_database.py
```

### Running the Application
Start the application with:
```bash
python src/run.py
```

The application will be available at (http://localhost:5002)


## Technologies Used
- Flask - Web framework
- SQLAlchemy - ORM for database operations
- Jinja2 - Template engine
- Bootstrap - Frontend framework
- ReportLab - PDF generation
- Beautiful Soup - Web scraping for Wikipedia data import
