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
from flask_server.ai.process import process_tika, process_plaintext, home_loop, process_file
    
load_dotenv()
PORT = int(os.getenv("PORT", 8000))

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/uploads'
app.config['PROCESSING_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/processing'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSING_FOLDER'], exist_ok=True)

capp = Celery('tasks', broker=os.getenv('RABBITMQ_URL', 'http://localhost:5672/'))
# Configure Celery to store task results
capp.conf.update(
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_annotations={
        '*': {'rate_limit': '10/s'}  # Example rate limit
    },
    task_acks_late=True,  # Ensure tasks are acknowledged only after completion
    worker_prefetch_multiplier=1,  # Prevent workers from prefetching too many tasks
)


# Set a task queue limit
MAX_TASKS = int(os.getenv('MAX_TASKS', 30))

@capp.task
def process_file_task(file_path, schema=example_schema):
    print(f"Processing file: {file_path}")
    processed_content = process_file(file_path, schema)
    print(f"Processed content: {processed_content}")
    return processed_content
    
@capp.task
def process_home_task(file_path, schema=default_home_form):
    print(f"Processing home report: {file_path}")
    text = process_tika(file_path)
    content = home_loop(text, schema)
    print(f"Processed home report content: {content}")
    return content

def queue_full():
    """Check if the task queue is full."""
    try:
        active_tasks = capp.control.inspect().active() or {}
        reserved_tasks = capp.control.inspect().reserved() or {}
        total_tasks = sum(len(tasks) for tasks in active_tasks.values()) + sum(len(tasks) for tasks in reserved_tasks.values())
        return total_tasks >= MAX_TASKS
    except Exception as e:
        print(f"Error checking task queue: {e}")
        return False
    
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
    try:
        if queue_full():
            print("Task queue is full, cannot enqueue file processing task")
            return jsonify({"error": "Task queue is full"}), 503
        
        file_path = upload_file(request.form.get('file'))
        schema = validate_form(request.form.get('form'), example_schema)
        
        id = process_file_task.apply_async(args=[file_path, schema])
        return jsonify({"task_id": id.id}), 202
    except Exception as e:
        print(f"Error enqueuing file processing task: {e}")
        return jsonify({"error": str(e)}), 500

    
@app.route('/process/home', methods=['POST'])
def process_home_report():
    try:
        if queue_full():
            print("Task queue is full, cannot enqueue file processing task")
            return jsonify({"error": "Task queue is full"}), 503
        
        file_path = upload_file(request.form.get('file'))
        schema = validate_form(request.form.get('form'), default_home_form)
        
        id = process_home_task.apply_async(args=[file_path, schema])
        return jsonify({"task_id": id.id}), 202
    
    except Exception as e:
        print(f"Error enqueuing home report processing task: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/process/appliance', methods=['POST'])
def process_appliance_photo():
    try:
        if queue_full():
            print("Task queue is full, cannot enqueue file processing task")
            return jsonify({"error": "Task queue is full"}), 503
        
        file_path = upload_file(request.form.get('file'))
        schema = validate_form(request.form.get('form'), default_appliance_form)
        # WIP!
        # process_appliance_task.apply_async(args=[file_path, default_appliance_form])
        id = process_file_task.apply_async(args=[file_path, default_appliance_form])
        return jsonify({"task_id": id.id}), 202

    except Exception as e:
        print(f"Error enqueuing appliance photo processing task: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/process/ocr', methods=['POST']) 
def tika_process():                                       # consider changing this to a task
    # get the OCR result from Tika
    try:
        file_path = upload_file(request.files.get('file'))
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
        queued_tasks = capp.control.inspect().reserved() or {}
        return jsonify({
            "active_tasks": tasks,
            "queued_tasks": queued_tasks
        }), 200
    except Exception as e:
        print(f"Error retrieving tasks: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    try:
        task = capp.AsyncResult(task_id)
        if task.state == 'PENDING':
            response = {'state': task.state, 'status': 'Pending...'}
        elif task.state == 'SUCCESS':
            response = {'state': task.state, 'result': task.result}
        elif task.state == 'FAILURE':
            response = {'state': task.state, 'error': str(task.info)}
        else:
            response = {'state': task.state, 'status': task.info}

        return jsonify(response), 200
    except Exception as e:
        print(f"Error retrieving task {task_id}: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/clear', methods=['GET'])
def clear_uploads():
    try:
        # clear tasks
        capp.control.purge()
        
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
    try:
        with open('flask_server/openapi_spec.yaml', 'r') as f: 
            openapispec = f.read()
    except FileNotFoundError:
        return jsonify({"error": "OpenAPI specification file not found"}), 404
    except Exception as e:
        print(f"Error reading OpenAPI specification: {e}")
        return jsonify({"error": str(e)}), 500
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)