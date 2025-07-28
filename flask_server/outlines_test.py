
from outlines import from_ollama, Generator
from outlines.types import JsonSchema
import ollama
from PIL import Image
import torch
import torchvision.transforms as transforms
from pdf2image import convert_from_path
from outlines import Generator, from_transformers
import os
import gc
import sys
import json
from dotenv import load_dotenv
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

file = './basic_tests/pizza_recipe.txt'
file2 = './basic_tests/dishwasher.jpg'

example_schema = """{
    "$defs": {
        "Status": {
            "enum": ["success", "failure"],
            "title": "Status",
            "type": "string"
        }
    },
    "properties": {
        "status": {
            "$ref": "#/$defs/Status"
        },
        "response": {
            "type": "string"
        }
    },
    "required": ["status", "response"],
    "title": "Structured Response",
    "type": "object"
}"""

default_appliance_form = """{
    "properties": {
        "serial_number": {
            "type": "string"
        },
        "model_number": {
            "type": "string"
        },
        "manufacturer": {
            "type": "string"
        },
        "manufacture_date": {
            "type": "string",
            "format": "date"
        },
        "type": {
            "type": "string"
        }
    }
}"""

default_home_form = """{
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

# if __name__ == "__main__":
#     schema = JsonSchema(default_appliance_form)


#     client = ollama.Client()
#     model = from_ollama(client,"gemma3:4b")

#     text = open(file, 'r', encoding='utf-8').read()

#     prompt = "Fill out the following form based on the text: " + text

#     generator = Generator(model, schema)
#     result = generator(prompt)
#     print("Result:", result)

def load_model():
    print("CUDA available:", torch.cuda.is_available(), file=sys.stderr)
    try:
        print("Supports float16:", torch.cuda.get_device_capability()[0] >= 7)
        print("CUDA device:", torch.cuda.current_device(), file=sys.stderr)
        print("CUDA name:", torch.cuda.get_device_name(torch.cuda.current_device()), file=sys.stderr)
    except Exception as e:
        print(f"Error checking CUDA capabilities: {e}", file=sys.stderr)

    # lighter model:
    model_name = "Qwen/Qwen2-VL-7B-Instruct"
    model_class = Qwen2VLForConditionalGeneration
    processor_class = AutoProcessor

    print(f"Using model: {model_name}", file=sys.stderr)

    device = torch.device("cuda")
    dtype = torch.float16 if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 7 else torch.bfloat16
    
    # it will have to download the model, which might take a while.
    model_kwargs={"device_map": "auto", "torch_dtype": dtype}
    processor_kwargs={"device_map": "cpu"}
    tf_model = model_class.from_pretrained(model_name, **model_kwargs, cache_dir='./cache')
    tf_processor = processor_class.from_pretrained(model_name, **processor_kwargs, cache_dir='./cache', use_fast=True)

    print(f"Model {model_name} loaded successfully", file=sys.stderr)
    model_i = from_transformers(tf_model, tf_processor)

    return model_i, tf_processor, device, dtype

_model = None
_tf_processor = None
_device = None
_dtype = None

def get_model():
    global _model
    global _tf_processor
    global _device
    global _dtype
    if _model is None or _tf_processor is None or _device is None or _dtype is None:
        _model, _tf_processor, _device, _dtype = load_model()
        print(f"Model loaded: {_model}", file=sys.stderr)
    return _model, _tf_processor, _device, _dtype


def process_vision(file_path, schema):
    #file_path = replace_containerized_path(file_path)
    # replace the containerized file path with the actual file path
    
    _model_i, _tf_processor, _device, _dtype = get_model()
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"""
                        You are an AI assistant that summarizes images. Use the image to fill this form:
                        {default_appliance_form}
                    """
                },
                {"type": "image", "image": ""},
            ],
        }
    ]
    print(f"Processing image {file_path}", file=sys.stderr)
    
    image_summary_generator = Generator(_model_i, schema)
    
    prompt = _tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.ConvertImageDtype(_dtype),
    ])
    
    try:
        image = Image.open(file_path)
        
        print(f"Using generator prompt: {prompt}", file=sys.stderr)
        print(f"Using generator schema: {schema}", file=sys.stderr)
        
        result = image_summary_generator({"text": prompt, "images": image})

        print(f"Result from generator: {result}", file=sys.stderr)
       
        del image
        torch.cuda.empty_cache()
        gc.collect()
        print(f"Processed image {file_path}: {result}", file=sys.stderr)
        print(f"Result: {result}", file=sys.stderr)
        print(f"Result type: {type(result)}", file=sys.stderr)
    
        try:
            res = json.loads(result)
            return res
        except json.JSONDecodeError as e:
            return {
                "error": "Failed to parse JSON from the generator output.",
                "details": str(e),
                "result": result
            }
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        raise Exception(f"Error processing image {file_path}: {e}")
    
if __name__ == "__main__":
    file_path = file2 
    schema = JsonSchema(default_appliance_form)

    result = process_vision(file_path, schema)
    
    print("Result:", result)