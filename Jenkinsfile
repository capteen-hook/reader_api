pipeline {
    agent any

    environment {
        OLLAMA_URL='http://localhost:11434/v1'
        TIKA_URL='http://tika:9998/tika'
        RABBITMQ_URL='http://rabbitmq:15672/api'

        PORT='8000'
        TRANSFORMERS_CACHE='./cache'
        WORK_DIR='./workdir'
        MODEL_NAME='gemma3:4b'
        POPPLER_PATH='C:\\Program Files\\Poppler\\poppler-24.08.0\\Library\\bin'
        LIGHTWEIGHT_MODE='True'
        JWT_SECRET_KEY='none'
        TAVILY_KEY='none'
        FLASK_SERVER_CONTAINER_NAME='flask_server'
        FLASK_SERVER_PORT='5000'
        FLASK_SERVER_ENV_FILE='./.env'
        TIKA_IMAGE='apache/tika:latest-full'
        TIKA_CONTAINER_NAME='tika'
        TIKA_PORT='9998'
        TIKA_CONFIG_FILE='./tika-config.xml'
        RABBITMQ_IMAGE='rabbitmq:management'
        RABBITMQ_CONTAINER_NAME='rabbitmq'
        RABBITMQ_PORT_1='5672'
        RABBITMQ_PORT_2='15672'
        RABBITMQ_DEFAULT_USER='user'
        RABBITMQ_DEFAULT_PASS='password'
    }

    stages {
        stage('Clone') {
            steps {
                checkout scm
            }
        }
        stage('Verify Dockerfile') {
            steps {
                sh '''
                if [ ! -f ./flask_server/Dockerfile ]; then
                    echo "Error: Dockerfile not found in ./flask_server"
                    exit 1
                fi
                '''
            }
        }
        stage('Build with Docker Compose') {
            steps {
                sh 'docker compose up -d --build'
            }
        }
        stage('Run Tests') {
            steps {
                sh 'curl -f http://localhost:8000/' // Flask Service should be running
                sh 'curl -f http://localhost:9998/' // Tika Service should be running
                sh 'curl -f http://localhost:5672/' // RabbitMQ Service should be running
            }
        }
    }
    post {
        always {
            sh 'docker compose down'
        }
    }
}