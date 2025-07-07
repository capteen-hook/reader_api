import json
import html
import requests
import os
from dotenv import load_dotenv

boilerplate = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Flask Server</title>
    <style>
    {css_code}
    </style>
</head>
<body>  
    {ollama_active}
    {body_content}
</body>
<script>
{javascript_code}
</script>
"""

tab_container = """
<div style="text-align: center; margin-top: 20px; margin-left: auto; margin-right: auto; width: 80%; position: relative; z-index: 0;">
    <div style="margin-bottom: 20px; position: relative; z-index: 3;">
        {tab_buttons}
    </div>
    <div style="margin-left: auto; margin-right: auto; width: 80%; border: 1px solid #ccc; padding: 20px; border-radius: 5px;">
    {tabs}
    </div>
</div>
"""

tab_button = """
<button onclick="showTab('{tab_id}')" style="margin: 0 10px;">{tab_name}</button> 
"""

process_form = """
<div id="{tab_id}" style="display: none; z-index: 1; top: 50px; margin-left: auto; margin-right: auto; width: 80%; background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
    <h2>{tab_name}</h2>
    <form class="process-form" action="{action_url}" method="post">
    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
    <input type="text" name="auth" placeholder="Enter authentication token" required>
    <textarea name="form" rows="10" cols="50" placeholder="Enter form data in JSON format" style="white-space: pre-wrap;">{form_data}</textarea>
    <br>
    <input type="submit" value="Process File">
    </form>
</div>
"""

# this doesnt need a form field- just a filename
tika_process = """
<div id="tab7" style="display:none; z-index: 1; top: 50px; margin-left: auto; margin-right: auto; width: 80%; background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
    <h2>Tika OCR</h2>
    <form class="process-form" action="/process/tika" method="post">
    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
    <input type="text" name="auth" placeholder="Enter authentication token" required>
    <br>
    <input type="submit" value="Process File with Tika OCR">
    </form>
</div>
"""

# this just sends a get request to clear the uploads
clear_uploads = """
<div id="tab8" style="display:none; z-index: 1; top: 50px; margin-left: auto; margin-right: auto; width: 80%; background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
    <h2>Clear Uploads</h2>
    <form action="/clear" method="get" id="clearUploadsForm">
    <input type="text" name="auth" placeholder="Enter authentication token" required>
    <input type="submit" value="Clear Uploads">
    </form>
</div>
"""

script_show_tab = """
function showTab(tabId) {
    document.querySelectorAll('div[id^="tab"]').forEach(div => {
        div.style.display = 'none';
    });
    document.getElementById(tabId).style.display = 'block';
}
"""

script_form = """
document.querySelectorAll('.process-form').forEach(form => {
    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent default form submission
        console.log('Form submitted:', this); // Log the form for debugging
        const formData = new FormData(this);
        const jsonData = {};

        formData.forEach((value, key) => {
            if (key === 'form') {
                try {
                    jsonData[key] = JSON.parse(value); // Parse JSON from the form field
                } catch (e) {
                    alert('Invalid JSON format in form data');
                    return;
                }
            } else {
                jsonData[key] = value; // Add other fields like filename
            }
        });
        console.log('Sending JSON data:', jsonData); // Log the JSON data for debugging
        fetch(this.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Explicitly set content type
                'Authorization': 'Bearer ' + jsonData.auth // Include auth token in headers                
            },
            body: JSON.stringify(jsonData) // Send JSON object as request body
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            alert(JSON.stringify(data, null, 2)); // Display response data
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });
});
"""

script_button_auth = """
document.querySelectorAll('.button-form-auth').forEach(form => {
    form.addEventListener('submit', function(event) {
        console.log('Form submitted:', this); // Log the form for debugging
        event.preventDefault(); // Prevent default form submission
        const formData = new FormData(this);
        const authToken = formData.get('auth');
        if (!authToken) {
            alert('Authorization token is missing!');
            return;
        }
        fetch(this.action, {
            method: this.method,
            headers: {
                'Authorization': 'Bearer ' + authToken
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            alert(JSON.stringify(data, null, 2)); // Display response data
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });
});
"""

script_button_noauth = """
document.querySelectorAll('.button-form-noauth').forEach(form => {
    form.addEventListener('submit', function(event) {
        console.log('Form submitted:', this); // Log the form for debugging
        event.preventDefault(); // Prevent default form submission
        fetch(this.action, {
            method: this.method
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            alert(JSON.stringify(data, null, 2)); // Display response data
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });
});
"""

script_file_upload = """
document.querySelectorAll('.upload-form').forEach(form => {
    form.addEventListener('submit', function(event) {
        console.log('Form submitted:', this); // Log the form for debugging
        event.preventDefault(); // Prevent default form submission
        const formData = new FormData(this);
        const authToken = formData.get('auth');
        if (!authToken) {
            alert('Authorization token is missing!');
            return;
        }
        fetch(this.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken // Include auth token in headers         
            },
            body: formData // Send FormData object as request body
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            alert(JSON.stringify(data, null, 2)); // Display response data
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });
});
"""
        
# script_clear_uploads = """
# document.getElementById('clearUploadsForm').addEventListener('submit', function(event) {
#     event.preventDefault(); // Prevent the default form submission
#     const formData = new FormData(this);
#     // Retrieve the auth token from the form data
#     const authToken = formData.get('auth');
#     if (!authToken) {
#         alert('Authorization token is missing!');
#         return;
#     }
#     fetch(this.action, {
#         method: 'GET',
#         headers: {
#             'Authorization': 'Bearer ' + authToken // Include auth token in headers
#         }
#     })
#     .then(response => {
#         if (!response.ok) {
#             throw new Error(`HTTP error! status: ${response.status}`);
#         }
#         return response.json();
#     })
#     .then(data => {
#         alert(JSON.stringify(data, null, 2));
#     })
#     .catch(error => {
#         alert('Error: ' + error.message);
#     });
# });
# """

file_upload_form = """
<div id="{tab_id}" style="display: none; z-index: 1; top: 50px; margin-left: auto; margin-right: auto; width: 80%; background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
    <h2>{tab_name}</h2>
    <form class="upload-form" action="{action_url}" method="post" enctype="multipart/form-data">
    <input type="file" name="file" required>
    <input type="text" name="auth" placeholder="Enter authentication token" required>
    <br>
    <input type="submit" value="Upload File">
    </form>
</div>
"""

button_form_auth = """
<div id="{tab_id}" style="display: none; z-index: 1; top: 50px; margin-left: auto; margin-right: auto; width: 80%; background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
    <h2>{tab_name}</h2>
    <form action="{action_url}" method="{method}" class="button-form-auth">
    <input type="text" name="auth" placeholder="Enter authentication token" required>
    <br>
    <input type="submit" value="{tab_name}">
    </form>
</div>
"""

button_form_noauth = """
<div id="{tab_id}" style="display: none; z-index: 1; top: 50px; margin-left: auto; margin-right: auto; width: 80%; background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px;">
    <h2>{tab_name}</h2>
    <form action="{action_url}" method="{method}" class="button-form-noauth">
    <input type="submit" value="{tab_name}">
    </form>
</div>
"""

def file_upload_tab(tab_info):
    # similiar to process form but no text area for form data
    return file_upload_form.format(
        tab_id=tab_info["tab_id"],
        tab_name=tab_info["tab_name"],
        action_url=tab_info["action_url"]
    )

def button_tab(tab_info, auth=True, method='post'):
    if auth:
        return button_form_auth.format(
            tab_id=tab_info["tab_id"],
            tab_name=tab_info["tab_name"],
            action_url=tab_info["action_url"],
            method=method
        )            
    elif not auth:
        return button_form_noauth.format(
            tab_id=tab_info["tab_id"],
            tab_name=tab_info["tab_name"],
            action_url=tab_info["action_url"],
            method=method
        )
    else:
        return '<div>man i dont even know</div>'

def ollama_active_element(ollama_active):
    if ollama_active:
        return '<div style="color: green; font-weight: bold;">Ollama is active</div>'
    else:
        return '<div style="color: red; font-weight: bold;">Ollama is not active</div>'
    
def try_ollama():
        
    load_dotenv()
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1").split("/v1")[0]  # Ensure we only use the base URL
    print(f"Checking Ollama at {OLLAMA_URL}")
    
    try:
        response = requests.get(f"{OLLAMA_URL}")
        if response.status_code == 200:
            return True
        else:
            print(f"Ollama health check failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error checking Ollama health: {e}")
        return False


def homePage(default_home_form, default_appliance_form, default_form_data):
    # default_home_form = html.escape(default_home_form)
    # default_appliance_form = html.escape(default_appliance_form)
    # default_form_data = html.escape(default_form_data)
    # parse the json strings to ensure they are displayed correctly in the HTML
    default_home_form = json.dumps(json.loads(default_home_form), indent=4)
    default_appliance_form = json.dumps(json.loads(default_appliance_form), indent=4)
    default_form_data = json.dumps(json.loads(default_form_data), indent=4)
    
    # ollama health check:
    ollama_active = try_ollama()
    
    proccess_endpoints = [
        {
            "tab_id": "tab2",
            "tab_name": "Process File - Standard",
            "action_url": "/process/file",
            "form_data": default_form_data,
        },
        {
            "tab_id": "tab3",
            "tab_name": "Process Home - Multi page inspection reports",
            "action_url": "/process/home",
            "form_data": default_home_form,
        },
        {
            "tab_id": "tab4",
            "tab_name": "Process Appliance - Images of manufacturer labels",
            "action_url": "/process/appliance",
            "form_data": default_appliance_form,
        }
    ]
    tabs_b_source = [
        {
            "tab_id": "tab1",
            "tab_name": "Docs",
            "action_url": "/docs",
        },
        {
            "tab_id": "tab5",
            "tab_name": "OCR - Extract Text from files",
            "action_url": "/process/ocr",
        },
        {
            "tab_id": "tab6",
            "tab_name": "Tasks",
            "action_url": "/tasks"
        },
        {
            "tab_id": "tab7",
            "tab_name": "Clear Tasks and files",
            "action_url": "/clear"
        }
    ]
    
    tabs_all = tabs_b_source + proccess_endpoints
    
    tab_buttons = "".join(
        tab_button.format(tab_id=tab["tab_id"], tab_name=tab["tab_name"]) for tab in tabs_all
    )
    
    process_endpoints = [process_form.format(**endpoint) for endpoint in proccess_endpoints]
    
    tabs_b_source = [
        button_tab(tabs_b_source[0], auth=False, method='get'),  # Docs tab does not need auth
        file_upload_tab(tabs_b_source[1]),
        button_tab(tabs_b_source[2], auth=True, method='get'),  # Tasks tab requires auth
        button_tab(tabs_b_source[3], auth=True, method='post')  # Clear tab requires auth
    ]
    
    tabs_b_source[0] = tabs_b_source[0].replace('display: none;', 'display: block;')  # Show the first tab by default
    
    tabs_all = "".join(process_endpoints + tabs_b_source)

        
    body_content = tab_container.format(tab_buttons=tab_buttons, tabs=tabs_all)
    javascript_code = script_show_tab + script_form + script_file_upload + script_button_auth + script_button_noauth
    css_code = ""
    
    return boilerplate.format(
        ollama_active=ollama_active_element(ollama_active),
        javascript_code=javascript_code,
        css_code=css_code,
        body_content=body_content
    )