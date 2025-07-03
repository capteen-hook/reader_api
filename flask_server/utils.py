
import os
from dotenv import load_dotenv

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
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

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
    
def validate_form(form_data, default=example_schema):
    try:
        if not form_data:
            return default
        
        # Validate form data against the schema
        schema = JsonSchema(form_data)
        
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
