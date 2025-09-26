pipeline {
    // 1. Dùng agent any để tránh lỗi biên dịch do thiếu Docker Pipeline Plugin.
    // Các bước Python cụ thể sẽ chạy bên trong Docker container.
    agent any

    environment {
        APP_NAME              = 'housing-ml-api'
        BUILD_TAGGED          = "${env.BUILD_NUMBER}"
        DOCKERHUB_NAMESPACE   = 'tiennguyenn371'          
        IMAGE                 = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:${BUILD_TAGGED}"
        IMAGE_LATEST          = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:latest"
        SONARQUBE_NAME        = 'SonarQubeServer'
    }

    options { 
        timestamps()
    }

    triggers { 
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Code Quality (Lint)') {
            steps {
                // Chạy lệnh trong container Python 3.9-slim để đảm bảo có pip, black, flake8
                script {
                    docker.image('python:3.9-slim').pull(true).inside {
                        sh '''
                        // Cài đặt tất cả dependencies trong môi trường Docker hiện tại
                        pip install --no-cache-dir -r requirements.txt
                        
                        // Thực thi linting
                        black --check .
                        flake8 .
                        '''
                    }
                }
            }
        }

        stage('Test') {
            steps {
                // Chạy lệnh trong container Python 3.9-slim
                script {
                    docker.image('python:3.9-slim').pull(true).inside {
                        sh '''
                        pytest -q \
                            --junitxml=reports/junit.xml \
                            --cov=app \
                            --cov-report=xml:reports/coverage.xml
                        '''
                    }
                }
            }
            post {
                always {
                    // Các bước này chạy ngoài container, trên Jenkins agent
                    junit 'reports/junit.xml'
                    recordIssues tools: [flake8(pattern: '**/*.py', id: 'flake8', name: 'flake8')]
                    publishCoverage adapters: [coberturaAdapter('reports/coverage.xml')],  
                                     sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                // Stage này cần Sonar Scanner được cài đặt trên Jenkins Agent
                withSonarQubeEnv("${SONARQUBE_NAME}") {
                    sh 'sonar-scanner'
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 3, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build (Docker)') {
            steps {
                // Stage này cần Docker CLI trên Jenkins Agent
                ansiColor('xterm') {
                    sh '''
                    docker build -t ${IMAGE} .
                    '''
                }
            }
        }

        stage('Security') {
            steps {
                // Chạy lệnh trong container Python 3.9-slim
                script {
                    docker.image('python:3.9-slim').pull(true).inside {
                        // Thực thi Security analysis (ví dụ: Bandit)
                        sh '''
                        bandit -r . -f xml -o reports/bandit.xml || true
                        '''
                    }
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/**', fingerprint: true
                    junit testResults: 'reports/bandit.xml', allowEmptyResults: true
                }
            }
        }

        stage('Deploy: Staging') {
            steps {
                // Stage này cần Docker Compose trên Jenkins Agent
                sh '''
                IMAGE_NAME=${IMAGE} docker compose -f docker-compose.staging.yml up -d --remove-orphans
                sleep 2
                curl -sSf http://localhost:8000/health
                '''
            }
        }

        stage('Release: Tag & Push Image (main only)') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    docker tag ${IMAGE} ${IMAGE_LATEST}
                    docker push ${IMAGE}
                    docker push ${IMAGE_LATEST}
                    '''
                }
                sh '''
                git config user.email "ci@example.com"
                git config user.name "jenkins"
                git tag -a v${BUILD_NUMBER} -m "Release ${BUILD_NUMBER}"
                git push origin v${BUILD_NUMBER} || true
                '''
            }
        }

        stage('Smoke + Monitoring Check') {
            steps {
                sh '''
                curl -sSf http://localhost:8000/metrics | head -n 20
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'docker-compose.staging.yml', fingerprint: true
        }
    }
}
