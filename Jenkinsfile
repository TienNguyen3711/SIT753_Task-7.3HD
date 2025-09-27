pipeline {
  agent any

  environment {
    APP_NAME = 'housing-ml-api'
    BUILD_TAGGED = "${env.BUILD_NUMBER}"
    DOCKERHUB_NAMESPACE = 'tiennguyen371'
    IMAGE = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:${BUILD_TAGGED}"
    IMAGE_LATEST = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:latest"
  }

  options { timestamps() }
  triggers { pollSCM('H/5 * * * *') }

  stages {
    stage('Checkout') {
      steps {
        echo ">>> Checking out source code..."
        checkout scm
      }
    }

    stage('Build Docker Image') {
      steps {
        sh '''
          echo ">>> Building Docker image..."
          docker build --no-cache --build-arg DEBIAN_FRONTEND=noninteractive -t ${IMAGE} .
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          echo ">>> Running tests inside app container..."
          rm -rf reports && mkdir -p reports
          docker run --rm \
            -v "$PWD/reports:/app/reports" \
            ${IMAGE} \
            pytest -q --maxfail=1 --disable-warnings \
                   --junitxml=reports/junit.xml \
                   --cov=app --cov-report=xml:reports/coverage.xml || true
        '''
      }
      post {
        always {
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**', fingerprint: true
        }
      }
    }

    stage('Code Quality') {
      steps {
        sh '''
          echo ">>> Running code quality checks inside container..."
          docker run --rm \
            -v "$PWD:/app" \
            ${IMAGE} \
            sh -c "black --check . || true; flake8 . || true"
        '''
      }
    }

    stage('Security') {
      steps {
        sh '''
          echo ">>> Running security scan inside container..."
          docker run --rm \
            -v "$PWD:/app" \
            ${IMAGE} \
            bandit -r app || true
        '''
      }
    }

    stage('Deploy: Staging') {
      steps {
        sh '''
          echo ">>> Deploying to staging with docker-compose..."
          IMAGE_NAME=${IMAGE} docker-compose -f docker-compose.staging.yml up -d --remove-orphans

          echo ">>> Waiting for container health..."
          for i in $(seq 1 20); do
            STATUS=$(docker inspect -f '{{json .State.Health.Status}}' housing-ml-api 2>/dev/null | tr -d '"')
            if [ "$STATUS" = "healthy" ]; then
              echo "Container is healthy."
              exit 0
            fi
            sleep 3
          done
          echo "WARN: container not healthy after retries."
          exit 1
        '''
      }
    }

    stage('Release: Push Image (main only)') {
      when { branch 'main' }
      steps {
        sh 'echo ">>> Pushing Docker image to DockerHub (simulated)..."'
      }
    }
  }
}
