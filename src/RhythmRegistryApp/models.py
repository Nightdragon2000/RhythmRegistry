from RhythmRegistryApp import db, login_manager
from flask_login import UserMixin


# ---------------------- USER AUTHENTICATION ---------------------- #
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)


# ---------------------- BASIC MODELS ---------------------- #
class Portrait(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)   
    main_role = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    main_photo = db.Column(db.String(500), nullable=False, unique=True) 
    date_of_birth = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)
    short_bio = db.Column(db.String(500), nullable=False)
    long_bio = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(10), nullable=False)

    # Relationship
    roles = db.relationship('Role', backref='portrait', lazy='select')
 

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100), nullable=False)
      

# ---------------------- RELATIONSHIP MODELS ---------------------- #
class PortraitsInRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portrait_id = db.Column(db.Integer, db.ForeignKey('portrait.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    # Relationships
    portraits = db.relationship('Portrait', backref='portraits_in_roles', lazy='select')
    roles = db.relationship('Role', backref='portraits_in_roles', lazy='select')


  