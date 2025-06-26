import json
import html

boilerplate = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Flask Server</title>
    <script>
    {javascript_code}
    </script>
    <style>
    {css_code}
    </style>
</head>
<body>
    {body_content}
</body>
"""

tab_container = """
<div style="display: flex; flex-direction: column; align-items: center; margin-top: 50px;">
    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
        {tab_buttons}
    </div>
    <div style="width: 80%; max-width: 800px; border: 1px solid #ccc; padding: 20px; border-radius: 5px;">
    {tabs}
    </div>
</div>
"""

tab_button = """
<button onclick="showTab('{tab_id}')" style="margin: 0 10px;">{tab_name}</button> 
"""

process_form = """
<div id="{tab_id}" style="display: none;">
    <h2>{tab_name}</h2>
    <form class="process-form" action="{action_url}" method="post">
    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
    <textarea name="form" rows="10" cols="50" placeholder="Enter form data in JSON format">{form_data}</textarea>
    <br>
    <input type="submit" value="Process File">
    </form>
    
</div>
"""

# this is different because the enctype must be multipart/form-data
upload_form = """  
<div id="tab1" style="display:block;">
    <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data" class="upload-form">
    <h2>Upload File</h2>
    <input type="file" name="file" required>
    <br>
    <input type="submit" value="Upload File">
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
        event.preventDefault();
        const formData = new FormData(this);
        const jsonData = {};

        formData.forEach((value, key) => {
            if (key === 'form') {
                try {
                    jsonData[key] = JSON.parse(value);
                } catch (e) {
                    alert('Invalid JSON format in form data');
                    return;
                }
            } else {
                jsonData[key] = value;
            }
        });

        fetch(this.action, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            alert(JSON.stringify(data, null, 2));
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });
});
"""

script_file_upload = """
document.getElementById('uploadForm').addEventListener('submit', function(event) {
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);

        fetch(this.action, {
            method: 'POST',
            body: formData // Send the FormData directly
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            alert(JSON.stringify(data, null, 2));
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });
});
"""


def homePage(default_home_form, default_appliance_form, default_form_data):
    default_home_form = html.escape(default_home_form)
    default_appliance_form = html.escape(default_appliance_form)
    default_form_data = html.escape(default_form_data)
    
    proccess_endpoint = [
        {
            "tab_id": "tab2",
            "tab_name": "Process PDF",
            "action_url": "/process/pdf",
            "form_data": default_form_data,
        },
        {
            "tab_id": "tab3",
            "tab_name": "Process Home",
            "action_url": "/process/home",
            "form_data": default_home_form,
        },
        {
            "tab_id": "tab4",
            "tab_name": "Process Appliance",
            "action_url": "/process/appliance",
            "form_data": default_appliance_form,
        },
        {
            "tab_id": "tab5",
            "tab_name": "Process txt file",
            "action_url": "/process/txt",
            "form_data": default_form_data,
        },
        {
            "tab_id": "tab6",
            "tab_name": "Process plain text",
            "action_url": "/process/text",
            "form_data": default_form_data,
        },
        {
            "tab_id": "tab7",
            "tab_name": "Process OCR",
            "action_url": "/process/tika",
            "form_data": default_form_data,
        }
    ]
    
    tabs_b_source = [
        {
            "tab_id": "tab1",
            "tab_name": "Upload File",
            "action_url": "/upload",
            "form_data": "",
        },
    ] + proccess_endpoint
    
    tab_buttons = "".join(
        tab_button.format(tab_id=tab["tab_id"], tab_name=tab["tab_name"]) for tab in tabs_b_source
    )

    
    tabs = "".join(
        process_form.format(
            tab_id=tab["tab_id"],
            tab_name=tab["tab_name"],
            action_url=tab["action_url"],
            form_data=json.dumps(tab["form_data"], indent=4)
        ) for tab in proccess_endpoint
    )
    
    tabs_all = upload_form + tabs
    
    body_content = tab_container.format(tab_buttons=tab_buttons, tabs=tabs_all)
    javascript_code = script_show_tab + script_form + script_file_upload
    css_code = ""
    
    return boilerplate.format(
        javascript_code=javascript_code,
        css_code=css_code,
        body_content=body_content
    )