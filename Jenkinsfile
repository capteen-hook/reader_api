pipeline {
    agent any

    environment {
        DEPLOY_DIR='/var/jenkins_home/workspace/deploy'

        OLLAMA_URL='http://host.docker.internal:11434/v1 # ollama on the host machine, natively for performance'
        TIKA_URL='http://tika:9998/tika # these depend on the container names'
        RABBITMQ_URL='pyamqp://user:password@localhost// # ^'
        PORT='8000'
        TRANSFORMERS_CACHE='./cache'
        WORK_DIR='./workdir'
        MODEL_NAME='gemma3:4b'
        POPPLER_PATH='C:\\Program Files\\Poppler\\poppler-24.08.0\\Library\\bin # On linux, you can leave this empty if you have poppler installed in your PATH'
        LIGHTWEIGHT_MODE='True # not used currently'
        JWT_SECRET_KEY='your_key_here'
        TAVILY_KEY='your_key_here'
        FLASK_SERVER_CONTAINER_NAME='flask_server-default'
        WORKER_CONTAINER_NAME='worker-default'
        TIKA_IMAGE='apache/tika:latest-full'
        TIKA_CONTAINER_NAME='tika-default'
        TIKA_PORT='9998'
        TIKA_CONFIG_FILE='./tika-config.xml'
        RABBITMQ_IMAGE='rabbitmq:management'
        RABBITMQ_CONTAINER_NAME='rabbitmq-default'
        RABBITMQ_HOST='localhost'
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
                    // move the .env.template to .env
                    sh 'cp .env.template .env'
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
                    def status = sh(script: "docker inspect --format='{{.State.Health.Status}}' ${FLASK_SERVER_CONTAINER_NAME}", returnStdout: true).trim()
                    echo "Current health status: ${status}"

                    if (status == "healthy") {
                    isHealthy = true
                    break
                    }

                    echo "Flask service is not healthy yet: ${sh(script: "docker inspect --format='{{.State.Health.Status}}' ${FLASK_SERVER_CONTAINER_NAME}", returnStdout: true).trim()}. Retrying in 10 seconds..."
                    retryCount++
                    sleep 10
                }

                if (!isHealthy) {
                    error "Flask service failed to become healthy after ${maxRetries} retries."
                }
                }
            }
        }
        stage('Run Tests') {
            steps {
                script {
                    // echo cwd
                    sh 'ls -la'
                    sh 'ls -la basic_tests'
                    echo "Current working directory: ${pwd()}"
                    def output = sh(script: './basic_tests/test.sh', returnStdout: true).trim()
                    def lastLine = output.readLines().last()
                    if (lastLine != "All tests passed!") {
                        error "Tests failed: ${lastLine}"
                    } else {
                        echo "Tests passed successfully!"
                    }
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    // Switch to the deploy directory
                    dir(DEPLOY_DIR) {
                        // pull the latest changes from the repository
                        sh 'git pull origin main || true' // Use '|| true' to avoid failure if no changes
                        // run on host
                        sh 'docker compose up -d --build'
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