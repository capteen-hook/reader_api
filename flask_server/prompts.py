
def fill_form(info: str, form: dict) -> str:
    return f"You are an assistant that helps read documents and fill out this form: {form}. \
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


curl -X POST http://localhost:8000/process/tika \
     -H "Content-Type: application/json" \
     -d '{"filename": "report_easy.pdf", "form": "{"$defs": {"Status": {"enum": ["success", "failure"],"title": "Status","type": "string"}},"properties": {"status": {"$ref": "#/$defs/Status"},"response": {"type": "string"}},"required": ["status", "response"],"title": "Structured Response","type": "object"}"}'