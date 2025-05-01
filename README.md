# Rhythm Registry

<img src="images/dashboard.png" alt="Dashboard" >

## Overview

Rhythm Registry is a Flask-based web application that allows users to:
- Manage portraits of individuals
- Assign roles to individuals
- Define relationships between individuals
- Import data from Wikipedia
- Generate PDF reports
- Search and filter the database

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

## Features
### Portrait Management
- Add, edit, and delete portraits
- Assign primary and secondary roles to individuals
- Upload and manage portrait images
### Role Management
- Create and manage roles for individuals
- Associate portraits with multiple roles
### Relationship Management
- Define relationships between individuals
- Visualize connections between portraits
### Data Import
- Import data from Wikipedia
- Process dates and extract person information
- Add portraits and roles to the database automatically
### PDF Generation
- Generate PDF reports of search results
- Preview and download PDF documents
### Search Functionality
- Search by name, role, date range
- Filter results based on various criteria

## Technologies Used
- Flask - Web framework
- SQLAlchemy - ORM for database operations
- Jinja2 - Template engine
- Bootstrap - Frontend framework
- ReportLab - PDF generation
- Beautiful Soup - Web scraping for Wikipedia data import
