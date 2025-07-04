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
from celery import Celery

# from flask_server.transformer_vision import process_vision
from tools.web_search import search_tavily
from ai.prompts import fill_form, fill_home_form, fill_home_form_forward, fill_home_form_websearch, fill_appliance_form, default_home_form, default_appliance_form, example_schema
from flask_server.test_page import homePage
from tools.utils import validate_file, validate_form, verify_jwt
from ai.process import process_tika, process_plaintext, home_loop

load_dotenv()
PORT = int(os.getenv("PORT", 8000))

capp = Celery('tasks', broker=os.getenv('RABBITMQ_URL', 'http://localhost:5672/'))

@capp.task
def test_task():
    print("This is a test task running in Celery")
    return "Task completed successfully"

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/uploads'
app.config['PROCESSING_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/processing'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSING_FOLDER'], exist_ok=True)

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
        try:
            content = process_plaintext(text, schema)
        except ValueError as e:
            print(f"Error processing PDF: {e}")
            return jsonify({"error": str(e)}), 400
        
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
        try:    
            content = process_plaintext(text, schema, fill_appliance_form(text, schema))
        except ValueError as e:
            print(f"Error processing appliance photo: {e}")
            return jsonify({"error": str(e)}), 400
        
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

        try:
            content = process_plaintext(text, schema)
        except ValueError as e:
            print(f"Error processing text file: {e}")
            return jsonify({"error": str(e)}), 400
        
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
        
        try:
            content = process_plaintext(text, schema)
        except ValueError as e:
            print(f"Error processing text: {e}")
            return jsonify({"error": str(e)}), 400
        
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