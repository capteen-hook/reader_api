pipeline {
    agent {
        docker { image 'docker:stable' }
    }
    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }
    stages {
        stage('Checkout') {
            steps {
                // Checkout the repository containing docker-compose.yml
                checkout scm
            }
        }
        stage('Build and Start Services') {
            steps {
                script {
                    // Build and start services using docker-compose
                    sh 'docker-compose -f $DOCKER_COMPOSE_FILE up -d --build'
                }
            }
        }
        stage('Run Tests') {
            steps {
                script {
                    // Example: Run health checks or integration tests
                    sh '''
                    curl -f http://localhost:${FLASK_SERVER_PORT:-5000}/health || exit 1
                    curl -f http://localhost:${TIKA_PORT:-9998}/tika || exit 1
                    '''
                }
            }
        }
        stage('Stop and Clean Up') {
            steps {
                script {
                    // Stop and remove containers
                    sh 'docker-compose -f $DOCKER_COMPOSE_FILE down'
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    // Deploy to production (customize as needed)
                    sh 'docker-compose -f $DOCKER_COMPOSE_FILE up -d'
                }
            }
        }
    }
    post {
        always {
            // Clean up workspace
            cleanWs()
        }
    }
}