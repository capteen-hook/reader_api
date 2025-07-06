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
from flask_server.tools.web_search import search_tavily
from flask_server.ai.prompts import fill_form, fill_home_form, fill_home_form_forward, fill_home_form_websearch, fill_appliance_form, default_home_form, default_appliance_form, example_schema
from flask_server.test_page import homePage
from flask_server.tools.utils import validate_file, validate_form, verify_jwt, upload_file
from flask_server.ai.process import process_tika, process_plaintext, home_loop

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

with open('flask_server/openapi_spec.yaml', 'r') as f:
    openapispec = f.read()

openapispec = ""
def process_file(request):
    try:
        file_path = upload_file(request)
        
        if file_path.split('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp']:
            # For image files, we can use vision processing
            # but for now- just try and get text from it with Tika
            # text = process_vision(file_path)
            text = process_tika(file_path)
        else:
            # For PDF files, use Tika to extract text
            text = process_tika(file_path)
            
        if not text:
            raise ValueError("No text extracted from the file")
        
        schema = validate_form(request.form.get('form'), default=example_schema)
        
        if not schema:
            raise ValueError("Invalid form schema provided")
        content = fill_form(text, schema)
        if not content:
            raise ValueError("No content generated from the form")
        
        return jsonify(content), 200
    
    except ValueError as ve:
        print(f"Value error: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({"error": str(e)}), 500

@app.before_request
def verify_api_key():
    # root path and docs path are public
    if request.path == '/' and request.method == 'GET' and len(request.path) == 1:
        return
    elif request.path == '/docs' and request.method == 'GET' and len(request.path) == 5:
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

@app.route('/process/file', methods=['POST'])
def process_file_default():
    return process_file(request)
    
@app.route('/process/home', methods=['POST'])
def process_home_report():
    try:
        file_path = upload_file(request)
        schema = validate_form(request.form.get('form'), default=default_home_form)
        
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
    # this just does process/file for now
    return process_file(request)
    
@app.route('/process/ocr', methods=['POST'])
def tika_process():
    # get the OCR result from Tika
    try:
        file_path = upload_file(request)
        
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
    
@app.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        tasks = capp.control.inspect().active() or {}
        return jsonify(tasks), 200
    except Exception as e:
        print(f"Error retrieving tasks: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = capp.AsyncResult(task_id)
        if task.state == 'PENDING':
            response = {'state': task.state, 'status': 'Pending...'}
        elif task.state != 'FAILURE':
            response = {'state': task.state, 'result': task.result}
        else:
            response = {'state': task.state, 'error': str(task.info)}
        
        return jsonify(response), 200
    except Exception as e:
        print(f"Error retrieving task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500
    
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
    
@app.route('/', methods=['GET'])
def index():
    return homePage(default_home_form, default_appliance_form, example_schema)

@app.route('/docs', methods=['GET'])
def docs():
    return jsonify(openapispec, 200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)