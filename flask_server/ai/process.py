import os
import requests
import json
from dotenv import load_dotenv
import ollama
from outlines import from_ollama, Generator
from flask_server.ai.prompts import example_schema, fill_form, fill_home_form_forward, fill_home_form_websearch, default_home_form, default_appliance_form
from flask_server.tools.utils import validate_file, validate_form, verify_jwt, upload_file
from flask_server.tools.web_search import search_tavily
from flask_server.ai.transformer_vision import process_vision
import sys

load_dotenv()

def replace_containerized_path(file_path):
    this = '/app/workdir/'
    with_this = '/home/liam/reader_api/workdir/'
    if file_path.startswith(this):
        file_path = file_path.replace(this, with_this)
    return file_path

def create_ollama_client():
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    #OLLAMA_URL = "http://localhost:11434" 

    # try to request the OLLAMA_URL 

    print(f"Using OLLAMA_URL: {OLLAMA_URL}")

    res = requests.get(OLLAMA_URL + "/v1/models")


    client = ollama.Client(host=OLLAMA_URL, timeout=120)
    model = from_ollama(client, os.getenv("MODEL_NAME", "gemma3:4b"))
    return model, client
    
_model = None
_client = None

def get_model():
    global _model
    global _client
    if _model is None or _client is None:
        _model, _client = create_ollama_client()
        print(f"Model loaded: {_model}", file=sys.stderr)
    return _model, _client

def process_file(file_path, schema=example_schema):
    #file_path = replace_containerized_path(file_path)
    
    _model, _client = get_model()
    
    try:
        schema = validate_form(schema)
        
        if file_path.split('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'webp']:
            # For image files, we can use vision processing
            # but for now- just try and get text from it with Tika
            result = process_vision(file_path, schema)
            
            try:
                # Attempt to parse the result as JSON
                return json.loads(result)
            except json.JSONDecodeError as e:
                # Log the error and the problematic result
                print(f"Error decoding JSON: {e}")
                print(f"Result string: {result}")
                raise ValueError("Failed to parse JSON from the generator output.")
            
        else:
            # For PDF files, use Tika to extract text
            text = process_tika(file_path)
                
            if not text:
                raise ValueError("No text extracted from the file")
            
            if not schema:
                raise ValueError("Invalid form schema provided")
            
            prompt = fill_form(text, schema)
        
            generator = Generator(_model, schema)
            # Process the text with the prompt
            result = generator(prompt)
            try:
                # Attempt to parse the result as JSON
                return json.loads(result)
            except json.JSONDecodeError as e:
                # Log the error and the problematic result
                print(f"Error decoding JSON: {e}")
                print(f"Result string: {result}")
                raise ValueError("Failed to parse JSON from the generator output.")
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        raise Exception(f"Error processing file {file_path}: {e}")

def home_loop(text, schema):
    schemaF = validate_form(schema)
    
    # home inspection reports can be quite long, so we need to split them into chunks
    chunksize = 10000
    overlap = 200
    chunks = [text[i:i + chunksize] for i in range(0, len(text), chunksize - overlap)]
    results = []
    final_res = {}
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        try:
            result = process_plaintext(chunk, schema, fill_home_form_forward(chunk, schemaF, final_res))
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            result = final_res.copy()  # Use the last valid result as a fallback
        
        # try and merge the result with the final result- deferring to the new result 
        # print the type of final res
        for key, value in final_res.items():
            # if result does not have the key, add it
            if key not in result:
                result[key] = value
        
        results.append(result)
        final_res = result
    # do a web search for the address if it exists
    address = final_res.get('address', '')
    if address and address != '':
        search_results = search_tavily(address)
        
        try:
            final_res = process_plaintext(search_results, schema, fill_home_form_websearch(search_results, schemaF, final_res))
        except Exception as e:
            print(f"Error processing web search results: {e}")
        
        
    return final_res

def process_tika(file_path):
    
    TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998/tika")
    #TIKA_URL = "http://localhost:9998/tika"
    
    
    if file_path.endswith('.pdf'):
        content_type = 'application/pdf'
    elif file_path.endswith('.png') or file_path.endswith('.jpg') or file_path.endswith('.jpeg') or file_path.endswith('.webp'):
        content_type = 'image/' + file_path.split('.')[-1]
    elif file_path.endswith('.txt') or file_path.endswith('.md') or file_path.endswith('.csv') or file_path.endswith('.json') or file_path.endswith('.yaml'):
        # no need for tika
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        raise ValueError("Unsupported file type. Only PDF and image, and text files are supported. File was of type: " + file_path.split('.')[-1])
            
            
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
        
        print("Full Tika response::")
        print(response.text)
        return response.text
    
def process_plaintext(text, schema, prompt=None):
    _model, _client = get_model()
    
    schema = validate_form(schema)
    
    if prompt is None:
        prompt = fill_form(text, schema)
    generator = Generator(_model, schema)
    # Process the text with the prompt
    result = generator(prompt)    
    try:
        # Attempt to parse the result as JSON
        return json.loads(result)
    except json.JSONDecodeError as e:
        # Log the error and the problematic result
        print(f"Error decoding JSON: {e}")
        print(f"Result string: {result}")
        raise ValueError("Failed to parse JSON from the generator output.")
    
def chat(text):
    _model, _client = get_model()
    
    try:
        response = _client.chat(
            model=os.getenv("MODEL_NAME", "gemma3:4b"),
            messages=[{"role": "user", "content": text}]
        )
        
        return response['message']['content']
    except Exception as e:
        print(f"Error during chat processing: {e}")
        raise Exception(f"Error during chat processing: {e}")        
    
if __name__ == "__main__":
    try:
        content = process_file("../../basic_tests/pizza_recipe.txt")
        print("Processed content:", content)
    except Exception as e:
        print(f"Error processing file: {e}")
        raise e