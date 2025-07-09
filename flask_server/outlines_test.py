
from outlines import from_ollama, Generator
from outlines.types import JsonSchema
import ollama

file = './basic_tests/pizza_recipe.txt'

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


schema = JsonSchema(default_appliance_form)


client = ollama.Client()
model = from_ollama(client,"gemma3:4b")

text = open(file, 'r', encoding='utf-8').read()

prompt = "Fill out the following form based on the text: " + text

generator = Generator(model, schema)
result = generator(prompt)
print("Result:", result)
