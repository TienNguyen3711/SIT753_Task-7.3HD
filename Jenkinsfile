pipeline {
  agent any
  environment {
    APP_NAME = 'housing-ml-api'
    BUILD_TAGGED = "${env.BUILD_NUMBER}"
    DOCKERHUB_NAMESPACE = 'yourdockerhub'          // TODO: sửa
    IMAGE = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:${BUILD_TAGGED}"
    IMAGE_LATEST = "${DOCKERHUB_NAMESPACE}/${APP_NAME}:latest"
    SONARQUBE_NAME = 'SonarQubeServer'             // TODO: trùng với Jenkins config
  }
 stage('Build') {
  steps {
    ansiColor('xterm') {
      sh 'echo "Building..."'
    }
  }
}

  triggers { pollSCM('H/5 * * * *') } // hoặc GitHub webhook

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Code Quality (Lint)') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -r requirements.txt
          black --check .
          flake8 .
        '''
      }
    }

    stage('Test') {
      steps {
        sh '''
          . .venv/bin/activate
          pytest -q --junitxml=reports/junit.xml --cov=app --cov-report=xml:reports/coverage.xml
        '''
      }
      post {
        always {
          junit 'reports/junit.xml'
          recordIssues tools: [flake8(pattern: '**/*.py', id: 'flake8', name: 'flake8')]
          publishCoverage adapters: [coberturaAdapter('reports/coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
        }
      }
    }

    stage('SonarQube Analysis') {
      steps {
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

    stage('Build (Docker)') {
      steps {
        sh '''
          docker build -t ${IMAGE} .
        '''
      }
    }

    stage('Security') {
      steps {
        sh '''
          . .venv/bin/activate
          # Code security
          bandit -r app -f junit -o reports/bandit.xml || true
          pip-audit -r requirements.txt -f json -o reports/pip_audit.json || true
          # Image security (nếu có Trivy)
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

    stage('Deploy: Staging') {
      steps {
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
