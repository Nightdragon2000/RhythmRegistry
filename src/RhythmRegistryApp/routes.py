from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, current_user, logout_user
import os
from RhythmRegistryApp import app, db, bcrypt
from RhythmRegistryApp.utils import rename_image
from RhythmRegistryApp.models import Portrait, Role, PortraitsInRoles, Users
from RhythmRegistryApp.forms import (NewPortraitForm, NewRoleForm, LoginForm, SignUpForm, EmptyForm, DateRangeForm)
from sqlalchemy import extract, and_, or_,func
from datetime import datetime
from io import BytesIO
import requests
import logging
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from sqlalchemy import text

# ---------------------- CONSTANTS ---------------------- #
PER_PAGE_PORTRAITS = 20
PER_PAGE_ROLES = 20
PER_PAGE_ROLES_IN_PORTRAITS = 20

# ---------------------- AUTHENTICATION ROUTES ---------------------- #
@app.before_request
def require_login():
    allowed_routes = ["login", "sign_up", "static"]
    if request.endpoint not in allowed_routes and not current_user.is_authenticated:
        return redirect(url_for("login"))

@app.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if request.method == "POST" and form.validate_on_submit():
        email_or_username = form.email_or_username.data
        password = form.password.data

        # Check if input is email or username
        user = Users.query.filter(
            (Users.email == email_or_username) | 
            (Users.username == email_or_username)
        ).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for("index"))
        else:
            flash("Incorrect username/email or password", "danger")

    return render_template("login.html", form=form)

@app.route("/sign_up/", methods=["GET", "POST"])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_email = Users.query.filter_by(email=form.email.data).first()
        if existing_email:
            form.email.errors.append('This email is already registered')
            return render_template("sign_up.html", form=form)
        
        # Check if username already exists
        existing_username = Users.query.filter_by(username=form.username.data).first()
        if existing_username:
            form.username.errors.append('This username is already taken')
            return render_template("sign_up.html", form=form)
            
        # Create new user if email and username don't exist
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = Users(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
        )
        
        db.session.add(user)
        
        success = False
        try:
            db.session.commit()
            success = True
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Registration error: {str(e)}")
        
        if success:
            flash("Your account has been created! You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("An error occurred during registration. Please try again.", "danger")
    
    return render_template("sign_up.html", form=form)

@app.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for("login"))

# ---------------------- MAIN ROUTES ---------------------- #
@app.route("/index/")
def index():
    return render_template("index.html")

# ---------------------- PORTRAIT ROUTES ---------------------- #
@app.route("/manage_portraits/", methods=["GET", "POST"])
def manage_portraits():
    form = EmptyForm()

    page = request.args.get("page", 1, type=int)
    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "desc")

    if not hasattr(Portrait, sort_by):
        sort_by = "id"

    if order == "asc":
        order_by = getattr(Portrait, sort_by).asc()
    else:
        order_by = getattr(Portrait, sort_by).desc()

    portraits = Portrait.query.order_by(order_by).paginate(
        page=page, per_page=PER_PAGE_PORTRAITS
    )
    return render_template("manage_portraits.html", portraits=portraits, sort_by=sort_by, order=order, form=form)

@app.route("/add_portrait/", methods=["GET", "POST"])
def add_portrait():
    form = NewPortraitForm()
    roles = Role.query.all()

    # Prepare role choices for form
    role_choices = [(role.id, role.role) for role in roles]
    role_choices.insert(0, (0, "Select Role"))
    form.main_role.choices = role_choices

    # Set choices for secondary roles
    for sub_form in form.secondary_roles:
        sub_form.form.main_role = form.main_role
        sub_form.form.secondary_role.choices = role_choices

    if form.validate_on_submit():
        # Extract form data
        first_name = form.first_name.data
        last_name = form.last_name.data
        main_role_id = form.main_role.data
        main_photo = form.main_photo.data
        date_of_birth = form.date_of_birth.data
        date_of_death = form.date_of_death.data if form.date_of_death.data else None
        short_bio = form.short_bio.data
        long_bio = form.long_bio.data

        # Create portrait object
        portrait = Portrait(
            first_name=first_name,
            last_name=last_name,
            main_role=main_role_id,
            date_of_birth=date_of_birth,
            date_of_death=date_of_death,
            short_bio=short_bio,
            long_bio=long_bio,
        )

        db.session.add(portrait)
        db.session.flush()  # Generate the ID for the portrait

        # Handle photo upload
        if main_photo:
            image_path = rename_image(main_photo, portrait.id, "portrait")
            portrait.main_photo = image_path

        # Handle secondary roles
        if form.secondary_roles:
            for sub_form in form.secondary_roles:
                secondary_role_data = sub_form.form.secondary_role.data
                if secondary_role_data and int(secondary_role_data) > 0:  # Ensure valid role is selected
                    portrait_role = PortraitsInRoles(
                        portrait_id=portrait.id, role_id=int(secondary_role_data)
                    )
                    db.session.add(portrait_role)

        db.session.commit()

        flash(f"Portrait {portrait.id} has been added successfully", "success")
        return redirect(url_for("manage_portraits"))

    return render_template("portrait_form.html", form=form, roles=roles, is_edit=False, form_action=url_for('add_portrait'), submit_text="Save Portrait")

@app.route("/edit_portrait/<int:portrait_id>", methods=["GET", "POST"])
def edit_portrait(portrait_id):
    portrait = Portrait.query.get_or_404(portrait_id)
    form = NewPortraitForm(obj=portrait)
    roles = Role.query.all()

    # Prepare role choices for form
    role_choices = [(role.id, role.role) for role in roles]
    role_choices.insert(0, (0, "Select Role"))
    form.main_role.choices = role_choices

    existing_pirs = PortraitsInRoles.query.filter_by(portrait_id=portrait_id).all()

    # Extract role IDs
    existing_roles = []
    for pir in existing_pirs:
        if pir.role_id != None:
            existing_roles.append(str(pir.role_id))

    # Ensure form has enough entries for existing roles
    while len(form.secondary_roles) < len(existing_roles):
        form.secondary_roles.append_entry()

    # Populate form with existing data
    if request.method == "GET":
        for i in range(len(form.secondary_roles)):
            form.secondary_roles[i].secondary_role.choices = role_choices
            if i < len(existing_roles):
                form.secondary_roles[i].secondary_role.data = existing_roles[i]
    else:
        for role_form in form.secondary_roles:
            role_form.secondary_role.choices = role_choices
            role_form.form.main_role = form.main_role

    if request.method == "POST" and form.validate_on_submit():
        updated_roles = [
            role_form.secondary_role.data for role_form in form.secondary_roles
            if role_form.secondary_role.data and int(role_form.secondary_role.data) > 0
        ]

        # Update portrait data
        portrait.first_name = form.first_name.data
        portrait.last_name = form.last_name.data
        portrait.main_role = form.main_role.data
        portrait.date_of_birth = form.date_of_birth.data
        portrait.date_of_death = (
            form.date_of_death.data if form.date_of_death.data else None
        )
        portrait.short_bio = form.short_bio.data
        portrait.long_bio = form.long_bio.data

        main_photo = request.files.get("main-photo")

        # Delete existing photo if checkbox is checked
        if form.delete_image.data and portrait.main_photo:
            filename = os.path.basename(portrait.main_photo)

            file_path = os.path.join("RhythmRegistryApp", "static", "images", filename)
            
            print(f"Attempting to delete: {file_path}")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Successfully deleted image: {file_path}")
                portrait.main_photo = None
            else:
                print(f"File not found: {file_path}")
                portrait.main_photo = None  

        # Handle new photo upload
        if main_photo:

            if portrait.main_photo:
                filename = os.path.basename(portrait.main_photo)
                
                old_file_path = os.path.join("RhythmRegistryApp", "static", "images", filename)
                
                # Try to remove the old file
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
        
            # Save new image
            image_path = rename_image(main_photo, portrait.id, "portrait")
            portrait.main_photo = image_path

        # Add new roles
        for role in updated_roles:
            if role not in existing_roles:
                portrait_role = PortraitsInRoles(portrait_id=portrait_id, role_id=role)
                db.session.add(portrait_role)

        # Remove roles that are no longer selected
        for role in existing_roles:
            if role not in updated_roles:
                portrait_role = PortraitsInRoles.query.filter_by(
                    portrait_id=portrait_id, role_id=role
                ).first()
                db.session.delete(portrait_role)

        db.session.commit()
        flash(f"Portrait {portrait.id} has been updated successfully", "success")
        return redirect(url_for("manage_portraits"))

    return render_template("portrait_form.html", form=form, portrait=portrait, is_edit=True, form_action=url_for('edit_portrait', portrait_id=portrait.id), submit_text="Update Portrait")

@app.route("/delete_portrait/<int:portrait_id>", methods=["GET", "POST"])
def delete_portrait(portrait_id):
    portrait = Portrait.query.get_or_404(portrait_id)

    # Delete associated image file if exists
    if portrait.main_photo:
        file_path = os.path.join(
            "RhythmRegistryApp", portrait.main_photo.lstrip("/\\")
        )
        print(file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print("File not found.")

    pirs = PortraitsInRoles.query.filter_by(portrait_id=portrait_id).all()
    for pir in pirs:
        db.session.delete(pir)

    db.session.delete(portrait)
    db.session.commit()

    flash(f"Portrait {portrait.id} has been deleted successfully", "success")
    return redirect(request.referrer)

@app.route("/search_in_portraits/", methods=["GET", "POST"])
def search_in_portraits():
    form = EmptyForm()
    search_text_in_portrait = request.form.get("search_text_in_portrait")

    if request.method == "POST":
        query = db.session.query(Portrait).join(Role)

        # Apply text search filter
        if search_text_in_portrait:
            query = query.filter(
                db.or_(
                    Portrait.first_name.ilike(f"%{search_text_in_portrait}%"),
                    Portrait.last_name.ilike(f"%{search_text_in_portrait}%"),
                    Role.role.ilike(f"%{search_text_in_portrait}%")
                )
            )

        portraits = query.paginate(page=1, per_page=PER_PAGE_PORTRAITS)

        return render_template("manage_portraits.html", portraits=portraits, form=form)
    else:
        portraits = Portrait.query.order_by(Portrait.id).paginate(page=1, per_page=PER_PAGE_PORTRAITS)
        return render_template("manage_portraits.html", portraits=portraits, form=form)

# --------------------------------- ROLE ROUTES ---------------------------------#

@app.route("/manage_roles/", methods=["GET", "POST"])
def manage_roles():
    form = EmptyForm()

    page = request.args.get("page", 1, type=int)
    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "desc")

    if not hasattr(Role, sort_by):
        sort_by = "id"

    if order == "asc":
        order_by = getattr(Role, sort_by).asc()
    else:
        order_by = getattr(Role, sort_by).desc()

    roles = Role.query.order_by(order_by).paginate(page=page, per_page=PER_PAGE_ROLES)
    return render_template("manage_roles.html", roles=roles, sort_by=sort_by, order=order, form=form)

@app.route("/add_role/", methods=["GET", "POST"])
def add_role():
    form = NewRoleForm()

    if form.validate_on_submit():
        role = form.role.data.capitalize()

        # Check if the role already exists
        existing_role = Role.query.filter_by(role=role).first()
        if existing_role:
            form.role.errors.append(f'Role {role} already exists.')
        else:
            # If the role does not exist, add it
            new_role = Role(role=role)
            db.session.add(new_role)
            db.session.commit()

            flash(f"Role {role} has been added successfully", "success")
            return redirect(url_for("manage_roles"))

    return render_template("add_role.html", form=form)

@app.route("/delete_role/<int:role_id>", methods=["GET", "POST"])
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    
    db.session.delete(role)
    db.session.commit()

    flash(f"Role {role.id} has been deleted successfully", "success")
    return redirect(url_for("manage_roles"))

# --------------------------------- PORTRAITS IN ROLES ROUTES ---------------------------------#

@app.route("/manage_portraits_in_roles/", methods=["GET", "POST"])
def manage_portraits_in_roles():
    form = EmptyForm()

    page = request.args.get("page", 1, type=int)
    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "desc")

    # Determine sort order based on parameters
    if sort_by == "id":
        if order == "asc":
            order_by = PortraitsInRoles.portrait_id.asc()
        else:
            order_by = PortraitsInRoles.portrait_id.desc()
    elif sort_by == "name":
        if order == "asc":
            order_by = Portrait.last_name.asc()
        else:
            order_by = Portrait.last_name.desc()
    else:
        order_by = PortraitsInRoles.portrait_id.desc()

    # Get unique portrait IDs and sort them
    distinct_portrait_ids_query = (
        PortraitsInRoles.query.join(PortraitsInRoles.portraits)
        .with_entities(
            PortraitsInRoles.portrait_id, Portrait.first_name, Portrait.last_name
        )
        .distinct()
        .order_by(order_by)
    )

    # Paginate them
    distinct_portrait_ids = distinct_portrait_ids_query.paginate(
        page=page, per_page=PER_PAGE_ROLES_IN_PORTRAITS
    )

    # Get PortraitsInRoles records for the paginated portrait
    paginated_portrait_ids = [pid[0] for pid in distinct_portrait_ids.items]
    portraits_in_roles = (
        PortraitsInRoles.query.filter(
            PortraitsInRoles.portrait_id.in_(paginated_portrait_ids)
        )
        .join(PortraitsInRoles.portraits)
        .order_by(order_by)
        .all()
    )

    # Build dictionary of portraits with their roles
    portraits_in_roles_dictionary = {}
    for pir in portraits_in_roles:
        if (
            pir.portraits 
            and pir.portraits.roles
            and pir.portraits.roles.role is not None
            and pir.roles
            and pir.roles.role is not None
        ):
            portrait_id = pir.portrait_id
            portrait_name = f"{pir.portraits.first_name} {pir.portraits.last_name}"
            portrait_main_role = pir.portraits.roles.role
            portrait_role = pir.roles.role

            if portrait_id not in portraits_in_roles_dictionary:
                portraits_in_roles_dictionary[portrait_id] = {
                    "id": portrait_id,
                    "name": portrait_name,
                    "main_role": portrait_main_role,
                    "roles": [portrait_role],
                }
            else:
                portraits_in_roles_dictionary[portrait_id]["roles"].append(portrait_role)

    return render_template("manage_portraits_in_roles.html", portraits_in_roles_dictionary=portraits_in_roles_dictionary, form=form, sort_by=sort_by, order=order, portraits=distinct_portrait_ids)

@app.route("/edit_portrait_in_role/<int:pir_id>", methods=["GET", "POST"])
def edit_portrait_in_role(pir_id):
    portrait = Portrait.query.get_or_404(pir_id)
    portraits_in_roles = PortraitsInRoles.query.filter_by(portrait_id=pir_id).all()
    roles = Role.query.all()
    form = NewPortraitForm(obj=portrait)

    # Prepare role choices for form
    role_choices = [(role.id, role.role) for role in roles]
    role_choices.insert(0, (0, "Select Role"))
    form.main_role.choices = role_choices

    # Get existing portrait-role relationships
    existing_pirs = PortraitsInRoles.query.filter_by(portrait_id=pir_id).all()

    # Extract role IDs
    existing_roles = []
    for pir in existing_pirs:
        if pir.role_id is not None:
            existing_roles.append(str(pir.role_id))

    # Ensure form has enough entries for existing roles
    while len(form.secondary_roles) < len(existing_roles):
        form.secondary_roles.append_entry()

    # Populate form with existing data
    if request.method == "GET":
        for i in range(len(form.secondary_roles)):
            form.secondary_roles[i].secondary_role.choices = role_choices
            if i < len(existing_roles):
                form.secondary_roles[i].secondary_role.data = existing_roles[i]
    else:
        for role_form in form.secondary_roles:
            role_form.secondary_role.choices = role_choices
            role_form.form.main_role = form.main_role

    if request.method == "POST" and form.validate_on_submit():
        # Extract and filter valid secondary roles
        updated_roles = []
        seen_roles = set()  # Track roles we've already seen to prevent duplicates
        
        for role_form in form.secondary_roles:
            role_id = role_form.secondary_role.data
            # Only add valid roles that aren't duplicates
            if role_id and int(role_id) > 0 and role_id not in seen_roles:
                updated_roles.append(role_id)
                seen_roles.add(role_id)
        
        portrait.main_role = form.main_role.data

        # Add new roles
        for role in updated_roles:
            if role not in existing_roles:
                portrait_role = PortraitsInRoles(portrait_id=pir_id, role_id=role)
                db.session.add(portrait_role)

        # Remove roles that are no longer selected
        for role in existing_roles:
            if role not in updated_roles:
                portrait_role = PortraitsInRoles.query.filter_by(
                    portrait_id=pir_id, role_id=role
                ).first()
                if portrait_role:
                    db.session.delete(portrait_role)

        db.session.commit()
        flash(f"Roles for {portrait.first_name} {portrait.last_name} updated successfully", "success")
        return redirect(url_for("manage_portraits_in_roles"))
   
    return render_template("edit_portrait_in_role.html", portraits_in_roles=portraits_in_roles, roles=roles, form=form)

@app.route("/delete_relatshionship/<int:pir_id>", methods=["GET", "POST"])
def delete_relatshionship(pir_id):
    pir = PortraitsInRoles.query.get_or_404(pir_id)
    form = EmptyForm()
    
    portrait_id = pir.portrait_id
    role_id = pir.role_id
    
    role_name = Role.query.get(role_id).role if role_id else "Unknown"
    
    db.session.delete(pir)
    db.session.commit()

    flash(f"Relationship with role '{role_name}' has been deleted successfully", "success")
    return redirect(url_for("edit_portrait_in_role", pir_id=portrait_id, form=form))

@app.route("/delete_portrait_in_role/<int:pir_id>", methods=["GET", "POST"])
def delete_portrait_in_role(pir_id):
    portrait = Portrait.query.get_or_404(pir_id)

    pirs = PortraitsInRoles.query.filter_by(portrait_id=pir_id).all()    
    relationship_count = len(pirs)

    for pir in pirs:
        db.session.delete(pir)

    db.session.commit()
    
    flash(f"All {relationship_count} additional roles associated with {portrait.first_name} {portrait.last_name} have been deleted.", "success")
    return redirect(url_for("manage_portraits_in_roles"))

#--------------------------------- DATABASE ROUTES ---------------------------------#

@app.route("/manage_database/", methods=["GET"])
def manage_database():
    return render_template("manage_database.html", page_title="Database Management")

@app.route("/delete_all_portraits/", methods=["GET", "POST"])
def delete_all_portraits():
    # Delete the entire images folder instead of individual files
    images_dir = os.path.join("ContentEmpneusisApp", "static", "images")
    if os.path.exists(images_dir):        
        # Delete all files in the images directory
        for filename in os.listdir(images_dir):
            file_path = os.path.join(images_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    
    PortraitsInRoles.query.delete()
    Portrait.query.delete()
      
    # Get the table names from the models
    portrait_table = Portrait.__tablename__
    portraits_in_roles_table = PortraitsInRoles.__tablename__
    
    # Reset sequences using PostgreSQL's setval function
    db.session.execute(text(f"SELECT setval(pg_get_serial_sequence('{portrait_table}', 'id'), 1, false)"))
    db.session.execute(text(f"SELECT setval(pg_get_serial_sequence('{portraits_in_roles_table}', 'id'), 1, false)"))
    
    db.session.commit()
    flash("All portraits and their relationships have been deleted successfully. ID counters have been reset.", "success")

    return redirect(url_for("manage_database"))

@app.route("/delete_all_roles/", methods=["GET", "POST"])
def delete_all_roles():
    # First, set main_role to NULL for all portraits
    Portrait.query.update({Portrait.main_role: None})
    
    PortraitsInRoles.query.delete()
    Role.query.delete()
    
    # Get the table name from the model
    role_table = Role.__tablename__
    
    # Reset sequence using PostgreSQL's setval function
    db.session.execute(text(f"SELECT setval(pg_get_serial_sequence('{role_table}', 'id'), 1, false)"))
    
    db.session.commit()    
    flash("All roles have been deleted successfully. ID counter has been reset.", "success")
    
    return redirect(url_for("manage_database"))

@app.route("/import_wikipedia/", methods=["POST"])
def import_wikipedia():
    # Get date parameters from the form
    use_date_range = request.form.get('use_date_range') == 'on'
    errors = {}

    if use_date_range:
        start_month = request.form.get('start_month', '')
        start_day = request.form.get('start_day', '')
    else:
        start_month = request.form.get('wiki_month', '')
        start_day = request.form.get('wiki_day', '')
    
    if not start_month or not start_day:
        errors['start_date'] = "Please select both month and day for the start date."
    
    # Format start date as dd-mm with proper validation
    if start_day and start_month:
        start_date = f"{start_day.zfill(2)}-{start_month.zfill(2)}"
    else:
        start_date = "01-01"
    
    if use_date_range:
        end_month = request.form.get('end_month', '')
        end_day = request.form.get('end_day', '')
        
        if not end_month or not end_day:
            errors['end_date'] = "Please select both month and day for the end date."
        
        # Format end date with proper validation
        if end_day and end_month:
            end_date = f"{end_day.zfill(2)}-{end_month.zfill(2)}"
        else:
            end_date = start_date
            
        # Check if start date is after end date
        try:
            # Create datetime objects for comparison (using a dummy year)
            start_date_obj = datetime.strptime(f"2000-{start_month}-{start_day}", "%Y-%m-%d")
            end_date_obj = datetime.strptime(f"2000-{end_month}-{end_day}", "%Y-%m-%d")
            
            # Compare dates 
            if start_date_obj > end_date_obj:
                errors['date_range'] = "Start date cannot be after end date."
        except ValueError:
            errors['date_format'] = "Invalid date format."
    else:
        end_date = start_date
    
    
    # Get section IDs based on checkboxes
    import_births = request.form.get('import_births') == 'on'
    import_deaths = request.form.get('import_deaths') == 'on'
    
    # Check if at least one checkbox is selected
    if not import_births and not import_deaths:
        errors['checkbox'] = "Please select at least one option (Births or Deaths)."
    
    # If there are any errors, return to the form with all errors
    if errors:
        return render_template(
            "manage_database.html", 
            page_title="Database Management",
            errors=errors,
            import_births=import_births,
            import_deaths=import_deaths,
            wiki_month=start_month,
            wiki_day=start_day,
            start_month=start_month,
            start_day=start_day,
            end_month=end_month,
            end_day=end_day,
            use_date_range=use_date_range
        )
    
    section_ids = []
    if import_births:
        section_ids.append('2.3')
    if import_deaths:
        section_ids.append('3.3')
    
    # Convert section_ids list to comma-separated string for command line
    section_ids_param = ','.join(section_ids)  
    
    data_import_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data_import'))
    
    # Create a command to run the script with date parameters and section IDs
    cmd_command = f'start cmd /k "cd /d {data_import_path} && python wikipedia_data_importer.py {start_date} {end_date} {section_ids_param}"'
    
    # Execute the command
    os.system(cmd_command)
    
    # Create message for user
    if use_date_range and start_date != end_date:
        date_range_msg = f" to {end_date}"
        date_msg = f"dates {start_date}{date_range_msg}"
    else:
        date_msg = f"the date {start_date}"

    sections = []
    if import_births:
        sections.append("births")
    if import_deaths:
        sections.append("deaths")

    sections_msg = f" (importing {' and '.join(sections)})" if sections else ""
    
    flash(f"Wikipedia data import script is now running for {date_msg}{sections_msg}. Please wait for it to complete.", "info")
    return redirect(url_for("manage_database"))

# ---------------------- SEARCH BY DATE ROUTES ---------------------- #

@app.route("/search_by_date/", methods=["GET", "POST"])
def search_by_date():
    # Clean up previews folder when returning to this page
    if request.method == "GET":
        previews_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'previews'))
        if os.path.exists(previews_dir):
            for filename in os.listdir(previews_dir):
                if filename.startswith("preview_") and filename.endswith(".pdf"):
                    try:
                        os.remove(os.path.join(previews_dir, filename))
                    except Exception as e:
                        app.logger.error(f"Error removing preview file {filename}: {str(e)}")
    
    form = DateRangeForm()  
    events = []  
    portraits_birthdays = []  
    portraits_deaths = []  

    if form.validate_on_submit():
        start_date = datetime.strptime(form.start_date.data, '%d-%m')
        start_day = start_date.day
        start_month = start_date.month

        if form.search_by_range.data:
            end_date = datetime.strptime(form.end_date.data, '%d-%m')
            end_day = end_date.day
            end_month = end_date.month

        search_types = request.form.getlist('search_types')

        if 'birth_dates' in search_types:
            if form.search_by_range.data:
                portraits_birthdays = Portrait.query.filter(
                    extract('day', Portrait.date_of_birth) >= start_day,
                    extract('month', Portrait.date_of_birth) >= start_month,
                    extract('day', Portrait.date_of_birth) <= end_day,
                    extract('month', Portrait.date_of_birth) <= end_month
                ).order_by(func.extract('month', Portrait.date_of_birth), 
                          func.extract('day', Portrait.date_of_birth)).all()
            else:
                portraits_birthdays = Portrait.query.filter(
                    extract('day', Portrait.date_of_birth) == start_day,
                    extract('month', Portrait.date_of_birth) == start_month
                ).order_by(func.extract('month', Portrait.date_of_birth), 
                          func.extract('day', Portrait.date_of_birth)).all()

        if 'death_dates' in search_types:
            if form.search_by_range.data:
                portraits_deaths = Portrait.query.filter(
                    extract('day', Portrait.date_of_death) >= start_day,
                    extract('month', Portrait.date_of_death) >= start_month,
                    extract('day', Portrait.date_of_death) <= end_day,
                    extract('month', Portrait.date_of_death) <= end_month,
                    Portrait.date_of_death.isnot(None)
                ).order_by(func.extract('month', Portrait.date_of_death), 
                          func.extract('day', Portrait.date_of_death)).all()
            else:
                portraits_deaths = Portrait.query.filter(
                    extract('day', Portrait.date_of_death) == start_day,
                    extract('month', Portrait.date_of_death) == start_month,
                    Portrait.date_of_death.isnot(None)
                ).order_by(func.extract('month', Portrait.date_of_death), 
                          func.extract('day', Portrait.date_of_death)).all()

        selected_portrait_columns = request.form.getlist('portrait_columns')
        selected_event_columns = request.form.getlist('event_columns')

        # PDF Generation Setup         
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []  

        # Font Setup 
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = 'DejaVuSans'
        title_style = ParagraphStyle(name='Title', parent=styles['Normal'], fontSize=12, leading=16, alignment=0, leftIndent=-22, underline=True)
        right_align_style = ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2, rightIndent=-20)

        # --------- PDF Helper Functions --------- #
        def draw_text(text, style=styles['Normal']):
            return Paragraph(text, style)

        # Add the date to the right side of the PDF
        if form.search_by_range.data:
            end_date = datetime.strptime(form.end_date.data, '%d-%m')
            elements.append(draw_text(f"Date: {start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}", right_align_style))
        else:
            elements.append(draw_text(f"Date: {start_date.strftime('%d/%m')}", right_align_style))

        # Function to download and create an image element
        def draw_image(image_url):
            if image_url is None:
                logging.error("Image URL is None")
                return Paragraph("No Image", styles['Normal'])
                
            if not isinstance(image_url, str):
                logging.error(f"Image URL is not a string: {type(image_url)}")
                return Paragraph("No Image", styles['Normal'])
                
            if not image_url.startswith("http"):
                image_url = "https:" + image_url
            logging.debug(f"Downloading image from URL: {image_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
            try:
                response = requests.get(image_url, headers=headers)
                if response.status_code == 200:
                    images_dir = os.path.join('static', 'images')
                    if not os.path.exists(images_dir):
                        os.makedirs(images_dir)
                    # Use a unique filename for each image
                    image_filename = f"{uuid.uuid4()}.jpg"
                    image_path = os.path.join(images_dir, image_filename)
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    logging.debug(f"Image saved to: {image_path}")
                    print(f"Image saved to: {image_path}")  
                    image = Image(image_path, width=100, height=100)
                    return image
                else:
                    logging.error(f"Failed to download image. Status code: {response.status_code}")
                    return Paragraph("No Image", styles['Normal'])
            except Exception as e:
                logging.error(f"Exception occurred while downloading image: {e}")
                return Paragraph("No Image", styles['Normal'])

        def get_roles(portrait):
            roles = [role.role for role in portrait.roles]
            return ", ".join(roles)

        def get_additional_roles(portrait):
            additional_roles = [pir.roles.role for pir in portrait.portraits_in_roles]
            return ", ".join(additional_roles)

        def get_main_role_text(portrait):
            main_role = Role.query.get(portrait.main_role)
            return main_role.role if main_role else "Unknown"

        # PDF Content Generation 
        # Function to add portraits section to the PDF
        def add_portraits_section(title, portraits):
            elements.append(draw_text(" "))
            elements.append(draw_text(title, title_style))
            elements.append(Spacer(1, 10))  # Margin below the title
            
            for i, portrait in enumerate(portraits):
                text_elements = []
                if 'id' in selected_portrait_columns:
                    text_elements.append(draw_text(f"<b>ID:</b> {portrait.id}<br/>"))
                if 'name' in selected_portrait_columns:
                    text_elements.append(draw_text(f"<b>Name:</b> {portrait.first_name} {portrait.last_name}<br/>"))
                if 'date_of_birth' in selected_portrait_columns:
                    text_elements.append(draw_text(f"<b>Date of Birth:</b> {portrait.date_of_birth.strftime('%d/%m/%Y')}<br/>"))
                if 'date_of_death' in selected_portrait_columns and portrait.date_of_death:
                    text_elements.append(draw_text(f"<b>Date of Death:</b> {portrait.date_of_death.strftime('%d/%m/%Y')}<br/> "))
                if 'short_bio' in selected_portrait_columns:
                    text_elements.append(draw_text("<b>Short Biography:</b>"))
                    text_elements.append(draw_text(f"{portrait.short_bio}"))
                if 'main_role' in selected_portrait_columns:
                    text_elements.append(draw_text(f"<b>Main Role:</b> {get_main_role_text(portrait)}<br/>"))
                if 'additional_roles' in selected_portrait_columns:
                    text_elements.append(draw_text(f"<b>Additional Roles:</b> {get_additional_roles(portrait)}<br/>"))

                # Create table layout based on selected columns
                if 'main_photo' in selected_portrait_columns:
                    image_url = portrait.main_photo
                    if image_url:
                        image_element = draw_image(image_url)
                    else:
                        image_element = Paragraph("No Image", styles['Normal'])
                        
                    if 'long_bio' in selected_portrait_columns:
                        bio_title = draw_text("<b>Detailed Biography:</b>")
                        bio_content = draw_text(f"{portrait.long_bio}")
                        bio_elements = [bio_title, bio_content]
                        
                        data = [
                            [image_element, text_elements],
                            [bio_elements, '']
                        ]
                    else:
                        data = [
                            [image_element, text_elements]
                        ]
                    col_widths = [100, 400]
                else:
                    if 'long_bio' in selected_portrait_columns:
                        text_elements.append(draw_text("<b>Detailed Biography:</b>"))
                        text_elements.append(draw_text(f"{portrait.long_bio}"))
                    data = [
                        [text_elements]
                    ]
                    col_widths = [500]

                # Apply table styling
                table = Table(data, colWidths=col_widths)
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('BOX', (0, 0), (-1, -1), 1, colors.black),
                    ('LEFTPADDING', (1, 0), (1, 0), 12),
                    ('RIGHTPADDING', (1, 0), (1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 1), (-1, 1), -2) if 'main_photo' in selected_portrait_columns and 'long_bio' in selected_portrait_columns else ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('SPAN', (0, 1), (1, 1)) if 'main_photo' in selected_portrait_columns and 'long_bio' in selected_portrait_columns else ('SPAN', (0, 0), (0, 0))
                ]))
                elements.append(KeepTogether([table, Spacer(1, 12)]))

        # Add Content to PDF 
        if portraits_birthdays:
            add_portraits_section("Portraits with Birth Dates:", portraits_birthdays)

        if portraits_deaths:
            add_portraits_section("Portraits with Death Dates:", portraits_deaths)

        # Build and Save PDF 
        doc.build(elements)
        buffer.seek(0)

        # Save the generated PDF as a temporary file
        previews_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'previews'))
        if not os.path.exists(previews_dir):
            os.makedirs(previews_dir)
        pdf_filename = f"preview_{uuid.uuid4()}.pdf"
        temp_pdf_path = os.path.join(previews_dir, pdf_filename)
        with open(temp_pdf_path, 'wb') as f:
            f.write(buffer.getvalue()) 

        # Clean up the temporary image files
        images_dir = os.path.join('static', 'images')
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.endswith(".jpg"):
                    os.remove(os.path.join(images_dir, filename))

        return render_template("preview_pdf.html",
            pdf_url=url_for('static', filename=f'previews/{pdf_filename}'),
            form=form, events=events, portraits_birthdays=portraits_birthdays,portraits_deaths=portraits_deaths)

    return render_template("search_by_date.html", form=form, events=events, portraits_birthdays=portraits_birthdays, portraits_deaths=portraits_deaths)

@app.route("/download_pdf/<filename>")
def download_pdf(filename):
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'previews', filename))
    return send_file(pdf_path, as_attachment=True, download_name='report.pdf', mimetype='application/pdf')

@app.route("/clear_previews/")
def clear_previews():
    previews_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'previews'))
    if os.path.exists(previews_dir):
        for filename in os.listdir(previews_dir):
            if filename.startswith("preview_") and filename.endswith(".pdf"):
                file_path = os.path.join(previews_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    app.logger.info(f"Removed preview file: {filename}")

    return redirect(url_for('search_by_date'))
