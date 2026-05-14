# Wine Quality MLOps

Учебный проект для двух лабораторных работ:

- CI/CD для ML-модели на датасете Wine Quality;
- взаимодействие сервиса модели с PostgreSQL через `docker-compose`.

## Что реализовано

- подготовка данных для `winequality-red.csv`;
- регрессионная модель `RandomForestRegressor` для предсказания `quality`;
- API-сервис на FastAPI с методом `/predict`;
- сохранение результатов предсказаний в PostgreSQL;
- загрузка train/test наборов в PostgreSQL отдельным seed-скриптом;
- unit и API tests на `pytest`;
- DVC pipeline для этапов `prepare` и `train`;
- Docker image и `docker-compose.yml`;
- GitHub Actions workflows для CI и CD;
- служебные файлы `config.ini`, `dev_sec_ops.yml`, `scenario.json`, `.env.example`.

## Структура

```text
.
|-- .github/workflows/
|-- artifacts/
|-- data/
|   |-- raw/
|   `-- processed/
|-- notebooks/
|-- scripts/
|-- src/wine_quality_mlops/
`-- tests/
```

## Быстрый старт

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/prepare_data.py --input data/raw/winequality-red.csv --output-dir data/processed --config config.ini
python scripts/train_model.py --train-path data/processed/train.csv --test-path data/processed/test.csv --artifacts-dir artifacts --config config.ini
pytest --cov=src/wine_quality_mlops --cov-report=xml --cov-report=term-missing
```

Для локального запуска с PostgreSQL:

```powershell
Copy-Item .env.example .env
docker compose build api
docker compose up -d postgres api
docker compose --profile seed run --rm db-seed
docker compose exec api python tests/functional/run_scenario.py --scenario /app/scenario.json --base-url http://127.0.0.1:8000 --report /app/artifacts/functional-test-report.json
docker compose down -v
```

## DVC pipeline

```powershell
dvc repro
```

## Docker

```powershell
docker compose build api
docker compose up -d postgres api
docker compose --profile seed run --rm db-seed
```

`docker-compose.yml` используется обязательно: он поднимает PostgreSQL, API и отдельный seed-контейнер для загрузки обучающего и тестового наборов в базу.

## Переменные окружения

Настройки PostgreSQL и image tag не захардкожены в исходном коде. Их нужно передавать через переменные окружения или `.env`.

Используются переменные:

- `DOCKER_IMAGE_NAME`
- `DOCKER_IMAGE_TAG`
- `APP_PORT`
- `DATABASE_HOST`
- `DATABASE_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`

Пример структуры есть в `.env.example`.

Для локального запуска скопируй `.env.example` в `.env` и задай свои значения подключения.

## API

- `GET /health` возвращает состояние сервиса и подключения к БД;
- `GET /training-data/summary` показывает количество train/test записей в PostgreSQL;
- `POST /predict` считает предсказание и сохраняет результат в PostgreSQL;
- `GET /predictions/latest` возвращает последнее сохранённое предсказание.

## CI/CD

- `Lab1 CI`: workflow `.github/workflows/ci.yml` запускается по `pull_request` в `main`, прогоняет `dvc repro`, `pytest`, собирает Docker image и отправляет его в Docker Hub.
- `Lab1 CD`: workflow `.github/workflows/cd.yml` запускается вручную, по расписанию или после успешного `Lab1 CI`, поднимает стек через `docker compose` и выполняет функциональный сценарий.

## Jenkins

Для раздельной сдачи лучше создать четыре отдельных Pipeline job и указать для каждой свой `Script Path`:

- `Jenkinsfile` — legacy-комбинированный pipeline для полного локального цикла сборки и проверки.
- `jenkins/lab1-ci.Jenkinsfile` — CI для первой лабы: `dvc repro`, `pytest`, сборка Docker image, push в Docker Hub и опциональный вызов CD job.
- `jenkins/lab1-cd.Jenkinsfile` — CD для первой лабы: функциональное тестирование по сценарию через `docker-compose`, ручной запуск или вызов из CI.
- `jenkins/lab2-ci.Jenkinsfile` — CI для второй лабы: сборка Docker image, push в Docker Hub, проверка PostgreSQL seed и функционального сценария через `docker-compose`.
- `jenkins/lab2-cd.Jenkinsfile` — CD для второй лабы: развёртывание стека `postgres + api`, загрузка train/test данных и функциональная проверка.

Минимальные Jenkins credentials:

- `postgres-password` как Secret text с паролем PostgreSQL для `lab1-cd`, `lab2-ci` и `lab2-cd`.

Для `lab1-ci` pipeline использует уже существующий логин Docker на Jenkins agent, поэтому перед первым запуском нужно один раз выполнить `docker login` на самой машине Jenkins.

Корневой `Jenkinsfile` можно оставить как legacy-комбинированный вариант, но для лабораторных лучше использовать отдельные pipeline-файлы из каталога `jenkins/`.

## GitHub и DockerHub

Перед использованием workflows нужно задать secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `POSTGRES_PASSWORD`

И repository variables:

- `APP_PORT`
- `DATABASE_HOST`
- `DATABASE_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`

Значения для подключения к БД нужно задавать через secrets, repository variables, Jenkins parameters или локальный `.env`, а не фиксировать в исходниках.

## Цитирование датасета

P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis.
Modeling wine preferences by data mining from physicochemical properties.
Decision Support Systems, Elsevier, 47(4):547-553, 2009.
