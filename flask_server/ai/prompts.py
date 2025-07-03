
def fill_form(info: str, form: dict) -> str:
    return f"You are an assistant that helps read documents and fill out this form: \
    {form} \
    Please read the following document and extract the requested information: \
    {info} \
    Fill out the form as completely as possible, leaving any unspecified fields empty."
    
def fill_home_form(info: str, form: dict) -> str:
    return f"You are a real estate agent. Clients \
    send you home inspection reports from which you need to extract \
    the relevant information to fill out the home form. \
    Home forms have these fields: \
    {form} \
    Leave any unspecified fields empty. Here is the inspection report: \
    {info} \
    Fill out the home form as completely as possible."
    
def fill_home_form_forward(info: str, schema: dict, previous_result: dict) -> str:
    return f"You are a real estate agent. Clients \
    send you home inspection reports from which you need to extract \
    the relevant information to fill out the home form. \
    This information is already partially filled out: \
    {previous_result} \
    If you find any new or more accurate information, use it to fill out the home form: \
    {schema} \
    Leave any unspecified fields empty. Here is the inspection report: \
    {info}"
    
def fill_home_form_websearch(websearch_results: str, schema: dict, previous_result: dict) -> str:
    return f"You are a real estate agent. Clients \
    send you home inspection reports from which you need to extract \
    the relevant information to fill out the home form. \
    This information is already partially filled out: \
    {previous_result} \
    The top search results for the address are: \
    {websearch_results} \
    Add any additional information found in the web search results to the home form: \
    {schema}"

def fill_appliance_form(info: str, schema: dict) -> str:
    return f"You are a home inspection assistant. Home inspectors \
    send you photos of appliance manufacturer plates and you need to extract \
    the available information to fill out this appliance form: \
    {schema} \
    from the appliance manufacturer plate: \
    {info} \
    Fill out the appliance form as completely as possible, \
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