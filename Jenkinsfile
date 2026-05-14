pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        string(name: 'DOCKER_IMAGE_NAME', defaultValue: 'wine-quality-mlops', description: 'Docker image name, e.g. dockerhub-user/wine-quality-mlops')
        string(name: 'DOCKER_IMAGE_TAG', defaultValue: '', description: 'Optional Docker image tag. Leave empty to use build-BUILD_NUMBER.')
        string(name: 'APP_PORT', defaultValue: '', description: 'Published API port for docker compose.')
        string(name: 'DATABASE_HOST', defaultValue: '', description: 'PostgreSQL host or service name.')
        string(name: 'DATABASE_PORT', defaultValue: '', description: 'PostgreSQL port.')
        string(name: 'POSTGRES_DB', defaultValue: '', description: 'PostgreSQL database name.')
        string(name: 'POSTGRES_USER', defaultValue: '', description: 'PostgreSQL application user.')
        string(name: 'POSTGRES_PASSWORD_CREDENTIALS_ID', defaultValue: 'postgres-password', description: 'Jenkins Secret Text credentials ID for PostgreSQL password.')
        string(name: 'DOCKERHUB_CREDENTIALS_ID', defaultValue: 'dockerhub-credentials', description: 'Jenkins Username/Password credentials ID for DockerHub.')
        booleanParam(name: 'RUN_FUNCTIONAL_TESTS', defaultValue: true, description: 'Run docker-compose functional tests with PostgreSQL.')
        booleanParam(name: 'PUSH_IMAGE', defaultValue: false, description: 'Push the built Docker image to DockerHub.')
    }

    environment {
        VENV_DIR = '.venv'
        COMPOSE_ENV_FILE = '.jenkins.env'
        COVERAGE_FILE = 'coverage.xml'
        FUNCTIONAL_REPORT = 'functional-test-report.json'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Resolve Parameters') {
            steps {
                script {
                    def requiredParams = [
                        'DOCKER_IMAGE_NAME',
                        'APP_PORT',
                        'DATABASE_HOST',
                        'DATABASE_PORT',
                        'POSTGRES_DB',
                        'POSTGRES_USER',
                        'POSTGRES_PASSWORD_CREDENTIALS_ID',
                    ]

                    def missing = requiredParams.findAll { !params[it]?.trim() }
                    if (missing) {
                        error("Missing Jenkins parameters: ${missing.join(', ')}")
                    }

                    env.RESOLVED_IMAGE_NAME = params.DOCKER_IMAGE_NAME.trim()
                    env.RESOLVED_IMAGE_TAG = params.DOCKER_IMAGE_TAG?.trim() ? params.DOCKER_IMAGE_TAG.trim() : "build-${env.BUILD_NUMBER}"
                    env.RESOLVED_APP_PORT = params.APP_PORT.trim()
                    env.RESOLVED_DATABASE_HOST = params.DATABASE_HOST.trim()
                    env.RESOLVED_DATABASE_PORT = params.DATABASE_PORT.trim()
                    env.RESOLVED_POSTGRES_DB = params.POSTGRES_DB.trim()
                    env.RESOLVED_POSTGRES_USER = params.POSTGRES_USER.trim()
                }
            }
        }

        stage('Prepare Compose Environment') {
            steps {
                withCredentials([
                    string(credentialsId: params.POSTGRES_PASSWORD_CREDENTIALS_ID, variable: 'POSTGRES_PASSWORD')
                ]) {
                    writeFile(
                        file: env.COMPOSE_ENV_FILE,
                        text: (
                            "DOCKER_IMAGE_NAME=${env.RESOLVED_IMAGE_NAME}\n" +
                            "DOCKER_IMAGE_TAG=${env.RESOLVED_IMAGE_TAG}\n" +
                            "APP_PORT=${env.RESOLVED_APP_PORT}\n" +
                            "DATABASE_HOST=${env.RESOLVED_DATABASE_HOST}\n" +
                            "DATABASE_PORT=${env.RESOLVED_DATABASE_PORT}\n" +
                            "POSTGRES_DB=${env.RESOLVED_POSTGRES_DB}\n" +
                            "POSTGRES_USER=${env.RESOLVED_POSTGRES_USER}\n" +
                            "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}\n"
                        )
                    )
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                powershell '''
python -m venv .venv
& ".\\.venv\\Scripts\\python.exe" -m pip install --upgrade pip
& ".\\.venv\\Scripts\\python.exe" -m pip install -r requirements.txt
'''
            }
        }

        stage('Run DVC Pipeline') {
            steps {
                powershell '& ".\\.venv\\Scripts\\dvc.exe" repro'
            }
        }

        stage('Run Pytest') {
            steps {
                powershell '& ".\\.venv\\Scripts\\pytest.exe" --cov=src/wine_quality_mlops --cov-report=xml --cov-report=term-missing'
            }
        }

        stage('Build Docker Image') {
            steps {
                powershell 'docker compose --env-file .jenkins.env build api'
            }
        }

        stage('Seed PostgreSQL') {
            when {
                expression { params.RUN_FUNCTIONAL_TESTS }
            }
            steps {
                powershell '''
docker compose --env-file .jenkins.env up -d postgres
docker compose --env-file .jenkins.env --profile seed run --rm db-seed
'''
            }
        }

        stage('Run Functional Tests') {
            when {
                expression { params.RUN_FUNCTIONAL_TESTS }
            }
            steps {
                powershell '''
$ErrorActionPreference = 'Stop'
docker compose --env-file .jenkins.env up -d api

for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$env:RESOLVED_APP_PORT/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            break
        }
    } catch {
        if ($attempt -eq 19) {
            throw "API healthcheck failed after 20 attempts."
        }
    }

    if ($attempt -eq 19) {
        throw "API healthcheck failed after 20 attempts."
    }

    Start-Sleep -Seconds 5
}

docker compose --env-file .jenkins.env exec -T api python tests/functional/run_scenario.py --scenario /app/scenario.json --base-url http://127.0.0.1:8000 --report /app/artifacts/functional-test-report.json
$containerId = docker compose --env-file .jenkins.env ps -q api
if (-not $containerId) {
    throw 'API container was not found after functional test execution.'
}
docker cp "$containerId`:/app/artifacts/functional-test-report.json" functional-test-report.json
'''
            }
        }

        stage('Push Docker Image') {
            when {
                expression { params.PUSH_IMAGE }
            }
            steps {
                powershell '''
$ErrorActionPreference = 'Stop'
if ($env:RESOLVED_IMAGE_NAME -notmatch '/') {
    throw 'For Docker Hub push set DOCKER_IMAGE_NAME as username/repository, for example yourname/wine-quality-mlops.'
}
docker push "$env:RESOLVED_IMAGE_NAME`:$env:RESOLVED_IMAGE_TAG"
if ($LASTEXITCODE -ne 0) {
    throw 'Docker push for the build tag failed.'
}
docker tag "$env:RESOLVED_IMAGE_NAME`:$env:RESOLVED_IMAGE_TAG" "$env:RESOLVED_IMAGE_NAME`:latest"
if ($LASTEXITCODE -ne 0) {
    throw 'Docker tag latest failed.'
}
docker push "$env:RESOLVED_IMAGE_NAME`:latest"
if ($LASTEXITCODE -ne 0) {
    throw 'Docker push for latest failed.'
}
'''
            }
        }

        stage('Generate DevSecOps Metadata') {
            steps {
                powershell '''
& ".\\.venv\\Scripts\\python.exe" scripts/generate_dev_sec_ops.py --image-ref "$env:RESOLVED_IMAGE_NAME`:$env:RESOLVED_IMAGE_TAG" --coverage-xml coverage.xml --output dev_sec_ops.yml
'''
            }
        }
    }

    post {
        always {
            script {
                if (fileExists(env.COMPOSE_ENV_FILE)) {
                    powershell(returnStatus: true, script: 'docker compose --env-file .jenkins.env logs')
                    powershell(returnStatus: true, script: 'docker compose --env-file .jenkins.env down -v --remove-orphans')
                    powershell(returnStatus: true, script: 'Remove-Item .jenkins.env -Force')
                }
            }

            archiveArtifacts(
                artifacts: 'coverage.xml,dev_sec_ops.yml,artifacts/metrics.json,functional-test-report.json',
                allowEmptyArchive: true,
                onlyIfSuccessful: false,
            )
        }
    }
}