import os
from werkzeug.utils import secure_filename
from RhythmRegistryApp import app
from flask import flash


# ---------------------- FILE HANDLING FUNCTIONS ---------------------- #
def rename_image(main_photo, id, table):
    """
    Handles the image upload, renaming, and saving process.
    Returns the file path of the saved image (str).
    """
    if main_photo:
        # Extract file extension
        _, extension = os.path.splitext(main_photo.filename)
        file_name = secure_filename(f"{table}_{id}{extension}")
        
        # Use os.path.join with proper path separators
        images_dir = os.path.join("RhythmRegistryApp", "static", "images")
        
        # Ensure the directory exists
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            
        # Create full path for saving the file
        file_save_path = os.path.join(images_dir, file_name)
        
        # Save the file
        main_photo.save(file_save_path)
        
        # Use forward slashes for the access path
        file_access_path = f"/static/images/{file_name}"

        return file_access_path
    else:
        return None





