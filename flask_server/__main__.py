# server.py
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import requests
import os
from dotenv import load_dotenv
from outlines import from_ollama, Generator
from outlines.types import JsonSchema
import ollama
import gc
from bs4 import BeautifulSoup
import json
import jwt 
from functools import wraps

# from flask_server.transformer_vision import process_vision
from flask_server.web_search import search_tavily
from flask_server.prompts import (fill_form, fill_home_form, fill_home_form_forward, fill_home_form_websearch, fill_appliance_form, default_home_form, default_appliance_form, example_schema)
from flask_server.test_page import homePage

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998/tika")
PORT = int(os.getenv("PORT", 8000))

client = ollama.Client()
model = from_ollama(client, os.getenv("MODEL_NAME", "gemma3:4b"))

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/uploads'
app.config['PROCESSING_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/processing'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSING_FOLDER'], exist_ok=True)

def home_loop(text, schema):
    
    # home inspection reports can be quite long, so we need to split them into chunks
    chunksize = 5000
    overlap = 100
    chunks = [text[i:i + chunksize] for i in range(0, len(text), chunksize - overlap)]
    results = []
    final_res = {}
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        result = process_plaintext(chunk, schema, fill_home_form_forward(chunk, schema, final_res))
        
        # try and merge the result with the final result- deferring to the new result 
        # print the type of final res
        for key, value in final_res.items():
            # if result does not have the key, add it
            if key not in result:
                result[key] = value
        
        print("Result from chunk:", result)
        results.append(result)
        final_res = result
        
    print("Final result after processing all chunks:", final_res)
    print("All results:", results)
    
    # do a web search for the address if it exists
    # address = final_res.get('address', '')
    if address:
        print("Performing web search for address:", address)
        search_results = search_tavily(address)
        
        final_res = process_plaintext(search_results, schema, fill_home_form_websearch(search_results, schema, final_res))
        
        print("Final result after web search:", final_res)
        
    return final_res

def process_tika(file_path):
    if file_path.endswith('.pdf'):
        content_type = 'application/pdf'
    elif file_path.endswith('.png') or file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
        content_type = 'image/' + file_path.split('.')[-1]
    else:
        raise ValueError("Unsupported file type. Only PDF and image files are supported.")
            
            
    headers = {
        'Content-Type': content_type,
    }
    
    with open(file_path, 'rb') as f:
        pdf_data = f.read()
    response = requests.put(TIKA_URL, data=pdf_data, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Tika processing failed with status code {response.status_code}")
    
    # clean up the tika response - we only want the text content inside the <div class="ocr"> tags
    try:
        return response.text.split('<div class="ocr">')[1].split('</div>')[0]
    except IndexError:
        print("Tika response does not contain expected OCR -> may have found no text")
        return response.text
    
def process_plaintext(text, schema, prompt=None):
    if prompt is None:
        prompt = fill_form(text, schema)
    generator = Generator(model, schema)
    # Process the text with the prompt
    result = generator(prompt)    
    return json.loads(result)

def validate_file(filename):
    try:
        # Validate filename
        filename = request.json.get('filename')
        if not filename:
            print("Filename is missing in request")
            raise ValueError("Filename is required")

        # Sanitize filename
        filename = secure_filename(filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File {filename} not found in upload folder")
            raise FileNotFoundError(f"File {filename} not found in upload folder")
        
        return file_path
    except ValueError as ve:
        raise ve
    except FileNotFoundError as fnfe:
        raise fnfe
    except Exception as e:
        print(f"Error validating file: {e}")
        raise Exception("Error validating file")
    
def validate_form(form_data, default=example_schema):
    try:
        if not form_data:
            return default
        
        # Validate form data against the schema
        schema = JsonSchema(form_data)
        
        # print("Validating form data against schema:", schema)
        # print("Schema content:", json.loads(schema.schema))
        # If validation passes, return the schema
        return schema
    except Exception as e:
        print(f"Error validating form data: {e}")
        raise ValueError("Invalid form data")
        
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key") 

def verify_jwt(token):
    try:
        # Decode the JWT token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.before_request
def verify_api_key():
    # root path is unprotected
    if request.path == '/' and request.method == 'GET' and len(request.path) == 1:
        return
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Missing Authorization header"}), 401
    
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token.split("Bearer ")[1]
    print(f"Token: {token}")
    decoded = verify_jwt(token)
    if not decoded:
        print("Invalid or expired token")
        return jsonify({"error": "Invalid or expired token"}), 401

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "No file provided"}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        return jsonify({"filename": filename}), 200
    
    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/process/pdf', methods=['POST'])
def process_pdf():
    try:
        
        file_path = validate_file(request.json.get('filename'))
        schema = validate_form(request.json.get('form'), default=example_schema)
       
        text = process_tika(file_path)
        content = process_plaintext(text, schema)
        
        return jsonify(content), 200
    except ValueError as ve:
        print(f"Value error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except FileNotFoundError as fnfe:
        print(f"File not found: {fnfe}")
        return jsonify({"error": str(fnfe)}), 404
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/process/home', methods=['POST'])
def process_home_report():
    try:
        file_path = validate_file(request.json.get('filename'))
        schema = validate_form(request.json.get('form'), default=default_home_form)
        
        text = process_tika(file_path)
        content = home_loop(text, schema)
        
        return jsonify(content), 200
    except ValueError as ve:
        print(f"Value error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except FileNotFoundError as fnfe:
        print(f"File not found: {fnfe}")
        return jsonify({"error": str(fnfe)}), 404
    except Exception as e:
        print(f"Error processing home report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/process/appliance', methods=['POST'])
def process_appliance_photo():
    try:
        file_path = validate_file(request.json.get('filename'))
        schema = validate_form(request.json.get('form'), default=default_appliance_form)
        
        # content = process_vision(text, schema) This is a lot more powerful, but requires a lot of resources
        text = process_tika(file_path)
        content = process_plaintext(text, schema, fill_appliance_form(text, schema))
        
        return jsonify(content), 200
    except ValueError as ve:
        print(f"Value error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except FileNotFoundError as fnfe:
        print(f"File not found: {fnfe}")
        return jsonify({"error": str(fnfe)}), 404
    except Exception as e:
        print(f"Error processing appliance photo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/process/txt', methods=['POST'])
def process_txt():
    try:
        file_path = validate_file(request.json.get('filename'))
        schema = validate_form(request.json.get('form'), default=example_schema)
        
        with open(file_path, 'r') as f:
            text = f.read()
    
        content = process_plaintext(text, schema)
        
        return jsonify(content), 200        
    except ValueError as ve:
        print(f"Value error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except FileNotFoundError as fnfe:
        print(f"File not found: {fnfe}")
        return jsonify({"error": str(fnfe)}), 404
    except Exception as e:
        print(f"Error processing text file: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/process/text', methods=['POST'])
def process_text():
    try:
        text = request.json.get('text')
        schema = validate_form(request.json.get('form'), default=example_schema)
        
        if not text:
            return jsonify({"error": "Invalid text"}), 400
        
        content = process_plaintext(text, schema)
        
        return jsonify(content), 200
    
    except Exception as e:
        print(f"Error processing text: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return homePage(default_home_form, default_appliance_form, example_schema)

@app.route('/clear', methods=['GET'])
def clear_uploads():
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.remove(file_path)
            
        for filename in os.listdir(app.config['PROCESSING_FOLDER']):
            file_path = os.path.join(app.config['PROCESSING_FOLDER'], filename)
            os.remove(file_path)
            
        return jsonify({"message": "Uploads cleared"}), 200
    except Exception as e:
        print(f"Error clearing uploads: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/process/tika', methods=['POST'])
def tika_process():
    # get the OCR result from Tika
    try:
        file_path = validate_file(request.json.get('filename'))
        
        text = process_tika(file_path)
        
        return jsonify(text), 200
    except ValueError as ve:
        print(f"Value error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except FileNotFoundError as fnfe:
        print(f"File not found: {fnfe}")
        return jsonify({"error": str(fnfe)}), 404
    except Exception as e:
        print(f"Error processing with Tika: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)