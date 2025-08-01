# reader_api

This API uses LLMs with structured generation to read files and format their content. A [JSON object Schema](https://json-schema.org/learn/getting-started-step-by-step) is used to define the structure of the output, so that you can prompt the LLM for specific fields. I would reccomend going easy on the 'required' option, as too many required fields can lead to hallucination.

The different /process/ endpoints use different models/prompts:

/process/file: standard, uses tika OCR if the file is not plaintext, and then a single prompt to process the file.

/process/home: similar to /process/file, but the prompt is more tailored, and it breaks down pdfs into pages, so that the LLM can process them in chunks. Finally, it does an internet search for the address and adds the result to the output.

/process/appliance: uses a vision model to process images of appliances manufacturer labels. this is pretty computationally intensive, so it may fail if overloaded.

# example

curl -s -i -X POST \
-H "Authorization: Bearer API_KEY" \
-F "file=@report.pdf" \
-F "schema=@schema.json" \
"https://shipshape.companionintelligence.org/process/home"

curl -s -i -X GET \
-H "Authorization: Bearer API_KEY" \
"https://shipshape.companionintelligence.org/tasks/YOUR_TASK_ID_FROM_PREVIOUS_STEP"

## requirements:

ollama: this server accesses ollama on localhost by default, edit in [.env](/flask_server/.env) 

tika: not implemented yet, but this will be an alternative to using a vision model. edit the tika path in the [.env](/flask_server/.env)

pdf2image requires poppler: if you cannot run the command `pdfinfo` in your terminal, you need to install poppler / supply the poppler path in the [.env](/flask_server/.env) file.

python 3.13: i used [astral uv](https://docs.astral.sh/uv/getting-started/installation/) as the package manager

## .env  

rename [.env.template](/flask_server/.env.template) to [.env](/flask_server/.env) and edit the variables as needed

OLLAMA_URL: the url of your ollama server, default is `http://localhost:11434`

TIKA_PATH: the path to your tika server, default is `http://localhost:9998` (not implemented yet)

TRANSFORMERS_CACHE: the path where the vision model will be stored

WORRK_DIR: the path where the files will be stored for processing, default is `./work_dir`

MODEL_NAME: the ollama model to use, default is `gemma3:4b`, but can be whatever you have installed

POPPLER_PATH: the path to the poppler binaries, none will use the system path

LIGHTWEIGHT_MODE: toggles between pixtral 12b and qwen 7b

## Installation

    uv venv
    
    uv install -r requirements.txt

## Run the server
this installs some models, so first run will take a while
files will be stored in the folder specified in the [.env](/flask_server/.env) file

    uv run -m flask_server


## To Do

Database

TTYL on all tasks

Seperate out a front end

Rate limiting

Streaming response

WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.

## Jenkins setup

    https://www.jenkins.io/doc/book/installing/docker/

Once you have DinD up and jenkins configured, test DinD with hello world

    docker exec jenkins-blueocean docker run hello-world

then add a pipeline job with the jenkinsfile from git repo

curl -i -X GET -H "Authorization: Bearer " "http://localhost:8000/2753bd52-5a44-46da-a632-905c968a8ae1"