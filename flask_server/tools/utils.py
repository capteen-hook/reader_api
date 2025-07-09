import os
import jwt
from dotenv import load_dotenv
from flask_server.ai.prompts import example_schema
from outlines.types import JsonSchema
from werkzeug.utils import secure_filename
import sys

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key") 

def validate_file(filename):
    try:
        # Validate filename
        filename = request.json.get('filename')
        if not filename:
            print("Filename is missing in request")
            raise ValueError("Filename is required")

        # Sanitize filename
        filename = secure_filename(filename)
        file_path = os.path.join('/app/workdir/uploads', filename)

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File {filename} not found in upload folder")
            raise FileNotFoundError(f"File {filename} not found in upload folder")
        
        return file_path
    except ValueError as ve:
        raise ve
    except FileNotFoundError as fnfe:
        raise fnfe
    except Exception as e:
        print(f"Error validating file: {e}")
        raise Exception("Error validating file")
    
def validate_form(form_data):
    try:
        
        # if form_data is a string, parse it as JSON
        if isinstance(form_data, str):
            import json
            form_data = json.loads(form_data)
            
        
        # Validate form data against the schema
        schema = JsonSchema(form_data)
        
        # print the type of the schema
        # print the type of the schema's schema attribute
        
        # print("Validating form data against schema:", schema)
        # print("Schema content:", json.loads(schema.schema))
        # If validation passes, return the schema
        return schema
    except Exception as e:
        print(f"Error validating form data: {e}")
        raise ValueError("Invalid form data")
        
def verify_jwt(token):
    try:
        # Decode the JWT token
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def upload_file(file):
    try:
        if not file:
            raise ValueError("No file part in the request")
        
        filename = secure_filename(file.filename)
        file_path = os.path.join('/app/workdir/uploads', filename)
        file.save(file_path)
        
        return file_path
    
    except Exception as e:
        print(f"Error uploading file: {e}", file=sys.stderr)
        raise Exception("Error uploading file")