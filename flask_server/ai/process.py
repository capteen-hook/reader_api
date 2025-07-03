import os
import requests
import json
from dotenv import load_dotenv
import ollama
from outlines import from_ollama, Generator

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")
TIKA_URL = os.getenv("TIKA_URL", "http://localhost:9998/tika")

client = ollama.Client()
model = from_ollama(client, os.getenv("MODEL_NAME", "gemma3:4b"))

def home_loop(text, schema):
    
    # home inspection reports can be quite long, so we need to split them into chunks
    chunksize = 10000
    overlap = 200
    chunks = [text[i:i + chunksize] for i in range(0, len(text), chunksize - overlap)]
    results = []
    final_res = {}
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}")
        try:
            result = process_plaintext(chunk, schema, fill_home_form_forward(chunk, schema, final_res))
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            result = final_res.copy()  # Use the last valid result as a fallback
        
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
    address = final_res.get('address', '')
    if address and address != '':
        print("Performing web search for address:", address)
        search_results = search_tavily(address)
        
        try:
            final_res = process_plaintext(search_results, schema, fill_home_form_websearch(search_results, schema, final_res))
        except Exception as e:
            print(f"Error processing web search results: {e}")
        
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
    try:
        # Attempt to parse the result as JSON
        return json.loads(result)
    except json.JSONDecodeError as e:
        # Log the error and the problematic result
        print(f"Error decoding JSON: {e}")
        print(f"Result string: {result}")
        raise ValueError("Failed to parse JSON from the generator output.")
    