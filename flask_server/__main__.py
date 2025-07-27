# server.py
from flask import Flask, jsonify, request, make_response
import requests
import os
from dotenv import load_dotenv
from outlines import from_ollama, Generator
import ollama
import gc
from bs4 import BeautifulSoup
import json
import jwt 
import sys
import time
from datetime import datetime
import threading
import redis
from functools import wraps
from celery import Celery
from flask_server.tools.web_search import search_tavily
from flask_server.ai.prompts import fill_form, fill_home_form, fill_home_form_forward, fill_home_form_websearch, fill_appliance_form, default_home_form, default_appliance_form, example_schema
from flask_server.test_page import homePage
from flask_server.tools.utils import validate_file, validate_form, verify_jwt, upload_file
from flask_server.ai.process import process_tika, chat #, process_plaintext, home_loop, process_file
from flask_server.celery import celery
from flask_server.tasks import process_file_task, process_home_task, process_plaintext_task, queue_full, process_vision_task

    
load_dotenv()

def clear_old_uploads_and_tasks(uploads, processing):
    try:
        cutoff_timestamp = time.time() - 2 * 3600  # 2 hours ago
        redis_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        redis_conn = redis.Redis.from_url(redis_url)

        for folder in [uploads, processing]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_timestamp:
                    os.remove(file_path)

        for key in redis_conn.scan_iter("celery-task-meta-*"):
            data = redis_conn.get(key)
            if data:
                try:
                    task_meta = json.loads(data)
                    date_done = task_meta.get("date_done")
                    if date_done:
                        task_time = datetime.strptime(date_done, "%Y-%m-%dT%H:%M:%S.%f")
                        if task_time.timestamp() < cutoff_timestamp:
                            redis_conn.delete(key)
                except Exception as e:
                    print(f"Skipping key {key} due to error: {e}")

        print("Auto-clear complete.")

    except Exception as e:
        print(f"Auto-clear error: {e}", file=sys.stderr)

def start_background_clear_thread(app):
    def run_clear_loop():
        while True:
            print("[Background] Running periodic clear...")
            clear_old_uploads_and_tasks(app)
            time.sleep(2 * 3600)  # Sleep 2 hours

    t = threading.Thread(target=run_clear_loop, daemon=True)
    t.start()
           
def create_app(app):
    BASE_URL = os.getenv("BASE_URL", "") # serv at root by default
    
    @app.before_request
    def verify_api_key():
        # root path and docs path are public
        if request.path == BASE_URL + '/' and request.method == 'GET' and len(request.path) == 1:
            return
        elif request.path == BASE_URL + '/docs' and request.method == 'GET' and len(request.path) == 5:
            return
        token = request.headers.get("Authorization")
        if not token:
            print("Missing Authorization header for route:", request.path, file=sys.stderr)
            return jsonify({"error": "Missing Authorization header"}), 401
        
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
        decoded = verify_jwt(token)
        if not decoded:
            print("Invalid or expired token")
            return jsonify({"error": "Invalid or expired token"}), 401

    @app.route(BASE_URL + '/process/file', methods=['POST'])
    def process_file_default():
        try:
            if queue_full():
                print("Task queue is full, cannot enqueue file processing task")
                return jsonify({"error": "Task queue is full"}), 503

            file_path = upload_file(request.files.get('file'))
            schema = request.form.get('form', example_schema)
            
            print(f"Processing file: {file_path} with schema: {schema}", file=sys.stderr)
            
            id = process_file_task.apply_async(args=[file_path, schema])
            return jsonify({"task_id": id.id}), 200
        except Exception as e:
            print(f"Error enqueuing file processing task: {e}")
            return jsonify({"error": str(e)}), 500

        
    @app.route(BASE_URL + '/process/home', methods=['POST'])
    def process_home_report():
        try:
            if queue_full():
                print("Task queue is full, cannot enqueue file processing task")
                return jsonify({"error": "Task queue is full"}), 503
            print(f"Incoming request: {request.files}, {request.form}, {request.headers}", file=sys.stderr)

            file_path = upload_file(request.files.get('file'))
            schema = request.form.get('form', default_home_form)
            
            id = process_home_task.apply_async(args=[file_path, schema])
            return jsonify({"task_id": id.id}), 200
        
        except Exception as e:
            print(f"Error enqueuing home report processing task: {e}")
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/process/appliance', methods=['POST'])
    def process_appliance_photo():
        try:
            
            if queue_full():
                return jsonify({"error": "Task queue is full"}), 503
            
            file_path = upload_file(request.files.get('file'))
            schema = request.form.get('form', default_appliance_form)
            # WIP!
            if os.getenv("VISION_MODE", "false").lower() == "true":
                id = process_vision_task.apply_async(args=[file_path, schema])
            else:
                id = process_file_task.apply_async(args=[file_path, schema])
                
            return jsonify({"task_id": id.id}), 200

        except Exception as e:
            print(f"Error enqueuing appliance photo processing task: {e}")
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/process/ocr', methods=['POST']) 
    def tika_process():                                       # consider changing this to a task
        # get the OCR result from Tika
        try:
            file_path = upload_file(request.files.get('file'))
            text = process_tika(file_path)
            print("Tika processing complete", file=sys.stderr)
            return jsonify(text), 200
        
        except ValueError as ve:
            print(f"Value error: {ve}", file=sys.stderr)
            return jsonify({"error": str(ve)}), 400
        except FileNotFoundError as fnfe:
            print(f"File not found: {fnfe}", file=sys.stderr)
            return jsonify({"error": str(fnfe)}), 404
        except Exception as e:
            print(f"Error processing with Tika: {e}", file=sys.stderr)
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/process/text', methods=['POST'])
    def plaintext_process():
        try:
           
            text = process_plaintext_task(request.json.get('message', ''), request.json.get('form', example_schema))
            return jsonify(text), 200
        except ValueError as ve:
            print(f"Value error: {ve}", file=sys.stderr)
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            print(f"Error processing plaintext file: {e}", file=sys.stderr)
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/chat', methods=['POST'])
    def chat_with_model():
        try:            
            text = chat(request.json.get('message', ''))
            return jsonify({"response": text}), 200
        except ValueError as ve:
            print(f"Value error: {ve}", file=sys.stderr)
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            print(f"Error processing chat request: {e}", file=sys.stderr)
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/tasks', methods=['GET'])
    def get_tasks():
        try:
            tasks = celery.control.inspect().active() or {}
            queued_tasks = celery.control.inspect().reserved() or {}
            return jsonify({
                "active_tasks": tasks,
                "queued_tasks": queued_tasks
            }), 200
        except Exception as e:
            print(f"Error retrieving tasks: {e}")
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/tasks/<task_id>', methods=['GET'])
    def get_task(task_id):
        try:
            task = celery.AsyncResult(task_id)
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
            print(f"Error retrieving task {task_id}: {e}", file=sys.stderr)
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/clear', methods=['POST'])
    def clear_uploads():
        try:
            clear_old_uploads_and_tasks(app.config['UPLOAD_FOLDER'], app.config['PROCESSING_FOLDER'])
            return jsonify({"message": "Cleared files and tasks older than 2 hours"}), 200

        except Exception as e:
            print(f"Error clearing uploads and tasks: {e}", file=sys.stderr)
            return jsonify({"error": str(e)}), 500
        
    @app.route(BASE_URL + '/', methods=['GET'])
    def index():
        return homePage(default_home_form, default_appliance_form, example_schema)

    @app.route(BASE_URL + '/docs', methods=['GET'])
    def docs():
        try:
            with open('flask_server/openapi_spec.yaml', 'r') as f: 
                openapispec = f.read()
            res = make_response(openapispec)
            res.mimetype = 'text/yaml'
            return res, 200
        except FileNotFoundError:
            return jsonify({"error": "OpenAPI specification file not found"}), 404
        except Exception as e:
            print(f"Error reading OpenAPI specification: {e}")
            return jsonify({"error": str(e)}), 500
            

if __name__ == '__main__':
    PORT = int(os.getenv("PORT", 8000))

    app = Flask(__name__)

    app.config['UPLOAD_FOLDER'] = '/app/work_dir/uploads' 
    app.config['PROCESSING_FOLDER'] = '/app/work_dir/processing'

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSING_FOLDER'], exist_ok=True)
    
    create_app(app)
    
    start_background_clear_thread(app)
    
    app.run(host='0.0.0.0', port=PORT)