import logging
from flask import Flask, request, render_template, send_from_directory, url_for, redirect, session, send_file, flash
from PIL import Image, ImageDraw, ImageFont
import random, textwrap
import os, io
from pymongo import MongoClient, ReturnDocument
from bson.objectid import ObjectId
import pandas as pd
# from datetime import datetime
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
# app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key'  # Required for session management

# Define path for the temporary folder
TEMP_FOLDER = 'C:\\Users\\acer\\Documents\\temp\\'
BACKUP_FOLDER = 'C:\\Users\\acer\\Documents\\backup_bon\\'

# Koneksi ke MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['CS_KARIADI']

# Koleksi untuk menyimpan counter
counter_collection = db['counters']
cs_collection = db['CS']  # Koleksi untuk menyimpan data CS

# Inisialisasi counter jika belum ada
if counter_collection.count_documents({'_id': 'bonid'}) == 0:
    counter_collection.insert_one({'_id': 'bonid', 'sequence_value': 0})

def get_next_sequence_value(sequence_name, reset=False):
    sequence = db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}} if not reset else {"$set": {"sequence_value": 0}},
        return_document=ReturnDocument.AFTER
    )
    return sequence['sequence_value']

@app.route('/edit_bon/<id>', methods=['GET'])
def edit_bon(id):
    result = cs_collection.find_one({'_id': ObjectId(id)})
    if result:
        return render_template('edit_bon.html', result=result)
    else:
        return "Data not found", 404

@app.route('/update_bon/<id>', methods=['POST'])
def update_bon(id):
    updated_data = {
        'noBon': request.form['noBon'],
        'namaBarang': request.form['namaBarang'],
        'Pemesan': request.form['Pemesan'],
        'from': request.form['from'],
        'macamPekerjaan': request.form['macamPekerjaan'],
        'diterimaOleh': request.form['diterimaOleh'],
        'tanggalOrder': request.form['tanggalOrder'],
        'diterimaJam': request.form['diterimaJam'],
        'dikerjakanBagian': request.form['dikerjakanBagian'],
        'tanggalTL': request.form['tanggalTl'],
        'tanggalSelesai': request.form['tanggalSelesai'],
        'PIC': request.form['PIC'],
        'dikerjakanSiapa': request.form['dikerjakanSiapa'],
        'keterangan': request.form['keterangan']
    }
    
    logging.debug(f"Updating document with ID: {id}")
    logging.debug(f"Updated data: {updated_data}")
    
    result = cs_collection.update_one({'_id': ObjectId(id)}, {'$set': updated_data})
    
    if result.modified_count > 0:
        return redirect(url_for('table'))
    else:
        return "No changes made or item not found", 404

# @app.route('/export_to_excel', methods=['POST'])
# def export_to_excel():
#     # Retrieve data from MongoDB
#     data = list(cs_collection.find())
    
#     # Convert MongoDB data to DataFrame
#     df = pd.DataFrame(data)
    
#     # Drop MongoDB's default `_id` field if present
#     if '_id' in df.columns:
#         df.drop('_id', axis=1, inplace=True)

#     # Define the desired column order
#     column_order = [
#         'noBon', 'Pemesan', 'from', 'macamPekerjaan', 'dikerjakanBagian',
#         'namaBarang', 'tanggalOrder', 'tanggalTL', 'tanggalSelesai', 'PIC',
#         'dikerjakanSiapa', 'keterangan', 'diterimaOleh', 'diterimaJam'
#     ]
    
#     # Reorder columns in the DataFrame
#     df = df[column_order]
    
#     # Create a BytesIO buffer to hold the Excel file
#     buffer = io.BytesIO()
    
#     # Write the DataFrame to the buffer as an Excel file
#     with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
#         df.to_excel(writer, index=False, sheet_name='Sheet1')
    
#     # Seek to the beginning of the buffer
#     buffer.seek(0)
    
#     # Get the current date and format it
#     current_date = datetime.now().strftime('%Y-%m-%d')
#     filename = f'data_{current_date}.xlsx'
    
#     # Return the Excel file as a response
#     return send_file(
#         buffer,
#         as_attachment=True,
#         download_name=filename,
#         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#     )

# Function to export data to Excel and save to specific folder
def export_to_excel_and_save():
    # Retrieve data from MongoDB
    data = list(cs_collection.find())
    
    # Convert MongoDB data to DataFrame
    df = pd.DataFrame(data)
    
    # Drop MongoDB's default `_id` field if present
    if '_id' in df.columns:
        df.drop('_id', axis=1, inplace=True)
    
    # Define the desired column order
    column_order = [
        'noBon', 'Pemesan', 'from', 'macamPekerjaan', 'dikerjakanBagian',
        'namaBarang', 'tanggalOrder', 'tanggalTL', 'tanggalSelesai', 'PIC',
        'dikerjakanSiapa', 'keterangan', 'diterimaOleh', 'diterimaJam'
    ]
    
    # Reorder columns in the DataFrame
    df = df[column_order]
    
    # Create a BytesIO buffer to hold the Excel file
    buffer = io.BytesIO()
    
    # Write the DataFrame to the buffer as an Excel file
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    # Seek to the beginning of the buffer
    buffer.seek(0)
    
    # Get the current date and format it
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f'backup_data_{current_date}.xlsx'
    
    # Define the path to save the file
    save_path = os.path.join(r'C:\Users\acer\Documents\backup_bon', filename)
    
    # Save the buffer content to a file
    with open(save_path, 'wb') as f:
        f.write(buffer.getvalue())
    
    print(f'File saved to {save_path}')

# Setup the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(export_to_excel_and_save, 'cron', day_of_week='tue', hour=9, minute=0)
scheduler.start()

# Define a separate route for manual export to Excel
@app.route('/export_to_excel', methods=['POST'])
def export_to_excel():
    # Retrieve data from MongoDB
    data = list(cs_collection.find())
    
    # Convert MongoDB data to DataFrame
    df = pd.DataFrame(data)
    
    # Drop MongoDB's default `_id` field if present
    if '_id' in df.columns:
        df.drop('_id', axis=1, inplace=True)
    
    # Define the desired column order
    column_order = [
        'noBon', 'Pemesan', 'from', 'macamPekerjaan', 'dikerjakanBagian',
        'namaBarang', 'tanggalOrder', 'tanggalTL', 'tanggalSelesai', 'PIC',
        'dikerjakanSiapa', 'keterangan', 'diterimaOleh', 'diterimaJam'
    ]
    
    # Reorder columns in the DataFrame
    df = df[column_order]
    
    # Create a BytesIO buffer to hold the Excel file
    buffer = io.BytesIO()
    
    # Write the DataFrame to the buffer as an Excel file
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    # Seek to the beginning of the buffer
    buffer.seek(0)
    
    # Get the current date and format it
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = f'data_{current_date}.xlsx'
    
    # Return the Excel file as a response
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
@app.route('/bon', methods=['GET'])
def bon():
    query = request.args.get('search')
    page = int(request.args.get('page', 1))
    per_page = 10  # Number of items per page

    try:
        query_int = int(query)
        search_query = {'$or': [{'noBon': query_int}, {'namaBarang': {'$regex': query, '$options': 'i'}}]}
    except (ValueError, TypeError):
        search_query = {'namaBarang': {'$regex': query, '$options': 'i'}}

    # Calculate total count and number of pages
    total_count = cs_collection.count_documents(search_query)
    total_pages = (total_count + per_page - 1) // per_page

    # Ensure the current page is within bounds
    page = max(1, min(page, total_pages))

    # Fetch the data for the current page, sorted by noBon in descending order
    results = list(cs_collection.find(search_query)
                   .sort('noBon', -1)  # Sort by noBon in descending order
                   .skip((page - 1) * per_page)
                   .limit(per_page))

    return render_template('bon.html', results=results, query=query, page=page, total_pages=total_pages)

@app.route('/delete_bon', methods=['POST'])
def delete_bon():
    # Ambil parameter dari formulir
    id = request.form.get('id')  # Ini adalah _id MongoDB
    noBon = request.form.get('noBon')  # Ini adalah nilai yang digunakan untuk file

    # Logging untuk debugging
    print(f"Received id: {id}")
    print(f"Received noBon: {noBon}")

    try:
        if id:
            # Hapus dokumen dari MongoDB menggunakan _id
            result = cs_collection.delete_one({'_id': ObjectId(id)})
            print(f"MongoDB delete result: {result.deleted_count} document(s) deleted.")
        else:
            print("ID tidak ditemukan.")

        if noBon:
            # Tentukan jalur file untuk dihapus
            file_path = os.path.join(TEMP_FOLDER, f'{noBon}.pdf')
            print(f"Attempting to delete file: {file_path}")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} dihapus.")
            else:
                print(f"File {file_path} tidak ditemukan.")
        else:
            print("noBon tidak ditemukan.")

    except Exception as e:
        print(f"An error occurred: {e}")

    # Redirect ke halaman yang sesuai
    return redirect(url_for('barang'))

@app.route('/reset_and_clear', methods=['POST'])
def reset_and_clear():
    try:
        # Reset the bon_id in MongoDB
        get_next_sequence_value('bonid', reset=True)

        # Clear all data from the 'CS' collection
        cs_collection.delete_many({})

        # Delete all files in the temp folder
        for filename in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        return redirect(url_for('barang'))
    except Exception as e:
        logging.exception("Error during reset and clear")
        return "Error: Failed to reset ID, clear database, and delete files."

@app.route('/', methods=['GET'])
def barang():
    return render_template('barang.html')

@app.route('/handle_barang', methods=['POST'])
def handle_barang():
    nama_barang = request.form.get('namaBarang')
    session['nama_barang'] = nama_barang  # Store in session
    
    # Remove old PNG file if it exists
    if 'certificate_filename' in session:
        old_png_path = os.path.join(TEMP_FOLDER, session['certificate_filename'])
        if os.path.exists(old_png_path):
            os.remove(old_png_path)

    return redirect(url_for('home'))

@app.route('/home', methods=['GET'])
def home():
    nama_barang = session.get('nama_barang', '')
    bon_id = session.get('bon_id', None)
    if bon_id is None:
        bon_id = counter_collection.find_one({'_id': 'bonid'})['sequence_value']
        session['bon_id'] = bon_id
    bon_id = int(bon_id)  # Ensure bon_id is an integer
    return render_template('home.html', bon_id=bon_id, nama_barang=nama_barang)

@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.form.to_dict()
        logging.info(f"Received data: {data}")

        # Tambahkan bon_id ke data
        no_bon = session.get('bon_id')
        if no_bon is None:
            return "Error: No Bon ID available."

        # Convert no_bon to integer before formatting
        no_bon = int(no_bon)
        data['noBon'] = no_bon

        # Simpan data ke sesi
        session['bon_id'] = data.get('noBon')
        session['nama_barang'] = data.get('namaBarang')
        session['Pemesan'] = data.get('Pemesan')
        session['from'] = data.get('from')
        session['macamPekerjaan'] = data.get('macamPekerjaan')
        session['diterimaOleh'] = data.get('diterimaOleh')
        session['tanggalOrder'] = data.get('tanggalOrder')
        session['diterimaJam'] = data.get('diterimaJam')
        session['dikerjakanBagian'] = data.get('dikerjakanBagian')
        # Tambahkan field tersembunyi
        session['tanggalTL'] = data.get('tanggalTL', '')
        session['tanggalSelesai'] = data.get('tanggalSelesai', '')
        session['PIC'] = data.get('PIC', '')
        session['dikerjakanSiapa'] = data.get('dikerjakanSiapa', '')
        session['keterangan'] = data.get('keterangan', '')

        certificate_filename = generate_certificate(data)
        session['certificate_filename'] = certificate_filename
        return render_template('home.html', bon_id=data['noBon'], nama_barang=data['namaBarang'], certificate_url=url_for('get_temp_file', filename=certificate_filename))
    except Exception as e:
        logging.exception("Error during certificate generation")
        return "An error occurred during certificate generation"

@app.route('/download')
def download():
    try:
        certificate_filename = session.get('certificate_filename')
        if not certificate_filename:
            return "Error: No certificate generated."

        # Path to the PNG file
        png_path = os.path.join(TEMP_FOLDER, certificate_filename)

        # Retrieve the noBon value from session
        no_bon = session.get('bon_id')
        if no_bon is None:
            return "Error: No Bon ID available."

        # Define the PDF file name to be the same as noBon
        pdf_filename = f"{no_bon}.pdf"
        pdf_path = os.path.join(TEMP_FOLDER, pdf_filename)

        # Convert PNG to PDF
        img = Image.open(png_path)
        img = img.convert('RGB')
        img.save(pdf_path, "PDF", resolution=100.0)

        # Simpan data ke MongoDB setelah download
        data = {
            'noBon': no_bon,
            'Pemesan': session.get('Pemesan'),
            'from': session.get('from'),
            'macamPekerjaan': session.get('macamPekerjaan'),
            'dikerjakanBagian': session.get('dikerjakanBagian'),
            'namaBarang': session.get('nama_barang'),
            'tanggalOrder': session.get('tanggalOrder'),
            'tanggalTL': session.get('tanggalTL', ''),
            'tanggalSelesai': session.get('tanggalSelesai', ''),
            'PIC': session.get('PIC', ''),
            'dikerjakanSiapa': session.get('dikerjakanSiapa', ''),
            'keterangan': session.get('keterangan', ''),
            'diterimaOleh': session.get('diterimaOleh'),
            'diterimaJam': session.get('diterimaJam')
        }
        cs_collection.insert_one(data)

        # Update the session to increment bon_id
        get_next_sequence_value('bonid')
        session.pop('bon_id', None)

        # Provide the PDF file for download
        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
    
    except Exception as e:
        logging.exception("Error during download")
        return "Error: Failed to process the download."
    finally:
        # Hapus semua file PNG di folder temp
        for filename in os.listdir(TEMP_FOLDER):
            if filename.endswith('.png'):
                file_path = os.path.join(TEMP_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        # Redirect to barang.html after download
        return redirect(url_for('barang'))

@app.route('/table', methods=['GET'])
def table():
    # Number of items per page
    per_page = 10

    # Get the current page from the query parameters, default to 1 if not provided
    page = int(request.args.get('page', 1))

    # Calculate the total number of documents in the collection
    total_count = cs_collection.count_documents({})

    # Calculate the total number of pages
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    # Ensure the current page is within bounds
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    # Calculate the number of documents to skip
    skip = (page - 1) * per_page

    # Fetch the documents for the current page, sorted by noBon in descending order
    results = list(cs_collection.find()
                   .sort('noBon', -1)  # Sort by noBon in descending order
                   .skip(skip)
                   .limit(per_page)) if total_count > 0 else []

    return render_template('table.html', results=results, page=page, total_pages=total_pages)

@app.route('/temp/<filename>')
def get_temp_file(filename):
    return send_from_directory(TEMP_FOLDER, filename)

def generate_certificate(data: dict) -> str:
    try:
        logging.info("Starting certificate generation")
        logging.info(f"Data received for certificate: {data}")
        img = Image.open("certificate_template.png")
        draw = ImageDraw.Draw(img)

        # Define base positions for other fields
        positions = {
            'noBon': (1200, 150),
            'Pemesan': (130, 450),
            'from': (920, 450),
            'macamPekerjaan': (130, 700),
            'namaBarang': (920, 700),
            'diterimaOleh': (550, 890),
            'tanggalOrder': (550, 1000),
            'diterimaJam': (550, 1115),
            'dikerjakanBagian': (700, 1230)  # Base position for 'dikerjakanBagian'
        }

        # Define X positions based on the value of dikerjakanBagian
        x_positions = {
            1: (620, 1250),
            2: (760, 1250),
            3: (900, 1250),
            4: (1040, 1250),
            5: (1180, 1250),
            6: (1320, 1250),
            7: (1460, 1250),
            8: (1600, 1250),
            9: (1740, 1250)
        }

        text_color = (0, 0, 0)
        font_path = "arial.ttf"
        font_size = 48
        logging.info(f"Using font path: {font_path}")
        font = ImageFont.truetype(font_path, font_size)

        def wrap_text(text, max_width):
            wrapped_text = textwrap.fill(text, width=max_width)
            return wrapped_text

        for key, position in positions.items():
            if key == 'dikerjakanBagian':
                dikerjakan_bagian = data.get(key, 0)
                try:
                    dikerjakan_bagian = int(dikerjakan_bagian)
                except ValueError:
                    dikerjakan_bagian = 0
                
                if dikerjakan_bagian in x_positions:
                    position = x_positions[dikerjakan_bagian]
                text = 'X'  # Always show 'X' for dikerjakanBagian
                logging.info(f"Setting position for 'dikerjakanBagian' ({dikerjakan_bagian}): {position}")
            else:
                text = str(data.get(key, ''))
                # Wrap text to fit the image width
                text = wrap_text(text, 33)  # Adjust the width as needed

            logging.info(f"Drawing text '{text}' at position {position}")
            # Split text into multiple lines for drawing
            lines = text.split('\n')
            y_offset = position[1]
            for line in lines:
                draw.text((position[0], y_offset), line, fill=text_color, font=font)
                y_offset += font.getsize(line)[1]  # Move to next line position

        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)

        file_name = f"{random.randint(0, 9999)}.png"
        temp_file_path = os.path.join(TEMP_FOLDER, file_name)
        img.save(temp_file_path)

        logging.info(f"Certificate generated and saved as {file_name}")
        return file_name
    except Exception as e:
        logging.exception("Error during certificate generation")
        raise e

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True)