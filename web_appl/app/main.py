import os
from flask import send_file, make_response, zip_file

@main.route('/download_images', methods=['POST'])
def download_images():
    selected_tables = request.form.getlist('selected_tables[]')
    
    if len(selected_tables) == 1:
        # If only one image is selected, send it directly
        image_path = selected_tables[0]
        return send_file(image_path, mimetype='image/jpeg', as_attachment=True)
    else:
        # If multiple images are selected, create a zip file
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for image_path in selected_tables:
                image_name = os.path.basename(image_path)
                zf.write(image_path, image_name)
        
        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='selected_images.zip'
        )