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

from transformers import AutoConfig


from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
# from transformers import LlavaForConditionalGeneration, LlavaProcessor

from flask_server.ai.prompts import default_appliance_form, default_home_form

load_dotenv()

def load_model():
    print("CUDA available:", torch.cuda.is_available(), file=sys.stderr, flush=True)
    try:
        print("Supports float16:", torch.cuda.get_device_capability()[0] >= 7)
        print("CUDA device:", torch.cuda.current_device(), file=sys.stderr, flush=True)
        print("CUDA name:", torch.cuda.get_device_name(torch.cuda.current_device()), file=sys.stderr, flush=True)
    except Exception as e:
        print(f"Error checking CUDA capabilities: {e}", file=sys.stderr, flush=True)
        
    model_name = "Qwen/Qwen2-VL-7B-Instruct"
    model_class = Qwen2VLForConditionalGeneration
    processor_class = AutoProcessor
    
    if os.getenv('GPU', 'True').lower() in ['true', '1', 'yes']:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 7:
            dtype = torch.float16
        else:
            dtype = torch.float32 
        print(f"Tried GPU: {torch.cuda.is_available()}, using device: {device}, dtype: {dtype}", file=sys.stderr, flush=True)
    else:
        device = torch.device("cpu")
        dtype = torch.float32
    # it will have to download the model, which might take a while.
    processor_kwargs={"device_map": "auto"}
    model_kwargs={"device_map": "auto", "torch_dtype": dtype}
    tf_model = model_class.from_pretrained(model_name, **model_kwargs, cache_dir='/app/workdir/cache')
    tf_processor = processor_class.from_pretrained(model_name, **processor_kwargs, cache_dir='/app/workdir/cache', use_fast=True)

    print(f"Model {model_name} loaded successfully", file=sys.stderr, flush=True)
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
        print(f"Model loaded: {_model}", file=sys.stderr, flush=True)
    return _model, _tf_processor, _device, _dtype

def convert_pdf_to_images(pdf_path, output_dir, dpi=120, fmt='PNG'):
    # Convert PDF to list of images
    if os.getenv('POPPLER_PATH', None) is None or os.getenv('POPPLER_PATH', '') == '':
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt=fmt
        )
    else:
        images = convert_from_path(
            pdf_path,
            dpi=dpi,
            fmt=fmt,
            poppler_path=os.getenv('POPPLER_PATH', None)  # Set Poppler path for windows- should be on the sys PATH on Linux/MacOS
        )
        
    imagenames = []
    
    os.makedirs(output_dir, exist_ok=True)
    for i, image in enumerate(images):
        path = os.path.join(output_dir, f'page_{i+1}.{fmt.lower()}')
        image.save(path)
        imagenames.append(path)

    del images  # Free up memory
    return imagenames

def process_vision_multiple(file_path, schema):
    
    _model_i, _tf_processor, _device, _dtype = get_model()

    if file_path.lower().endswith('.pdf'):
        imagenames = convert_pdf_to_images(file_path, output_dir='/app/workdir/processing')
    else:
        imagenames = [file_path]
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"""
                        You are an AI assistant that summarizes images. Use the image to fill this form:
                        {default_home_form}
                    """
                },
                {"type": "image", "image": ""},
            ],
        }
    ]
    
    page_summary_generator = Generator(_model_i, schema)
    
    prompt = _tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    results = []
    for imagename in imagenames:
        try:
            image = Image.open(imagename)
            
            result = page_summary_generator(
                {"text": prompt, "images": image},
                max_new_tokens=1024
            )
            
            print(f"Result from generator: {result}", file=sys.stderr, flush=True)
            
            results.append(result)
            
            del image
            torch.cuda.empty_cache()
            gc.collect()
        except Exception as e:
            print(f"Error processing image {imagename}: {e}")
            results.append({"error": str(e)})
        
    return results

def process_vision(file_path, schema):
    
    
    _model_i, _tf_processor, _device, _dtype = get_model()
    # ]
    
    
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
    print(f"Processing image {file_path}", file=sys.stderr, flush=True)
    
    image_summary_generator = Generator(_model_i, schema)
    
    prompt = _tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    # transform = transforms.Compose([
    #     transforms.ToTensor(),
    #     transforms.ConvertImageDtype(_dtype),
    # ])
    
    try:
        image = Image.open(file_path)
        
        
        
        print(f"Using generator prompt: {prompt}", file=sys.stderr, flush=True)
        print(f"Using generator schema: {schema}", file=sys.stderr, flush=True)
        
        result = image_summary_generator(
            {"text": prompt, "images": image},
            max_new_tokens=1024
        )

        print(f"Result from generator: {result}", file=sys.stderr, flush=True)
       
        del image
        torch.cuda.empty_cache()
        gc.collect()
        print(f"Processed image {file_path}: {result}", file=sys.stderr, flush=True)
        print(f"Result: {result}", file=sys.stderr, flush=True)
        print(f"Result type: {type(result)}", file=sys.stderr, flush=True)
        
        try:
            res = json.loads(result)
            print(f"Parsed JSON from generator output: {res}", file=sys.stderr, flush=True)
            return res
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from the generator output: {e}", file=sys.stderr, flush=True)
            return {
                "error": "Failed to parse JSON from the generator output.",
                "details": str(e),
                "result": result
            }
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        raise Exception(f"Error processing image {file_path}: {e}")