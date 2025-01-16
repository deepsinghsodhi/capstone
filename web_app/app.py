from flask import Flask, request, render_template, send_file,url_for,  session as flask_session
import boto3
import pandas as pd
import os
import io

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

session = boto3.Session(profile_name='saurab')
textract = session.client('textract')

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        print(f"File saved to {filepath}")
        table_data = extract_table_data(filepath)
        print(f"Extracted table data: {table_data}")
        flask_session['table_data'] = table_data  # Store table data in session
        return render_template('index.html', table_data=table_data)
    return 'No file uploaded.'


@app.route('/download_csv')
def download_csv():
    table_data = session.get('table_data')
    if not table_data:
        return 'No table data available.'
    
    # Generate CSV in memory
    csv_buffer = io.StringIO()
    df = pd.DataFrame(table_data)
    df.to_csv(csv_buffer, index=False, header=False)
    csv_buffer.seek(0)
    
    return send_file(csv_buffer, as_attachment=True, download_name='extracted_table.csv', mimetype='text/csv')

def extract_table_data(image_path):
    with open(image_path, 'rb') as document:
        response = textract.analyze_document(
            Document={'Bytes': document.read()},
            FeatureTypes=['TABLES']
        )
    
    print(f"Textract response: {response}")
    
    table_data = []
    for block in response['Blocks']:
        if block['BlockType'] == 'CELL':
            row_index = block['RowIndex'] - 1
            col_index = block['ColumnIndex'] - 1
            text = ''
            if 'Relationships' in block:
                for relationship in block['Relationships']:
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            for child_block in response['Blocks']:
                                if child_block['Id'] == child_id and child_block['BlockType'] == 'WORD':
                                    text += child_block['Text'] + ' '
            text = text.strip()
            while len(table_data) <= row_index:
                table_data.append([])
            while len(table_data[row_index]) <= col_index:
                table_data[row_index].append('')
            table_data[row_index][col_index] = text
    
    print(f"Extracted table data: {table_data}")
    return table_data



def save_to_csv(table_data, original_filename):
    if not table_data:
        print("No table data extracted.")
        return None
    
    df = pd.DataFrame(table_data)
    print(f"DataFrame created: {df}")
    
    csv_filename = os.path.splitext(original_filename)[0] + '.csv'
    csv_filepath = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
    df.to_csv(csv_filepath, index=False, header=False)  # Ensure header is set to False if no headers are present
    print(f"CSV file saved to {csv_filepath}")
    return csv_filepath



if __name__ == '__main__':
    app.run(debug=True)