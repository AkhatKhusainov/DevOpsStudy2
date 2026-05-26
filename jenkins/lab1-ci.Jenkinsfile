pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        string(name: 'DOCKER_IMAGE_NAME', defaultValue: 'wine-quality-mlops', description: 'Docker image name. For Docker Hub push use username/repository.')
        string(name: 'DOCKER_IMAGE_TAG', defaultValue: '', description: 'Optional Docker image tag. Leave empty to use build-BUILD_NUMBER.')
        string(name: 'DOCKERHUB_CREDENTIALS_ID', defaultValue: 'dockerhub-credentials', description: 'Jenkins Username/Password credentials ID for Docker Hub login.')
        booleanParam(name: 'TRIGGER_CD', defaultValue: false, description: 'Trigger the Lab 1 CD functional pipeline after a successful push.')
        string(name: 'CD_JOB_NAME', defaultValue: 'WineQuality-Lab1-CD', description: 'Jenkins job name for the Lab 1 CD pipeline.')
    }

    environment {
        VENV_DIR = '.venv'
        COVERAGE_FILE = 'coverage.xml'
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
                    env.RESOLVED_IMAGE_NAME = params.DOCKER_IMAGE_NAME?.trim() ? params.DOCKER_IMAGE_NAME.trim() : 'wine-quality-mlops'
                    env.RESOLVED_IMAGE_TAG = params.DOCKER_IMAGE_TAG?.trim() ? params.DOCKER_IMAGE_TAG.trim() : "build-${env.BUILD_NUMBER}"
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
                powershell '''
$ErrorActionPreference = 'Stop'
$env:DOCKER_IMAGE_NAME = $env:RESOLVED_IMAGE_NAME
$env:DOCKER_IMAGE_TAG = $env:RESOLVED_IMAGE_TAG
docker compose build api
if ($LASTEXITCODE -ne 0) {
    throw 'Docker image build failed.'
}
'''
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: params.DOCKERHUB_CREDENTIALS_ID, usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')
                ]) {
                    powershell '''
$ErrorActionPreference = 'Stop'
if ($env:RESOLVED_IMAGE_NAME -notmatch '/') {
    throw 'For Docker Hub push set DOCKER_IMAGE_NAME as username/repository, for example yourname/wine-quality-mlops.'
}
$env:DOCKERHUB_TOKEN | docker login --username "$env:DOCKERHUB_USERNAME" --password-stdin
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Hub login failed.'
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
        }

        stage('Generate DevSecOps Metadata') {
            steps {
                powershell '''
& "./.venv/Scripts/python.exe" scripts/generate_dev_sec_ops.py --image-ref "$env:RESOLVED_IMAGE_NAME`:$env:RESOLVED_IMAGE_TAG" --coverage-xml coverage.xml --output dev_sec_ops.yml
'''
            }
        }

        stage('Trigger Lab 1 CD') {
            when {
                expression { params.TRIGGER_CD }
            }
            steps {
                build job: params.CD_JOB_NAME,
                    wait: false,
                    parameters: [
                        string(name: 'DOCKER_IMAGE_NAME', value: env.RESOLVED_IMAGE_NAME),
                        string(name: 'DOCKER_IMAGE_TAG', value: env.RESOLVED_IMAGE_TAG),
                    ]
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'coverage.xml,dev_sec_ops.yml,artifacts/metrics.json',
                allowEmptyArchive: true,
                onlyIfSuccessful: false,
            )
        }
    }
}