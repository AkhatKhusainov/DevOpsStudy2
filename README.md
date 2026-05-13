# Wine Quality MLOps

Учебный проект для задания по CI/CD для ML-модели на датасете Wine Quality.

## Что реализовано

- подготовка данных для `winequality-red.csv`;
- регрессионная модель `RandomForestRegressor` для предсказания `quality`;
- API-сервис на FastAPI с методом `/predict`;
- unit и API tests на `pytest`;
- DVC pipeline для этапов `prepare` и `train`;
- Docker image и `docker-compose.yml`;
- GitHub Actions workflows для CI и CD;
- служебные файлы `config.ini`, `dev_sec_ops.yml`, `scenario.json`.

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
uvicorn --app-dir src wine_quality_mlops.app:app --host 0.0.0.0 --port 8000
```

## DVC pipeline

```powershell
dvc repro
```

## Docker

```powershell
docker build -t wine-quality-mlops:local .
docker run --rm -p 8000:8000 wine-quality-mlops:local
```

## CI/CD

- `CI`: запускается по `pull_request` в `main`, прогоняет `dvc repro`, `pytest`, собирает Docker image и отправляет его в DockerHub.
- `CD`: запускается вручную, по расписанию или после успешного `CI`, поднимает контейнер и выполняет функциональный сценарий внутри контейнера.

## GitHub и DockerHub

Перед использованием workflows нужно задать secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## Цитирование датасета

P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis.
Modeling wine preferences by data mining from physicochemical properties.
Decision Support Systems, Elsevier, 47(4):547-553, 2009.
