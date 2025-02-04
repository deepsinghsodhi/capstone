from flask import Blueprint, request, render_template
from app.table_extractor import TableExtractor
import os

main = Blueprint('main', __name__)
extractor = TableExtractor()

@main.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded'
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected'

        if file:
            # Save uploaded PDF temporarily
            temp_path = 'temp.pdf'
            file.save(temp_path)
            
            try:
                # Process the PDF
                extracted_tables = extractor.process_pdf(temp_path)
                # Convert paths for template
                template_paths = [path.replace('app/', '') for path in extracted_tables]
                return render_template('results.html', tables=template_paths)
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
    
    return render_template('upload.html')