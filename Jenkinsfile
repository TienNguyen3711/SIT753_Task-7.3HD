pipeline {
    agent {
        docker {
            image 'python:3.11-slim'
            args '-u root:root'   // chạy với quyền root để tránh lỗi permission
        }
    }

    environment {
        APP_NAME = 'housing-ml-api'
        BUILD_TAGGED = "${env.BUILD_NUMBER}"
        DOCKERHUB_NAMESPACE = 'tiennguyenn371'   // TODO: sửa thành Docker Hub namespace của bạn
        IMAGE = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:${BUILD_TAGGED}"
        IMAGE_LATEST = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:latest"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Env') {
            steps {
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                    echo ">>> Building project..."
                    mkdir -p build
                    tar -czf build/app.tar.gz app model requirements.txt
                    ls -lh build/
                '''
                archiveArtifacts artifacts: 'build/*.tar.gz', fingerprint: true
            }
        }

        stage('Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest -q --junitxml=reports/junit.xml --cov=app --cov-report=xml:reports/coverage.xml || true
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Code Quality (Lint)') {
            steps {
                sh '''
                    . .venv/bin/activate
                    flake8 app/ || true
                '''
            }
        }

        stage('Security') {
            steps {
                sh '''
                    . .venv/bin/activate
                    bandit -r app || true
                    pip-audit || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build -t $IMAGE -t $IMAGE_LATEST .
                '''
            }
        }

        stage('Deploy: Staging') {
            steps {
                sh '''
                    echo ">>> Deploying to staging..."
                    docker run -d --rm -p 8000:8000 $IMAGE
                '''
            }
        }

        stage('Release: Push Image (main only)') {
            when {
                branch 'main'
            }
            steps {
                withDockerRegistry([ credentialsId: 'dockerhub-credentials', url: '' ]) {
                    sh '''
                        docker push $IMAGE
                        docker push $IMAGE_LATEST
                    '''
                }
            }
        }

        stage('Monitoring (Datadog)') {
            steps {
                sh '''
                    echo ">>> Sending dummy metric to Datadog..."
                    curl -X POST -H "Content-type: application/json" \
                         -H "DD-API-KEY:$DD_API_KEY" \
                         -d '{"series":[{"metric":"app.build.success","points":[[$(date +%s), 1]],"type":"count","tags":["env:staging"]}]}' \
                         "https://api.datadoghq.com/api/v1/series"
                '''
            }
        }
    }
}
