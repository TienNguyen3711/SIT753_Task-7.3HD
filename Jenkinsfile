pipeline {
    agent any

    environment {
        APP_NAME = 'housing-ml-api'
        BUILD_TAGGED = "${env.BUILD_NUMBER}"
        DOCKERHUB_NAMESPACE = 'yourdockerhub'   // sửa thành namespace DockerHub của bạn
        IMAGE = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:${BUILD_TAGGED}"
        IMAGE_LATEST = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:latest"
        SONARQUBE_NAME = 'SonarQubeServer'      // trùng với tên cấu hình trong Jenkins
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                sh '''
                    echo ">>> Building Python project..."
                    mkdir -p build
                    tar -czf build/app.tar.gz app model requirements.txt
                    ls -lh build/
                '''
                archiveArtifacts artifacts: 'build/app.tar.gz', fingerprint: true
            }
        }

        stage('Test') {
            agent {
                docker {
                    image 'python:3.11-slim'
                }
            }
            steps {
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install -r requirements.txt
                    PYTHONPATH=. pytest -q \
                        --junitxml=reports/junit.xml \
                        --cov=app --cov-report=xml:reports/coverage.xml || true
                '''
            }
        }

        stage('Code Quality (Lint + SonarQube)') {
            steps {
                sh '''
                    . .venv/bin/activate
                    flake8 app/ > flake8-report.txt || true
                '''
                withSonarQubeEnv("${SONARQUBE_NAME}") {
                    sh '''
                        . .venv/bin/activate
                        sonar-scanner \
                          -Dsonar.projectKey=${APP_NAME} \
                          -Dsonar.sources=app \
                          -Dsonar.python.coverage.reportPaths=reports/coverage.xml
                    '''
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 1, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security') {
            steps {
                sh '''
                    . .venv/bin/activate
                    bandit -r app -f txt -o bandit-report.txt || true
                    pip-audit -r requirements.txt > pip-audit-report.txt || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${IMAGE}")
                }
            }
        }

        stage('Deploy: Staging') {
            steps {
                sh '''
                    echo ">>> Deploying container..."
                    docker run -d --rm -p 8000:8000 ${IMAGE}
                '''
            }
        }

        stage('Release: Push Image (main only)') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry('', 'dockerhub-credentials') {
                        docker.image("${IMAGE}").push()
                        docker.image("${IMAGE}").push("latest")
                    }
                }
            }
        }

        stage('Monitoring (Datadog)') {
            steps {
                sh '''
                    echo ">>> Sending metrics to Datadog..."
                    # Ví dụ gửi metric custom
                    echo "jenkins.pipeline.success:1|c" | nc -w 1 -u localhost 8125 || true
                '''
            }
        }
    }

    post {
        always {
            // Publish JUnit test results
            junit 'reports/junit.xml'

            // Publish lint results
            recordIssues tools: [flake8(pattern: '**/flake8-report.txt')]

            // Archive reports
            archiveArtifacts artifacts: 'reports/*.xml, *.txt', allowEmptyArchive: true
        }
    }
}
