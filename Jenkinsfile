pipeline {
    agent any
    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
        DOCKER_HOST = 'unix:///var/run/docker.sock'
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Build and Start Services') {
            steps {
                script {
                    sh 'docker-compose -f $DOCKER_COMPOSE_FILE up -d --build'
                }
            }
        }
        stage('Run Tests') {
            steps {
                script {
                    sh '''
                    curl -f http://localhost:${FLASK_SERVER_PORT:-5000}/health || exit 1
                    curl -f http://localhost:${TIKA_PORT:-9998}/tika || exit 1
                    curl -f http://localhost:${RABBITMQ_PORT:-5672}/ || exit 1
                    '''
                }
            }
        }
        stage('Stop and Clean Up') {
            steps {
                script {
                    sh 'docker-compose -f $DOCKER_COMPOSE_FILE down'
                }
            }
        }
        stage('Deploy') {
            steps {
                script {
                    sh 'docker-compose -f $DOCKER_COMPOSE_FILE up -d'
                }
            }
        }
    }
    post {
        always {
            node('any') { // Specify a valid label
                cleanWs()
            }
        }
    }
}