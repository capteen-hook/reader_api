import json

def homePage(default_home_form, default_appliance_form, test_text):
    return """
        <html>
            <head>
                <title>Flask Server</title>
                <script>
                    function showTab(tabId) {
                        document.querySelectorAll('div[id^="tab"]').forEach(div => {
                            div.style.display = 'none';
                        });
                        document.getElementById(tabId).style.display = 'block';
                    }
                </script>
            </head>
            <body>
                <div style="flex-direction: column; align-items: center; margin-top: 50px;">
                    <button onclick="showTab('tab1')">Upload File</button>
                    <button onclick="showTab('tab2')">Process PDF</button>
                    <button onclick="showTab('tab3')">Process Home Report</button>
                    <button onclick="showTab('tab4')">Process Appliance Photo</button>
                    <button onclick="showTab('tab5')">Process Text File</button>
                    <button onclick="showTab('tab6')">Process Image for OCR</button>
                </div>
                <div id="tab1" style="display:block;">
                    <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data" class="upload-form">
                    <h2>Upload File</h2>
                    <input type="file" name="file" required>
                    <br>
                    <input type="submit" value="Upload File">
                    </form>
                </div>
                <div id="tab2" style="display:none;">
                    <form id="processPdfForm" action="/process/pdf" method="post" class="process-form">
                    <h2>Process PDF</h2>
                    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
                    <textarea name="form" rows="10" cols="50" placeholder="Enter form data in JSON format">""" + default_home_form + """</textarea>
                    <br>
                    <input type="submit" value="Process PDF">
                    </form>
                </div>
                <div id="tab3" style="display:none;">
                    <form id="processHomeForm" action="/process/home" method="post" class="process-form">
                    <h2>Process Home Report</h2>
                    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
                    <textarea name="form" rows="10" cols="50" placeholder="Enter form data in JSON format">""" + default_home_form + """</textarea>
                    <br>
                    <input type="submit" value="Process Home Report">
                    </form>
                </div>
                <div id="tab4" style="display:none;">
                    <form id="processApplianceForm" action="/process/appliance" method="post" class="process-form">
                    <h2>Process Appliance Photo</h2>
                    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
                    <textarea name="form" rows="10" cols="50" placeholder="Enter form data in JSON format">""" + default_appliance_form + """</textarea>
                    <br>
                    <input type="submit" value="Process Appliance Photo">
                    </form>
                </div>
                <div id="tab5" style="display:none;">
                    <form id="processTxtForm" action="/process/txt" method="post" class="process-form">
                    <h2>Process Text File</h2>
                    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
                    <textarea name="form" rows="10" cols="50" placeholder="Enter form data in JSON format">""" + test_text + """</textarea>
                    <br>
                    <input type="submit" value="Process Text File">
                    </form>
                </div>
                <div id="tab6" style="display:none;">
                    <form id="processImageForm" action="/ocr" method="post" class="process-form">
                    <h2>Process Image for OCR</h2>
                    <input type="text" name="filename" placeholder="Enter uploaded filename" required>
                    <br>
                    <input type="submit" value="Process Image or PDF for OCR">
                    </form>
                </div>
                <script>
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

                    document.getElementById('tab1').style.display = 'block'; // Show the first tab by default
                </script>
            </body>
        </html>
        """