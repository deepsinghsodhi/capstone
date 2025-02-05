from flask import Blueprint, render_template, request, send_file, current_app, redirect, url_for, Response
from werkzeug.utils import secure_filename
from io import BytesIO, StringIO
import zipfile
import os
import tempfile
from PIL import Image
from pdf2image import convert_from_path
import torch
import shutil
import os
from datetime import datetime
from transformers import AutoImageProcessor, TableTransformerForObjectDetection

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'pdf'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize the table detection model
image_processor = AutoImageProcessor.from_pretrained("microsoft/table-transformer-detection")
model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-transformer-detection")

@main.route('/')
def index():
    return redirect(url_for('main.upload_file'))

@main.route('/upload_file', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['pdf_file']
        
        if file.filename == '':
            return 'No file selected', 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_path = os.path.join(temp_dir, filename)
                file.save(pdf_path)
                
                # Convert PDF to images
                images = convert_from_path(pdf_path)
                
                saved_images = []
                for page_num, image in enumerate(images):
                    # Process the image with the table detection model
                    inputs = image_processor(images=image, return_tensors="pt")
                    outputs = model(**inputs)

                    # Convert outputs to Pascal VOC format
                    target_sizes = torch.tensor([image.size[::-1]])
                    results = image_processor.post_process_object_detection(
                        outputs, 
                        threshold=0.8, 
                        target_sizes=target_sizes
                    )[0]

                    # Extract and save detected tables
                    for idx, (score, label, box) in enumerate(zip(
                        results["scores"], 
                        results["labels"], 
                        results["boxes"]
                    )):
                        if score >= 0.8:  # Only save tables with high confidence
                            box = [int(i) for i in box.tolist()]
                            xmin, ymin, xmax, ymax = box
                            
                            # Crop the detected table
                            cropped_table = image.crop((xmin, ymin, xmax, ymax))
                            
                            # Save the cropped table
                            image_filename = f'table_page{page_num + 1}_table{idx + 1}.jpg'
                            image_path = os.path.join(
                                current_app.static_folder, 
                                'extracted_tables', 
                                image_filename
                            )
                            cropped_table.save(image_path, 'JPEG')
                            saved_images.append(f'extracted_tables/{image_filename}')
                
                return render_template('results.html', tables=saved_images)
    
    return render_template('upload.html')

@main.route('/download_images', methods=['POST'])
def download_images():
    selected_tables = request.form.getlist('selected_tables[]')
    
    if not selected_tables:
        return "No images selected", 400

    # Create a download directory with timestamp to avoid conflicts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', f'extracted_tables_{timestamp}')
    os.makedirs(download_dir, exist_ok=True)

    # Copy each selected image to the download directory
    for table in selected_tables:
        source_path = os.path.join(current_app.static_folder, table.replace('static/', ''))
        dest_path = os.path.join(download_dir, os.path.basename(source_path))
        shutil.copy2(source_path, dest_path)

    return f"Images have been downloaded to: {download_dir}", 200

@main.route('/extract_csv', methods=['POST'])
def extract_csv():
    selected_table = request.form.get('selected_table')
    if not selected_table:
        return "No table selected", 400

    # Create a CSV file in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Add your CSV extraction logic here
    writer.writerow(['Column 1', 'Column 2', 'Column 3'])
    writer.writerow(['Data 1', 'Data 2', 'Data 3'])
    
    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=extracted_table.csv'
        }
    )