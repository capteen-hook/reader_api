FROM python:3.12-slim

WORKDIR /app

# Install Rust, required build tools, pkg-config, and OpenSSL development libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    build-essential \
    pkg-config \
    libssl-dev \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
ENV PATH="/root/.cargo/bin:${PATH}"

COPY . /app/flask_server
COPY ../openapi_spec.yaml /app/flask_server/openapi_spec.yaml

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r ./flask_server/requirements.txt

# before launching the server, write out an api key to a file with generate_long_lasting_token in ./flask_server/generate.py
RUN python -c "from flask_server.generate import generate_long_lasting_token; generate_long_lasting_token()"

EXPOSE ${PORT:-8000}

CMD ["python", "-m", "flask_server"]