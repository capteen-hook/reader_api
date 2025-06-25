# server.py
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from PIL import Image
import requests
import os
from dotenv import load_dotenv
from outlines import from_ollama, Generator, from_transformers
from outlines.types import JsonSchema
import ollama
from pdf2image import convert_from_path
import torch

from flask_server.prompts import (fill_form, fill_home_form, fill_appliance_form, default_home_form, default_appliance_form, example_schema)
from flask_server.test_page import homePage

from transformers import LlavaForConditionalGeneration, LlavaProcessor
import torchvision.transforms as transforms


model_name="mistral-community/pixtral-12b"
model_class=LlavaForConditionalGeneration
processor_class = LlavaProcessor

load_dotenv()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998/tika")
PORT = int(os.getenv("PORT", 8000))

client = ollama.Client()
model = from_ollama(client, os.getenv("MODEL_NAME", "gemma3:4b"))

# it will have to download the model, which might take a while.
model_kwargs={"device_map": "auto", "torch_dtype": torch.bfloat16}
processor_kwargs={"device_map": "cpu"}
tf_model = model_class.from_pretrained(model_name, **model_kwargs, cache_dir=os.getenv("TRANSFORMERS_CACHE", "./cache"))
tf_processor = processor_class.from_pretrained(model_name, **processor_kwargs, cache_dir=os.getenv("TRANSFORMERS_CACHE", "./cache"))

model_i = from_transformers(tf_model, tf_processor)

def convert_pdf_to_images(pdf_path, output_dir=None, dpi=120, fmt='PNG'):
    # Convert PDF to list of images
    print(f"Converting PDF {pdf_path} to images in {output_dir}")
    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        fmt=fmt,
        poppler_path='C:\\Program Files\\Poppler\\poppler-24.08.0\\Library\\bin',
    )

    # Optionally save images
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for i, image in enumerate(images):
            image.save(os.path.join(output_dir, f'page_{i+1}.{fmt.lower()}'))

    return images

def process_vision(file_path, form_data):
    """
    Process a file using the Ollama model and return structured content.

    Args:
        file_path: Path to the file to process
        form_data: Form data to fill in the template
    Returns:
        List of structured content extracted from the file
    """

    if file_path.lower().endswith('.pdf'):
        # conver to list of images
        images = convert_pdf_to_images(file_path, output_dir=app.config['PROCESSING_FOLDER'])
    else:
        # file is an image
        images = [Image.open(file_path)]
    
    # Define a transformation pipeline to convert images to tensors
    transform = transforms.Compose([
        transforms.ToTensor(),  # Convert PIL image to tensor
        transforms.ConvertImageDtype(torch.bfloat16),  # Convert tensor dtype to bfloat16
    ])
    
    
    messages = [
        {
            "role": "user",
            "content": [
                # The text you're passing to the model --
                # this is where you do your standard prompting.
                {"type": "text", "text": f"""
                    {fill_form("Use the image", form=form_data)}
                    """
                },

                # This a placeholder, the actual image is passed in when
                # we call the generator function down below.
                {"type": "image", "image": ""},
            ],
        }
    ]
    
    page_summary_generator = Generator(model_i, JsonSchema(form_data))
    
    # Convert the messages to the final prompt
    prompt = tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    
    results = []
    for image in images:
        image_tensor = transform(image).to("cuda" if torch.cuda.is_available() else "cpu")
        result = page_summary_generator({"text": prompt, "images": image})
        print(result)
        results.append(result)
        
    print("Processed results:", results)
        
    return results

def process_plaintext(text, form_data):
    prompt = fill_form(text, form=form_data)
    print("Processing text with prompt:", prompt)
    schema = JsonSchema(form_data)
    print("Using schema for text processing:", schema)
    generator = Generator(model, schema)
    print("Processing text with generator:", generator)
    # Process the text with the prompt
    result = generator(prompt)
    
    print("Processed text result:", result)
    
    return result

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/uploads'
app.config['PROCESSING_FOLDER'] = os.getenv('WORK_DIR', './work_dir') + '/processing'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSING_FOLDER'], exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        print("Received file upload request: ", request.files)
        file = request.files.get('file')
        if not file:
            print("No file provided")
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
        filename = request.json.get('filename')
        form_data = request.json.get('form')
        
        if not filename or not form_data:
            return jsonify({"error": "Invalid filename or form data"}), 400
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        content = process_vision(file_path, form_data)
        
        return jsonify(content), 200
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/process/home', methods=['POST'])
def process_home_report():
    try:
        filename = request.json.get('filename')
        form_data = request.json.get('form', default_home_form)
        
        if not filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
      
        content = process_vision(file_path, form_data)
        
        return jsonify(content), 200
    except Exception as e:
        print(f"Error processing home report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/process/appliance', methods=['POST'])
def process_appliance_photo():
    try:
        filename = request.json.get('filename')
        form_data = request.json.get('form', default_appliance_form)
        
        if not filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
       
        content = process_vision(file_path, form_data)
        
        return jsonify(content), 200
    except Exception as e:
        print(f"Error processing appliance photo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/process/txt', methods=['POST'])
def process_txt():
    print("Got request to process: ", request.json)
    try:
        filename = request.json.get('filename')
        form_data = request.json.get('form')
        
        if not filename or not form_data:
            return jsonify({"error": "Invalid filename or form data"}), 400
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        with open(file_path, 'r') as f:
            text = f.read()
    
        content = process_plaintext(text, form_data)
        
        return jsonify(content), 200        
    except Exception as e:
        print(f"Error processing text file: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/process/text', methods=['POST'])
def process_text():
    try:
        text = request.json.get('text')
        form_data = request.json.get('form')
        
        if not text or not form_data:
            return jsonify({"error": "Invalid text or form data"}), 400
        
        content = process_plaintext(text, form_data)
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)