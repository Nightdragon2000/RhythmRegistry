from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SubmitField, FileField, SelectField, PasswordField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Regexp, Optional, ValidationError, Length, Email, EqualTo
from flask_wtf.file import FileAllowed
import re

# ---------------------- VALIDATORS ---------------------- #
def role_selected(form, field):
    """Validates that a role has been selected """
    if field.data == '0':
        raise ValidationError('Please select a role from the dropdown')
    
def secondary_roles_differs_from_main(form, field):
    """Ensures secondary role is different from the main role"""
    if field.data == form.main_role.data and field.data != '0':
        raise ValidationError('Secondary role must be different from the main role')
    
def no_duplicate_roles(form, field):
    """Prevents duplicate secondary roles from being added"""
    role_to_fields = {}
    duplicates = set()

    # 1. Step: Identify all roles and track duplicates
    for entry in field.entries:
        role_field = entry.form.secondary_role
        role = role_field.data
        if role:
            if role in role_to_fields:
                # If role already exists, mark it as a duplicate
                duplicates.add(role)
                # Also mark the previously seen field as a duplicate
                role_to_fields[role].append(role_field)
            else:
                role_to_fields[role] = [role_field]

    # 2. Steps:  Add error messages to all duplicate fields
    for role, fields in role_to_fields.items():
        if role in duplicates:
            for role_field in fields:
                # Append error message only if it doesn't already have an error
                if not role_field.errors:
                    role_field.errors.append('Duplicate role entry is not allowed.')

    if duplicates:
        raise ValidationError('Duplicate role entries are not allowed.')
            
def validate_date_of_death(form, field):
    """Ensures date of death is not before date of birth"""
    if field.data < form.date_of_birth.data:
        raise ValidationError('Date of death must be after date of birth')


# ---------------------- AUTHENTICATION FORMS ---------------------- #
class SignUpForm(FlaskForm):
    """Form for user registration"""
    username = StringField(label='Username', validators=[
        DataRequired(message='Username is required'), 
        Length(min=4, max=25, message='Username must be between 4 and 25 characters')
    ])
    email = StringField(label='Email', validators=[
        DataRequired(message='Email address is required'), 
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField(label='Password', validators=[
        DataRequired(message='Password is required'), 
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    password_confirm = PasswordField(label='Confirm Password', validators=[
        DataRequired(message='Please confirm your password'), 
        EqualTo('password', message='Passwords do not match')
    ])
    
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    """Form for user login"""
    email_or_username = StringField(label='Email or Username', validators=[
        DataRequired(message='Please enter your email or username')
    ])
    password = PasswordField(label='Password', validators=[
        DataRequired(message='Please enter your password')
    ])    
    remember_me = BooleanField(label='Remember Me')

    submit = SubmitField('Login')


# ---------------------- PORTRAIT MANAGEMENT FORMS ---------------------- #
class AddSecondaryRoleForm(FlaskForm):
    """Subform for adding secondary roles to a portrait"""
    secondary_role = SelectField(
        label='Secondary Role', 
        choices=[], 
        validators=[Optional(), role_selected, secondary_roles_differs_from_main]
    )

class NewPortraitForm(FlaskForm):
    """Form for creating or editing a portrait"""
    first_name = StringField(label='First Name', validators=[
        DataRequired(message='First name is required'), 
        Regexp(r'^[^\d]+$', message='First name cannot contain numbers')
    ])
    last_name = StringField(label='Last Name', validators=[
        DataRequired(message='Last name is required'), 
        Regexp(r'^[^\d]+$', message='Last name cannot contain numbers')
    ])
    main_role = SelectField(
        label='Main Role', 
        choices=[], 
        validators=[DataRequired(), role_selected]
    )
    main_photo = FileField(
        label='Main Photo', 
        validators=[
            Optional(strip_whitespace=True), 
            FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG, JPEG, and PNG images are allowed')
        ]
    )
    date_of_birth = DateField(
        label='Date of Birth', 
        validators=[DataRequired(message='This field is required')]
    )
    date_of_death = DateField(
        label='Date of Death', 
        validators=[Optional(), validate_date_of_death]
    )
    short_bio = TextAreaField(label='Short Biography', validators=[Optional()])
    long_bio = TextAreaField(label='Long Biography', validators=[Optional()])
    secondary_roles = FieldList(
        FormField(AddSecondaryRoleForm), 
        min_entries=0,
        validators=[no_duplicate_roles]
    )      
    delete_image = BooleanField(label='Delete Image', default=False)

    submit = SubmitField('Submit')


# ---------------------- ROLE MANAGEMENT FORMS ---------------------- #
class NewRoleForm(FlaskForm):
    """Form for creating a new role"""
    role = StringField(
        label='Role', 
        validators=[
            DataRequired(message='Role name is required'), 
            Regexp('^[A-Za-zΑ-Ωα-ω ]*$', message='Role name can only contain letters and space')
        ]
    )
    
    submit = SubmitField('Submit')


# ---------------------- UTILITY FORMS ---------------------- #
class EmptyForm(FlaskForm):
    """Empty form used for CSRF protection on simple actions"""
    pass
class DateRangeForm(FlaskForm):
    """Form for searching portraits by date range"""
    date_format = r'^\d{2}-\d{2}$'  

    start_date = StringField('Start Date', validators=[
        DataRequired(message="Start date is required"), 
        Regexp(date_format, message="Please use DD-MM format for the date")
    ], render_kw={"placeholder": "DD-MM"})
    
    end_date = StringField('End Date', validators=[
        Optional(), 
        Regexp(date_format, message="Please use DD-MM format for the date")
    ], render_kw={"placeholder": "DD-MM"})
    search_by_range = BooleanField('Date Range', default=False)
    submit = SubmitField('Search')