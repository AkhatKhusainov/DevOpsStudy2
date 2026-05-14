pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        string(name: 'DOCKER_IMAGE_NAME', defaultValue: 'wine-quality-mlops', description: 'Docker image name. For registry deploy use username/repository.')
        string(name: 'DOCKER_IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag to deploy.')
        string(name: 'APP_PORT', defaultValue: '', description: 'Published API port for docker compose.')
        string(name: 'DATABASE_HOST', defaultValue: '', description: 'PostgreSQL host or service name.')
        string(name: 'DATABASE_PORT', defaultValue: '', description: 'PostgreSQL port.')
        string(name: 'POSTGRES_DB', defaultValue: '', description: 'PostgreSQL database name.')
        string(name: 'POSTGRES_USER', defaultValue: '', description: 'PostgreSQL application user.')
        string(name: 'POSTGRES_PASSWORD_CREDENTIALS_ID', defaultValue: 'postgres-password', description: 'Jenkins Secret Text credentials ID for PostgreSQL password.')
        booleanParam(name: 'PULL_IMAGE_BEFORE_DEPLOY', defaultValue: true, description: 'Pull the image tag from a registry before docker compose up.')
        booleanParam(name: 'KEEP_DEPLOYED', defaultValue: false, description: 'Leave the docker compose stack running after a successful deployment.')
    }

    environment {
        COMPOSE_ENV_FILE = '.jenkins.env'
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
                        'DOCKER_IMAGE_TAG',
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
                    env.RESOLVED_IMAGE_TAG = params.DOCKER_IMAGE_TAG.trim()
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

        stage('Pull Docker Image') {
            when {
                expression { params.PULL_IMAGE_BEFORE_DEPLOY && env.RESOLVED_IMAGE_NAME.contains('/') }
            }
            steps {
                powershell '''
$ErrorActionPreference = 'Stop'
docker pull "$env:RESOLVED_IMAGE_NAME`:$env:RESOLVED_IMAGE_TAG"
if ($LASTEXITCODE -ne 0) {
    throw 'Docker image pull failed.'
}
'''
            }
        }

        stage('Start Compose Stack') {
            steps {
                powershell 'docker compose --env-file .jenkins.env up -d postgres api'
            }
        }

        stage('Seed PostgreSQL') {
            steps {
                powershell 'docker compose --env-file .jenkins.env --profile seed run --rm db-seed'
            }
        }

        stage('Wait For API Health') {
            steps {
                powershell '''
$ErrorActionPreference = 'Stop'
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$env:RESOLVED_APP_PORT/health" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            return
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
'''
            }
        }

        stage('Run Functional Scenario') {
            steps {
                powershell '''
$ErrorActionPreference = 'Stop'
docker compose --env-file .jenkins.env exec -T api python tests/functional/run_scenario.py --scenario /app/scenario.json --base-url http://127.0.0.1:8000 --report /app/artifacts/functional-test-report.json
$containerId = docker compose --env-file .jenkins.env ps -q api
if (-not $containerId) {
    throw 'API container was not found after functional test execution.'
}
docker cp "$containerId`:/app/artifacts/functional-test-report.json" functional-test-report.json
'''
            }
        }
    }

    post {
        always {
            script {
                if (fileExists(env.COMPOSE_ENV_FILE)) {
                    powershell(returnStatus: true, script: 'docker compose --env-file .jenkins.env logs')
                    if (!params.KEEP_DEPLOYED || currentBuild.currentResult != 'SUCCESS') {
                        powershell(returnStatus: true, script: 'docker compose --env-file .jenkins.env down -v --remove-orphans')
                    }
                    powershell(returnStatus: true, script: 'Remove-Item .jenkins.env -Force')
                }
            }

            archiveArtifacts(
                artifacts: 'functional-test-report.json',
                allowEmptyArchive: true,
                onlyIfSuccessful: false,
            )
        }
    }
}