# VERY VERY COMPUTE INTENSIVE, currenntly disabled

from PIL import Image
import torch
import torchvision.transforms as transforms
from pdf2image import convert_from_path
from outlines import Generator, from_transformers
import os
import gc
from flask_server.ai.prompts import fill_form
import sys
from dotenv import load_dotenv

load_dotenv()

def replace_containerized_path(file_path):
    this = '/app/workdir/'
    with_this = '/home/liam/reader_api/workdir/'
    if file_path.startswith(this):
        file_path = file_path.replace(this, with_this)
    return file_path

def load_model():
    print("CUDA available:", torch.cuda.is_available(), file=sys.stderr)
    print("Supports float16:", torch.cuda.get_device_capability()[0] >= 7)
    print("CUDA device:", torch.cuda.current_device(), file=sys.stderr)
    print("CUDA name:", torch.cuda.get_device_name(torch.cuda.current_device()), file=sys.stderr)

    if os.getenv("LIGHTWEIGHT_MODEL", "True").lower() in ["true", "1", "yes"]:
        # lighter model:
        from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
        model_name = "Qwen/Qwen2-VL-7B-Instruct"
        model_class = Qwen2VLForConditionalGeneration
        processor_class = AutoProcessor
    else:
        # heavyweight model:
        from transformers import LlavaForConditionalGeneration, LlavaProcessor
        model_name="mistral-community/pixtral-12b"
        model_class=LlavaForConditionalGeneration
        processor_class = LlavaProcessor

    print(f"Using model: {model_name}", file=sys.stderr)
    device = torch.device("cuda")
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    # it will have to download the model, which might take a while.
    model_kwargs={"device_map": "auto", "torch_dtype": dtype}
    processor_kwargs={"device_map": "gpu"}
    tf_model = model_class.from_pretrained(model_name, **model_kwargs, cache_dir='/home/liam/reader_api/workdir/cache')
    tf_processor = processor_class.from_pretrained(model_name, **processor_kwargs, cache_dir='/home/liam/reader_api/workdir/cache', use_fast=True)

    print(f"Model {model_name} loaded successfully", file=sys.stderr)
    model_i = from_transformers(tf_model, tf_processor)

    return model_i, tf_processor, device, dtype

_model = None
_tf_processor = None
_device = None
_dtype = None

def get_model():
    global _model
    if _model is None or _tf_processor is None or _device is None or _dtype is None:
        _model, _tf_processor, _device, _dtype = load_model()
        print(f"Model loaded: {_model}", file=sys.stderr)
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
    file_path = replace_containerized_path(file_path)
    
    _model_i, _tf_processor, _device, _dtype = get_model()

    if file_path.lower().endswith('.pdf'):
        # conver to list of images
        imagenames = convert_pdf_to_images(file_path, output_dir='/home/liam/reader_api/workdir/processing')
    else:
        # file is an image
        imagenames = [file_path]
    
    messages = [
        {
            "role": "user",
            "content": [
                # The text you're passing to the model --
                # this is where you do your standard prompting.
                {"type": "text", "text": f"""
                    {fill_form("Use the image", schema)}
                    """
                },

                # This a placeholder, the actual image is passed in when
                # we call the generator function down below.
                {"type": "image", "image": ""},
            ],
        }
    ]
    
    page_summary_generator = Generator(_model_i, schema)
    
    # Convert the messages to the final prompt
    prompt = _tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.ConvertImageDtype(_dtype),
    ])
    
    results = []
    for imagename in imagenames:
        try:
            image = Image.open(imagename)
            
            image_tensor = transform(image).to(device=_device, dtype=_dtype)
            result = page_summary_generator({"text": prompt, "images": image_tensor})
            #result = page_summary_generator({"text": prompt, "images": [image]})
            results.append(result)
            
            # Free up memory
            del image_tensor
            del image
            torch.cuda.empty_cache()
            gc.collect()
        except Exception as e:
            print(f"Error processing image {imagename}: {e}")
            results.append({"error": str(e)})
        
    return results

def process_vision(file_path, schema):
    file_path = replace_containerized_path(file_path)
    # replace the containerized file path with the actual file path
    
    
    _model_i, _tf_processor, _device, _dtype = get_model()
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"""
                    {fill_form("Use the image", schema)}
                    """
                },
                {"type": "image", "image": ""},
            ],
        }
    ]
    print(f"Processing image {file_path} with schema {schema}", file=sys.stderr)
    
    image_summary_generator = Generator(_model_i, schema)
    
    prompt = _tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.ConvertImageDtype(_dtype),
    ])
    
    print(f"Transform composed", file=sys.stderr)
    
    try:
        image = Image.open(file_path)
        
        print(f"Starting generation for image {file_path}", file=sys.stderr)
        
        #result = image_summary_generator({"text": prompt, "images": [image]})
        image_tensor = transform(image).to(device=_device, dtype=_dtype)
        result = page_summary_generator({"text": prompt, "images": image_tensor})
        
        print(f"Image processed successfully", file=sys.stderr)
        
        del image
        torch.cuda.empty_cache()
        gc.collect()
        print(f"Processed image {file_path}: {result}", file=sys.stderr)
        return result
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        raise Exception(f"Error processing image {file_path}: {e}")