from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import timedelta
from .config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, SECRET_KEY


app = Flask(__name__)

# Configuration section
app.config["SECRET_KEY"] = SECRET_KEY
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://rhythm_registry_user:2UFsBkwFQ7Uh85skVcMWeD9rsnE42xZ6@dpg-d0bssrpr0fns73drcbmg-a/rhythm_registry'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=2)

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

login_manager.login_view = "login"


from . import routes
