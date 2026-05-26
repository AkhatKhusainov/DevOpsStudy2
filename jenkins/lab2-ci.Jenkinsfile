pipeline {
    agent { label 'windows' }

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        string(name: 'DOCKER_IMAGE_NAME', defaultValue: 'wine-quality-mlops', description: 'Local image name or registry/repository for validation builds.')
        string(name: 'DOCKER_IMAGE_TAG', defaultValue: '', description: 'Optional Docker image tag. Leave empty to use build-BUILD_NUMBER.')
        string(name: 'DOCKERHUB_CREDENTIALS_ID', defaultValue: 'dockerhub-credentials', description: 'Jenkins Username/Password credentials ID for Docker Hub login. Leave empty to reuse the host Docker login.')
        string(name: 'APP_PORT', defaultValue: '', description: 'Published API port for docker compose.')
        string(name: 'DATABASE_HOST', defaultValue: '', description: 'PostgreSQL host or service name.')
        string(name: 'DATABASE_PORT', defaultValue: '', description: 'PostgreSQL port.')
        string(name: 'POSTGRES_DB', defaultValue: '', description: 'PostgreSQL database name.')
        string(name: 'POSTGRES_USER', defaultValue: '', description: 'PostgreSQL application user.')
        string(name: 'POSTGRES_PASSWORD_CREDENTIALS_ID', defaultValue: 'postgres-password', description: 'Jenkins Secret Text credentials ID for PostgreSQL password.')
        booleanParam(name: 'PUSH_IMAGE', defaultValue: true, description: 'Push the built Docker image to Docker Hub.')
        booleanParam(name: 'TRIGGER_CD', defaultValue: false, description: 'Trigger the Lab2 CD pipeline after a successful CI run.')
        string(name: 'CD_JOB_NAME', defaultValue: 'WineQuality-Lab2-CD', description: 'Jenkins job name for the Lab2 CD pipeline.')
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

                    env.RESOLVED_IMAGE_NAME = params.DOCKER_IMAGE_NAME?.trim() ? params.DOCKER_IMAGE_NAME.trim() : 'wine-quality-mlops'
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
if (-not (Test-Path .venv/Scripts/python.exe)) {
    python -m venv .venv
}
& "./.venv/Scripts/python.exe" -m pip install --upgrade pip
& "./.venv/Scripts/python.exe" -m pip install -r requirements.txt
'''
            }
        }

        stage('Run DVC Pipeline') {
            steps {
                powershell '& "./.venv/Scripts/dvc.exe" repro'
            }
        }

        stage('Run Pytest') {
            steps {
                powershell '& "./.venv/Scripts/pytest.exe" --cov=src/wine_quality_mlops --cov-report=xml --cov-report=term-missing'
            }
        }

        stage('Build Docker Image') {
            steps {
                powershell 'docker compose --env-file .jenkins.env build api'
            }
        }

        stage('Push Docker Image') {
            when {
                expression { params.PUSH_IMAGE }
            }
            steps {
                script {
                    def pushScript = '''
$ErrorActionPreference = 'Stop'
if ($env:RESOLVED_IMAGE_NAME -notmatch '/') {
    throw 'For Docker Hub push set DOCKER_IMAGE_NAME as username/repository, for example yourname/wine-quality-mlops.'
}
if ($env:DOCKERHUB_USERNAME -and $env:DOCKERHUB_TOKEN) {
    $env:DOCKERHUB_TOKEN | docker login --username "$env:DOCKERHUB_USERNAME" --password-stdin
    if ($LASTEXITCODE -ne 0) {
        throw 'Docker Hub login failed.'
    }
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
                    def dockerhubCredentialsId = params.DOCKERHUB_CREDENTIALS_ID?.trim()
                    if (dockerhubCredentialsId) {
                        withCredentials([
                            usernamePassword(credentialsId: dockerhubCredentialsId, usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')
                        ]) {
                            powershell pushScript
                        }
                    } else {
                        powershell pushScript
                    }
                }
            }
        }

        stage('Seed PostgreSQL') {
            steps {
                powershell '''
docker compose --env-file .jenkins.env up -d postgres
docker compose --env-file .jenkins.env --profile seed run --rm db-seed
'''
            }
        }

        stage('Run Functional Tests') {
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

        stage('Generate DevSecOps Metadata') {
            steps {
                powershell '''
& "./.venv/Scripts/python.exe" scripts/generate_dev_sec_ops.py --image-ref "$env:RESOLVED_IMAGE_NAME`:$env:RESOLVED_IMAGE_TAG" --coverage-xml coverage.xml --output dev_sec_ops.yml
'''
            }
        }

        stage('Trigger Lab 2 CD') {
            when {
                expression { params.TRIGGER_CD }
            }
            steps {
                build job: params.CD_JOB_NAME,
                    wait: false,
                    parameters: [
                        string(name: 'DOCKER_IMAGE_NAME', value: env.RESOLVED_IMAGE_NAME),
                        string(name: 'DOCKER_IMAGE_TAG', value: env.RESOLVED_IMAGE_TAG),
                        string(name: 'APP_PORT', value: env.RESOLVED_APP_PORT),
                        string(name: 'DATABASE_HOST', value: env.RESOLVED_DATABASE_HOST),
                        string(name: 'DATABASE_PORT', value: env.RESOLVED_DATABASE_PORT),
                        string(name: 'POSTGRES_DB', value: env.RESOLVED_POSTGRES_DB),
                        string(name: 'POSTGRES_USER', value: env.RESOLVED_POSTGRES_USER),
                        string(name: 'POSTGRES_PASSWORD_CREDENTIALS_ID', value: params.POSTGRES_PASSWORD_CREDENTIALS_ID),
                    ]
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