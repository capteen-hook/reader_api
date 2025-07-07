pipeline {
    agent any

    environment {
        DEPLOY_DIR='/var/jenkins_home/workspace/deploy'

        // use the env variables from .env.template
        for (line in readFile('.env.template').readLines()) {
            // set each line as an environment variable
            def (key, value) = line.split('=')
            if (key && value) {
                env[key.trim()] = value.trim()
            }
        }
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
                    def status = sh(script: "docker inspect --format='{{.State.Health.Status}}' flask_server", returnStdout: true).trim()
                    echo "Current health status: ${status}"

                    if (status == "healthy") {
                    isHealthy = true
                    break
                    }

                    echo "Flask service is not healthy yet: ${sh(script: "docker inspect --format='{{.State.Health.Status}}' flask_server", returnStdout: true).trim()}"

                    retryCount++
                    sleep 10
                }

                if (!isHealthy) {
                    error "Flask service failed to become healthy after ${maxRetries} retries."
                }
                }
            }
        }
        stage {
            name: 'Run Tests'
            steps {
                script {
                    def output = sh(script: './basics_tests/test.sh', returnStdout: true).trim()
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
                        sh 'docker compose up -d --build' // Rebuild and start the containers
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