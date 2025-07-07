# VERY VERY COMPUTE INTENSIVE, currenntly disabled

from PIL import Image
import torch
import torchvision.transforms as transforms
from pdf2image import convert_from_path
from outlines import Generator, from_transformers
import os
import gc
from flask_server.prompts import fill_form
from dotenv import load_dotenv

load_dotenv()

if os.getenv("LIGHTWEIGHT_MODEL", "True").lower() in ["true", "1", "yes"]:
    # heavyweight model:
    from transformers import LlavaForConditionalGeneration, LlavaProcessor
    model_name="mistral-community/pixtral-12b"
    model_class=LlavaForConditionalGeneration
    processor_class = LlavaProcessor
else:
    # lighter model:
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    model_name = "Qwen/Qwen2-VL-7B-Instruct"
    model_class = Qwen2VLForConditionalGeneration
    processor_class = AutoProcessor

device = torch.device("cuda")
dtype = torch.float32
# it will have to download the model, which might take a while.
model_kwargs={"device_map": "auto", "torch_dtype": dtype}
processor_kwargs={"device_map": "gpu"}
tf_model = model_class.from_pretrained(model_name, **model_kwargs, cache_dir=os.getenv("TRANSFORMERS_CACHE", "./cache"))
tf_processor = processor_class.from_pretrained(model_name, **processor_kwargs, cache_dir=os.getenv("TRANSFORMERS_CACHE", "./cache"))

model_i = from_transformers(tf_model, tf_processor)

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

    if file_path.lower().endswith('.pdf'):
        # conver to list of images
        imagenames = convert_pdf_to_images(file_path, output_dir=os.getenv('WORK_DIR', './work_dir') + '/processing')
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
    
    page_summary_generator = Generator(model_i, schema)
    
    # Convert the messages to the final prompt
    prompt = tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.ConvertImageDtype(dtype),
    ])
    
    results = []
    for imagename in imagenames:
        try:
            image = Image.open(imagename)
            
            # image_tensor = transform(image).to(device=device, dtype=dtype)
            # result = page_summary_generator({"text": prompt, "images": image_tensor})
            result = page_summary_generator({"text": prompt, "images": [image]})
            results.append(result)
            
            # Free up memory
            #del image_tensor
            del image
            torch.cuda.empty_cache()
            gc.collect()
        except Exception as e:
            print(f"Error processing image {imagename}: {e}")
            results.append({"error": str(e)})
        
    return results

def process_vision(file_path, schema):
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
    
    image_summary_generator = Generator(model_i, schema)
    
    prompt = tf_processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.ConvertImageDtype(dtype),
    ])
    
    try:
        image = Image.open(file_path)
        
        result = image_summary_generator({"text": prompt, "images": [image]})
        
        del image
        torch.cuda.empty_cache()
        gc.collect()
        
        return result
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        raise Exception(f"Error processing image {file_path}: {e}")