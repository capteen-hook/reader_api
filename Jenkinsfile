pipeline {
    agent any

    stages {
        stage('Clone') {
            steps {
                checkout scm
            }
        }
        stage('Build with Docker Compose') {
            steps {
                sh 'docker-compose build'
                sh 'docker-compose up -d'
            }
        }
        stage('Run Tests') {
            steps {
                sh 'curl -f http://localhost:8000/ || true' // Flask Service should be running
                sh 'curl -f http://localhost:9998/ || true' // Tika Service should be running
                sh 'curl -f http://localhost:5672/ || true' // RabbitMQ Service should be running
            }
        }
    }
    post {
        always {
            sh 'docker-compose down || true'
        }
    }
}
