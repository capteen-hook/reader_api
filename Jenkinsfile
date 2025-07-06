pipeline {
    agent any

    environment {
        OLLAMA_URL='http://host.docker.internal:11434/v1 # ollama on the host machine, natively for performance'
        TIKA_URL='http://tika:9998/tika # these depend on the container names'
        RABBITMQ_URL='http://rabbitmq:15672/api # ^'

        PORT='8000'

        TRANSFORMERS_CACHE='./cache'
        WORK_DIR='./workdir'

        MODEL_NAME='gemma3:4b'

        POPPLER_PATH='none'

        LIGHTWEIGHT_MODE='True # not used currently'

        JWT_SECRET_KEY='none'
        TAVILY_KEY='none'

        FLASK_SERVER_CONTAINER_NAME='flask_server'

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
        stage('Create .env File') {
            steps {
                script {
                    sh 'rm -rf .env' // Ensure no directory or file named `.env` exists
                    writeFile file: '.env', text: """
                        OLLAMA_URL=${OLLAMA_URL}
                        TIKA_URL=${TIKA_URL}
                        RABBITMQ_URL=${RABBITMQ_URL}
                        PORT=${PORT}
                        TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}
                        WORK_DIR=${WORK_DIR}
                        MODEL_NAME=${MODEL_NAME}
                        POPPLER_PATH=${POPPLER_PATH}
                        LIGHTWEIGHT_MODE=${LIGHTWEIGHT_MODE}
                        JWT_SECRET_KEY=${JWT_SECRET_KEY}
                        TAVILY_KEY=${TAVILY_KEY}
                        FLASK_SERVER_CONTAINER_NAME=${FLASK_SERVER_CONTAINER_NAME}
                        TIKA_IMAGE=${TIKA_IMAGE}
                        TIKA_CONTAINER_NAME=${TIKA_CONTAINER_NAME}
                        TIKA_PORT=${TIKA_PORT}
                        TIKA_CONFIG_FILE=${TIKA_CONFIG_FILE}
                        RABBITMQ_IMAGE=${RABBITMQ_IMAGE}
                        RABBITMQ_CONTAINER_NAME=${RABBITMQ_CONTAINER_NAME}
                        RABBITMQ_PORT_1=${RABBITMQ_PORT_1}
                        RABBITMQ_PORT_2=${RABBITMQ_PORT_2}
                        RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}
                        RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}
                    """
                }
            }
        }
        stage('Build with Docker Compose') {
            steps {
                sh 'docker compose up -d --build'
            }
        }
        stage('Flask healthcheck') {
            steps {
                script {
                def maxRetries = 20
                def retryCount = 0
                def isHealthy = false

                while (retryCount < maxRetries) {
                    def status = sh(script: "docker inspect --format='{{.State.Health.Status}}' flask_server", returnStdout: true).trim()
                    echo "Current health status: ${status}"

                    if (status == "healthy") {
                    isHealthy = true
                    break
                    }

                    retryCount++
                    sleep 10
                }

                if (!isHealthy) {
                    error "Flask service failed to become healthy after ${maxRetries} retries."
                }
                }
            }
        }
        stage('Tika healthcheck') {
            steps {
                script {
                def maxRetries = 20
                def retryCount = 0
                def isHealthy = false

                while (retryCount < maxRetries) {
                    def status = sh(script: "docker inspect --format='{{.State.Health.Status}}' tika", returnStdout: true).trim()
                    echo "Current health status: ${status}"

                    if (status == "healthy") {
                    isHealthy = true
                    break
                    }

                    retryCount++
                    sleep 10
                }

                if (!isHealthy) {
                    error "Tika service failed to become healthy after ${maxRetries} retries."
                }
                }
            }
        }
        stage('RabbitMQ healthcheck') {
            steps {
                script {
                def maxRetries = 20
                def retryCount = 0
                def isHealthy = false

                while (retryCount < maxRetries) {
                    def status = sh(script: "docker inspect --format='{{.State.Health.Status}}' rabbitmq", returnStdout: true).trim()
                    echo "Current health status: ${status}"

                    if (status == "healthy") {
                    isHealthy = true
                    break
                    }

                    retryCount++
                    sleep 10
                }

                if (!isHealthy) {
                    error "RabbitMQ service failed to become healthy after ${maxRetries} retries."
                }
                }
            }
        }
    }
    post {
        always {
            sh 'docker compose down'
        }
    }
}