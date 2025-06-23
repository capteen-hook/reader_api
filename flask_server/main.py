# server.py
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from flask import Flask, jsonify, request
from enum import Enum
from openai import AsyncOpenAI
from outlines import models, generate
from outlines.models.openai import OpenAIConfig
from werkzeug.utils import secure_filename
from PIL import Image
import requests
import asyncio
import sys

# Load environment variables
import os
from dotenv import load_dotenv
load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998/tika")
PORT = int(os.getenv("PORT", 8000))

def fill_form(info: str) -> str:
    return f"You are an assistant that helps read documents. \
    Please read the following document and extract the requested information: \
    {info}. Fill out the form as completely as possible, leaving any unspecified fields empty."
    
def fill_home_form(info: str) -> str:
    return f"You are a property manager. Clients \
    send you inspection reports from which you need to extract \
    the relevant information to fill out the home form. \
    Home forms have information about the home, such as address, \
    type (e.g., apartment, detached, semi-detached, terraced), \
    year built, square footage, number of floors, number of bathrooms, etc. \
    Leave any unspecified fields empty. Here is the inspection report: {info} \
    Fill out the home form as completely as possible."

def fill_appliance_form(info: str) -> str:
    return f"You are a home inspection assistant. Home inspectors \
    send you photos of appliance manufacturer plates and you need to extract \
    the relevant information to fill out the appliance form. Here is the information \
    from the appliance manufacturer plate: {info}. Fill out the appliance form as completely as possible, \
    leaving any unspecified fields empty."
    
default_home_form = {
    "address": "string",
    "latlon": "array[float]",
    "year_built": "string",
    "square_footage": "integer",
    "bedrooms": "integer",
    "bathrooms": "integer",
    "pool": "boolean",
    "garage": "boolean"
}

default_appliance_form = {
    "serial_number": "string",
    "manufacturer": "string",
    "type": "string"
}

home_schema = """{
    "properties": {
        "address": {
            "type": "string"
        },
        "bedrooms": {
            "type": "integer"
        },
        "bathrooms": {
            "type": "integer"
        },
        "square_footage": {
            "type": "integer"
        },
        "year_built": {
            "type": "integer"
        },
        "type": {
            "type": "string"
        },
        "stories": {
            "type": "integer"
        },
        "basement": {
            "type": "boolean"
        },
        "garage": {
            "type": "boolean"
        },
        "pool": {
            "type": "boolean"
        },
        "roof_type": {
            "type": "string"
        },
        "location": {
            "type": "string"
        }
    },
    "required": ["address", "type"],
    "title": "Home",
    "type": "object"
}"""
def parse_form(form: dict) -> dict:
    # outlines needs a format like home_schema
    formatted_form = """{
        "properties": {
    """
    for key, value in form.items():
        if isinstance(value, str):
            value_type = "string"
        elif isinstance(value, int):
            value_type = "integer"
        elif isinstance(value, float):
            value_type = "number"
        elif isinstance(value, bool):
            value_type = "boolean"
        elif isinstance(value, list):
            value_type = "array"
        else:
            value_type = "string"
        formatted_form += f'"{key}": {{ "type": "{value_type}" }},\n'
    formatted_form += """
        }
        "required": [],
        "title": "Form",
        "type": "object"
    }"""
    
    return formatted_form    

def pdf_tika_ocr(file_path: str) -> str:
        headers = {
            'Content-Type': 'application/pdf',
            'Accept': 'text/plain'
        }
            
        with open(file_path, 'rb') as f:
            pdf_data = f.read()
        response = requests.put(TIKA_URL, data=pdf_data, headers=headers)
        if response.status_code == 200:
            file_content = response.text
            return file_content
        else:
            raise Exception(f"Error processing PDF: {response.status_code} - {response.text}")

def image_tesseract_ocr(file_path: str) -> str:
    headers = {
        'Content-Type': 'application/octet-stream',
        'Accept': 'text/plain'
    }
    with open(file_path, 'rb') as f:
        image_data = f.read()
    response = requests.put(TIKA_URL, data=image_data, headers=headers)
    if response.status_code == 200:
        file_content = response.text
        return file_content
    else:
        raise Exception(f"Error processing image: {response.status_code} - {response.text}")

def convert_to_png(input_path, output_path):
    # Open the image file
    with Image.open(input_path) as img:
        # Save the image as PNG
        img.save(output_path, format="PNG")
    print(f"Image converted to PNG and saved at {output_path}")

def ollama(form):
    model = models.openai(
        "gemma3:4b",
        base_url="http://localhost:11434/v1",
        api_key='ollama'
    )

    async def generate_async(prompt):
        return await generate.json(model, form, prompt)

    def generate_sync(prompt):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Use asyncio.run_coroutine_threadsafe if already in an event loop
            future = asyncio.run_coroutine_threadsafe(generate_async(prompt), loop)
            return future.result()
        else:
            return asyncio.run(generate_async(prompt))

    return generate_sync

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/pdf', methods=['POST'])
def upload_pdf():
    try:
        file = request.files.get('file')
        form_data = request.json.get('form', {})
        
        # if form data is empty, return an error        
        if not file or not form_data:
            return jsonify({"error": "Invalid file or form data"}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # OCR the file
        text = pdf_tika_ocr(file_path)
        # get the generator
        generator = ollama(parse_form(form_data))
        # Generate the response
        content = generator(fill_form(text))
        
        return jsonify(content), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/home', methods=['POST'])
def upload_home_report():
    try:
        file = request.files.get('file')
        form_data = request.json.get('form', {})
        
        # if no form data is provided, use default form
        if not form_data:
            form_data = default_home_form
        
        if not file:
            return jsonify({"error": "Invalid file or form data"}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # OCR the file
        text = pdf_tika_ocr(file_path)
        # get the generator
        generator = ollama(parse_form(form_data))
        # Generate the response
        content = generator(fill_home_form(text))
        
        return jsonify(content), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/appliance', methods=['POST'])
def upload_appliance_photo():
    try:
        file = request.files.get('file')
        form_data = request.json.get('form', {})
        
        # if no form data is provided, use default form
        if not form_data:
            form_data = default_appliance_form
        
        if not file:
            return jsonify({"error": "Invalid file or form data"}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # convert the image to PNG if it's not already
        if not filename.lower().endswith('.png'):
            png_path = os.path.splitext(file_path)[0] + '.png'
            convert_to_png(file_path, png_path)
            file_path = png_path
        
        # ocr the image
        text = image_tesseract_ocr(file_path)
        # get the generator
        generator = ollama(parse_form(form_data))
        # Generate the response
        content = generator(fill_appliance_form(text))
        
        return jsonify(content), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)