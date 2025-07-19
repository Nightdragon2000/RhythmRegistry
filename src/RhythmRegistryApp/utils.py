import os
from werkzeug.utils import secure_filename
from RhythmRegistryApp import app
from flask import flash

# ---------------------- FILE HANDLING FUNCTIONS ---------------------- #
def rename_image(main_photo, id, table):
    if main_photo:
        # Extract file extension
        _, extension = os.path.splitext(main_photo.filename)
        file_name = secure_filename(f"{table}_{id}{extension}")

        images_dir = os.path.join("RhythmRegistryApp", "static", "images")
        
        # Ensure the directory exists
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            
        file_save_path = os.path.join(images_dir, file_name)        
        main_photo.save(file_save_path)
        file_access_path = f"/static/images/{file_name}"

        return file_access_path
    else:
        return None





