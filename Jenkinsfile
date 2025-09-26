pipeline {
  agent any
  environment {
    APP_NAME = 'housing-ml-api'
    BUILD_TAGGED = "${env.BUILD_NUMBER}"
    DOCKERHUB_NAMESPACE = 'tiennguyen371'
    IMAGE = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:${BUILD_TAGGED}"
    IMAGE_LATEST = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:latest"
    SONARQUBE_NAME = 'SonarQubeServer'
  }
  options {
    timestamps()
  }
  triggers { pollSCM('H/5 * * * *') }

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
        docker { image 'python:3.11-slim' }
      }
      steps {
        sh '''
          python -m venv .venv
          . .venv/bin/activate
          pip install -r requirements.txt
          PYTHONPATH=. pytest -q --junitxml=reports/junit.xml --cov=app --cov-report=xml:reports/coverage.xml
        '''
      }
      post {
        always {
          junit 'reports/junit.xml'
          recordIssues tools: [flake8(pattern: '**/*.py', id: 'flake8', name: 'flake8')]
          recordCoverage tools: [[parser: 'Cobertura', pattern: 'reports/coverage.xml']]
        }
      }
    }

    stage('Code Quality (Lint + SonarQube)') {
      agent {
        docker { image 'python:3.11-slim' }
      }
      steps {
        sh '''
          . .venv/bin/activate
          black --check .
          flake8 .
        '''
        withSonarQubeEnv("${SONARQUBE_NAME}") {
          sh '''
            . .venv/bin/activate
            sonar-scanner
          '''
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

    stage('Security') {
      agent {
        docker { image 'python:3.11-slim' }
      }
      steps {
        sh '''
          . .venv/bin/activate
          bandit -r app -f junit -o reports/bandit.xml || true
          pip-audit -r requirements.txt -f json -o reports/pip_audit.json || true
          if command -v trivy >/dev/null 2>&1; then
            trivy image --exit-code 0 --format table -o reports/trivy.txt ${IMAGE} || true
          fi
        '''
      }
      post {
        always {
          archiveArtifacts artifacts: 'reports/**', fingerprint: true
          junit testResults: 'reports/bandit.xml', allowEmptyResults: true
        }
      }
    }

    stage('Build Docker Image') {
      steps {
        sh '''
          docker build -t ${IMAGE} .
        '''
      }
    }

    stage('Deploy: Staging') {
      steps {
        sh '''
          IMAGE_NAME=${IMAGE} docker compose -f docker-compose.staging.yml up -d --remove-orphans
          sleep 5
          curl -sSf http://localhost:8000/health
        '''
      }
    }

    stage('Release: Push Image (main only)') {
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

    stage('Monitoring (Datadog)') {
      steps {
        sh '''
          echo ">>> Sending metrics to Datadog..."
          curl -X POST "https://api.datadoghq.com/api/v1/series" \
            -H "Content-Type: application/json" \
            -H "DD-API-KEY:${DD_API_KEY}" \
            -d @- <<EOF
          {
            "series": [
              {
                "metric": "jenkins.pipeline.success",
                "points": [[ $(date +%s), 1 ]],
                "type": "count",
                "tags": ["pipeline:SIT753_Task-7.3HD", "stage:monitoring"]
              }
            ]
          }
EOF
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
