pipeline {
    // 1. Dùng Docker Agent với Python image để đảm bảo có sẵn 'pip' và 'python'
    agent {
        docker {
            image 'python:3.9-slim' // Image Python chính thức, gọn nhẹ
            // Thêm các tham số tùy chọn nếu cần (ví dụ: Sonar-scanner)
            // args '-v /usr/bin/sonar-scanner:/usr/bin/sonar-scanner' 
        }
    }

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
                sh '''
                // Cài đặt tất cả dependencies trong môi trường Docker hiện tại
                pip install --no-cache-dir -r requirements.txt
                
                // Thực thi linting
                black --check .
                flake8 .
                '''
            }
        }

        stage('Test') {
            steps {
                // Đã loại bỏ '. .venv/bin/activate' vì chúng ta đang ở trong Docker Agent Python
                sh '''
                pytest -q \
                    --junitxml=reports/junit.xml \
                    --cov=app \
                    --cov-report=xml:reports/coverage.xml
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    recordIssues tools: [flake8(pattern: '**/*.py', id: 'flake8', name: 'flake8')]
                    publishCoverage adapters: [coberturaAdapter('reports/coverage.xml')],  
                                     sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv("${SONARQUBE_NAME}") {
                    // Cần đảm bảo Sonar Scanner được cài đặt trên Jenkins Agent/hoặc trong Image bạn dùng
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
                ansiColor('xterm') {
                    // Stage này build Docker Image chứa ứng dụng của bạn (bao gồm Python/Dependencies)
                    sh '''
                    docker build -t ${IMAGE} .
                    '''
                }
            }
        }

        stage('Security') {
            steps {
                // Giả định Bandit là công cụ bảo mật và đã được cài đặt qua requirements.txt
                sh '''
                // Thực thi Security analysis (ví dụ: Bandit)
                bandit -r . -f xml -o reports/bandit.xml || true
                '''
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
                // Lệnh triển khai Docker-compose
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
