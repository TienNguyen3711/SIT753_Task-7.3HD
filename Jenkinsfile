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

  options { timestamps() }
  triggers { pollSCM('H/5 * * * *') }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Build Artefact') {
      steps {
        sh '''
          echo ">>> Packaging project..."
          mkdir -p build
          tar -czf build/app.tar.gz app model requirements.txt
        '''
        archiveArtifacts artifacts: 'build/app.tar.gz', fingerprint: true
      }
    }

    stage('Test') {
      agent { docker { image 'python:3.11-slim' } }
      steps {
        sh '''
          python -m venv .venv
          . .venv/bin/activate
          pip install --no-cache-dir -r requirements.txt
          mkdir -p reports
          PYTHONPATH=. pytest -q --junitxml=reports/junit.xml \
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

    stage('Code Quality (SonarQube)') {
      when { branch 'main' }
      agent { docker { image 'sonarsource/sonar-scanner-cli:latest' } }
      steps {
        sh '''
          black --check .
          flake8 .
        '''
        withSonarQubeEnv("${SONARQUBE_NAME}") {
          sh 'sonar-scanner'
        }
      }
    }

    stage('Quality Gate') {
      when { branch 'main' }
      steps {
        timeout(time: 3, unit: 'MINUTES') {
          waitForQualityGate abortPipeline: true
        }
      }
    }

    stage('Security') {
      when { branch 'main' }
      agent { docker { image 'python:3.11-slim' } }
      steps {
        sh '''
          . .venv/bin/activate || true
          bandit -r app -f junit -o reports/bandit.xml || true
          pip-audit -r requirements.txt -f json -o reports/pip_audit.json || true
          trivy image --exit-code 0 --format table -o reports/trivy.txt ${IMAGE} || true
        '''
      }
      post {
        always {
          junit testResults: 'reports/bandit.xml', allowEmptyResults: true
          archiveArtifacts artifacts: 'reports/**', fingerprint: true
        }
      }
    }

    stage('Build Docker Image') {
      steps { sh 'docker build -t ${IMAGE} .' }
    }

    stage('Deploy: Staging') {
      when { branch 'main' }
      steps {
        sh '''
          IMAGE_NAME=${IMAGE} docker compose -f docker-compose.staging.yml up -d --remove-orphans
          sleep 5
          python healthcheck.py
        '''
      }
    }

    stage('Release: Push Image (main only)') {
      when { branch 'main' }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials',
                                          usernameVariable: 'DOCKER_USER',
                                          passwordVariable: 'DOCKER_PASS')]) {
          sh '''
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
            docker tag ${IMAGE} ${IMAGE_LATEST}
            docker push ${IMAGE}
            docker push ${IMAGE_LATEST}
          '''
        }
      }
    }

    stage('Monitoring (Datadog)') {
      when { branch 'main' }
      steps {
        sh '''
          echo ">>> Sending metrics to Datadog..."
          curl -X POST -H 'Content-type: application/json' \
            -d '{"series":[{"metric":"jenkins.pipeline.success","points":[['"$(date +%s)"',1]],"type":"count","tags":["pipeline:success"]}]}' \
            https://api.datadoghq.com/api/v1/series?api_key=$DATADOG_API_KEY || true
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
