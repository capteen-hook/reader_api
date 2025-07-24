FROM rocm/pytorch:rocm6.4.1_ubuntu24.04_py3.12_pytorch_release_2.6.0

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

# Copy only requirements.txt first to leverage Docker's caching
COPY ./requirements.txt /app/flask_server/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/flask_server/requirements.txt

# Copy the rest of the application files
COPY . /app/flask_server

# before launching the server, write out an api key to a file with generate_long_lasting_token in ./flask_server/generate.py
#RUN python -c "from flask_server.generate import generate_long_lasting_token; generate_long_lasting_token()"

EXPOSE ${PORT:-8000}

CMD ["python", "-m", "flask_server"]