# Wine Quality MLOps Lab2

Учебный проект для второй лабораторной работы по CI/CD для ML-модели на датасете Wine Quality.

## Что реализовано

- подготовка данных для `winequality-red.csv`;
- регрессионная модель `RandomForestRegressor` для предсказания `quality`;
- API-сервис на FastAPI с методом `/predict`;
- сохранение результатов предсказаний в PostgreSQL;
- загрузка train/test наборов в PostgreSQL отдельным seed-скриптом;
- unit и API tests на `pytest`;
- DVC pipeline для этапов `prepare` и `train`;
- Docker image и `docker-compose.yml`;
- GitHub Actions workflows для Lab2 CI и Lab2 CD;
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

- `Lab2 CI`: workflow `.github/workflows/ci.yml` запускается по `pull_request` в `main`, прогоняет `dvc repro`, `pytest`, собирает Docker image и отправляет его в Docker Hub repo `ntfs121/wine-quality-mlops-lab2`.
- `Lab2 CD`: workflow `.github/workflows/cd.yml` запускается вручную, по расписанию или после успешного `Lab2 CI`, поднимает стек через `docker compose` и выполняет функциональный сценарий.

## Jenkins

Для Jenkins в этом репозитории нужны только lab2 pipeline файлы:

- `jenkins/lab2-ci.Jenkinsfile` — CI для второй лабы: сборка Docker image, push в Docker Hub, проверка PostgreSQL seed и функционального сценария через `docker-compose`.
- `jenkins/lab2-cd.Jenkinsfile` — CD для второй лабы: развёртывание стека `postgres + api`, загрузка train/test данных и функциональная проверка.

Минимальные Jenkins credentials:

- `postgres-password` как Secret text с паролем PostgreSQL для `lab2-ci` и `lab2-cd`.
- `dockerhub-credentials` как Username/Password credential для Docker Hub push из `lab2-ci`.

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

## Результаты

- материалы по второй лабораторной работе находятся в `Результаты_работы/Лаба2/`.

## Цитирование датасета

P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis.
Modeling wine preferences by data mining from physicochemical properties.
Decision Support Systems, Elsevier, 47(4):547-553, 2009.
