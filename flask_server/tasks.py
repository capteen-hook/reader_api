from celery import Celery
from flask_server.celery import celery
import os
from dotenv import load_dotenv
import sys

load_dotenv()

from flask_server.tools.web_search import search_tavily
from flask_server.ai.prompts import fill_form, fill_home_form, fill_home_form_forward, fill_home_form_websearch, fill_appliance_form, default_home_form, default_appliance_form, example_schema
from flask_server.test_page import homePage
from flask_server.tools.utils import validate_file, validate_form, verify_jwt, upload_file
from flask_server.ai.process import process_tika, process_plaintext, home_loop, process_file
#from flask_server.ai.transformer_vision import process_vision
    

# Set a task queue limit
MAX_TASKS = int(os.getenv('MAX_TASKS', 30))

@celery.task
def process_file_task(file_path, schema=example_schema):
    processed_content = process_file(file_path, schema)
    return processed_content
    
@celery.task
def process_home_task(file_path, schema=default_home_form):
    text = process_tika(file_path)
    content = home_loop(text, schema)
    return content

@celery.task
def process_plaintext_task(file_path, schema=example_schema):
    content = process_plaintext(file_path, schema)
    return content

# @celery.task
# def process_vision_task(file_path, schema=default_appliance_form):
#     content = process_vision(file_path, schema)
#     return content

def queue_full():
    try:
        active_tasks = celery.control.inspect().active() or {}
        reserved_tasks = celery.control.inspect().reserved() or {}
        total_tasks = sum(len(tasks) for tasks in active_tasks.values()) + sum(len(tasks) for tasks in reserved_tasks.values())
        print(f"Total tasks in queue: {total_tasks}", file=sys.stderr)
        return total_tasks >= MAX_TASKS
    except Exception as e:
        print(f"Error checking task queue: {e}", file=sys.stderr)
        return True 
    