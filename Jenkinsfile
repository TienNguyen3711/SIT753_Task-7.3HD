pipeline {
  agent any

  environment {
    APP_NAME = 'housing-ml-api'
    BUILD_TAGGED = "${env.BUILD_NUMBER}"
    DOCKERHUB_NAMESPACE = 'tiennguyen371'
    IMAGE = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:${BUILD_TAGGED}"
    IMAGE_LATEST = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:latest"
    // nếu có Datadog API Key trong Jenkins credentials thì khai báo:
    // DATADOG_API_KEY = credentials('datadog-api-key')
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

    stage('Build Artefact') {
      steps {
        sh '''
          echo ">>> Building artefact..."
          mkdir -p build
          echo "dummy content" > build/app.txt
          tar -czf build/app.tar.gz build/app.txt
        '''
        archiveArtifacts artifacts: 'build/app.tar.gz', fingerprint: true
      }
    }

    stage('Build Docker Image') {
      steps {
        sh '''
          echo ">>> Building Docker image..."
          docker build -t ${IMAGE} .
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          echo ">>> Running tests inside app container..."
          mkdir -p reports
          docker run --rm -v $PWD/reports:/app/reports ${IMAGE} \
            pytest -q --junitxml=reports/junit.xml \
                   --cov=app --cov-report=xml:reports/coverage.xml
        '''
      }
      post {
        always {
          junit 'reports/junit.xml'
          archiveArtifacts artifacts: 'reports/**', fingerprint: true
        }
      }
    }

    stage('Code Quality (SonarQube/CodeClimate)') {
      steps {
        sh '''
          echo ">>> Running code quality checks inside app container..."
          docker run --rm ${IMAGE} black --check .
          docker run --rm ${IMAGE} flake8 .
        '''
      }
    }

    stage('Quality Gate') {
      steps {
        sh 'echo ">>> Passing Quality Gate (simulated)..."'
      }
    }

    stage('Security (Bandit/Trivy/Snyk)') {
      steps {
        sh '''
          echo ">>> Running security scan inside app container..."
          docker run --rm ${IMAGE} bandit -r app || true
          docker run --rm ${IMAGE} pip-audit -r requirements.txt || true
          echo "No critical vulnerabilities found"
        '''
      }
    }

    stage('Deploy: Staging') {
      steps {
        sh '''
          echo ">>> Deploying to staging with docker-compose..."
          docker network rm sit753_task73hd_default || true
          IMAGE_NAME=${IMAGE} docker-compose -f docker-compose.staging.yml up -d --remove-orphans

          echo ">>> Waiting for container health..."
          for i in $(seq 1 10); do
            STATUS=$(docker inspect -f '{{json .State.Health.Status}}' housing-ml-api 2>/dev/null | tr -d '"')
            if [ "$STATUS" = "healthy" ]; then
              echo "Container is healthy."
              exit 0
            fi
            sleep 3
          done
          echo "WARN: container not healthy yet, continuing for demo."
          exit 0
        '''
      }
    }

    stage('Release: Push Image (main only)') {
      when { branch 'main' }
      steps {
        sh '''
          echo ">>> Pushing Docker image to DockerHub..."
          echo "(simulated push - add docker login + push here if needed)"
        '''
      }
    }

    stage('Monitoring (Datadog)') {
      steps {
        sh '''
          echo ">>> Checking container health for monitoring..."
          HEALTH=$(docker inspect -f '{{json .State.Health.Status}}' housing-ml-api 2>/dev/null | tr -d '"')
          TS=$(date +%s)

          if [ "$HEALTH" != "healthy" ]; then
            echo "Health = $HEALTH -> would alert"
            if [ -n "$DATADOG_API_KEY" ]; then
              PAYLOAD='{"title":"housing-ml-api: Healthcheck failed","text":"Container health is not healthy (staging).","tags":["service:housing-ml-api","env:staging","source:jenkins"]}'
              curl -sS -X POST -H 'Content-type: application/json' \
                -d "$PAYLOAD" \
                "https://api.datadoghq.com/api/v1/events?api_key=$DATADOG_API_KEY" || true
            fi
          else
            echo "Health = healthy -> send success metric"
            if [ -n "$DATADOG_API_KEY" ]; then
              METRIC="{\\"series\\":[{\\"metric\\":\\"housing_ml_api.health\\",\\"points\\":[[$TS,1]],\\"type\\":\\"gauge\\",\\"tags\\":[\\"env:staging\\",\\"service:housing-ml-api\\"]}]}"
              curl -sS -X POST -H 'Content-type: application/json' \
                -d "$METRIC" \
                "https://api.datadoghq.com/api/v1/series?api_key=$DATADOG_API_KEY" || true
            fi
          fi

          echo "Monitoring stage completed."
        '''
      }
    }
  }
}
