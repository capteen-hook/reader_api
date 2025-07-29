This is the reader_api
it reads files into json schemas, and provides a REST API to access them.
it uses celery, redis, and rabbitmq to provide a file queue system for heavy tasks.

# Read the docs

use [https://editor.swagger.io/](https://editor.swagger.io/) to view the API documentation.
and paste [./openapi_spec.yaml](./openapi_spec.yaml) into the editor.

# Run with UV
Run the development server:

```bash
uv venv

uv install -r requirements.txt

uv run -m flask_server
```