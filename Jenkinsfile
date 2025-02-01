pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.test.yml'
        TEST_ENV_FILE = '.env.test'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Test Environment') {
            steps {
                sh '''
                    cp .env.example ${TEST_ENV_FILE}
                    docker-compose -f ${DOCKER_COMPOSE_FILE} build
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    docker-compose -f ${DOCKER_COMPOSE_FILE} up -d test_db
                    sleep 10  # Ждем запуска БД
                    docker-compose -f ${DOCKER_COMPOSE_FILE} run --rm test pytest -v
                '''
            }
            post {
                always {
                    junit 'test-results/*.xml'
                    sh 'docker-compose -f ${DOCKER_COMPOSE_FILE} down'
                }
            }
        }

        stage('Build Production') {
            when {
                branch 'main'
            }
            steps {
                sh 'docker-compose build'
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    docker-compose down
                    docker-compose up -d
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
} 