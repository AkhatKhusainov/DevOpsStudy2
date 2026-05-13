from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel, Field

from wine_quality_mlops.predict import ModelService


DEFAULT_MODEL_PATH = Path("artifacts/model.joblib")
DEFAULT_METADATA_PATH = Path("artifacts/model_metadata.json")
DEFAULT_METRICS_PATH = Path("artifacts/metrics.json")


class PredictionRequest(BaseModel):
    fixed_acidity: float = Field(..., ge=0)
    volatile_acidity: float = Field(..., ge=0)
    citric_acid: float = Field(..., ge=0)
    residual_sugar: float = Field(..., ge=0)
    chlorides: float = Field(..., ge=0)
    free_sulfur_dioxide: float = Field(..., ge=0)
    total_sulfur_dioxide: float = Field(..., ge=0)
    density: float = Field(..., ge=0)
    ph: float = Field(..., ge=0)
    sulphates: float = Field(..., ge=0)
    alcohol: float = Field(..., ge=0)


class PredictionResponse(BaseModel):
    predicted_quality: float
    model_version: str


def _artifact_path(env_name: str, default_path: Path) -> Path:
    return Path(os.getenv(env_name, default_path.as_posix()))


def get_model_service(request: Request) -> ModelService:
    return request.app.state.model_service


def create_app(service: ModelService | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.model_service = service or ModelService.from_paths(
            model_path=_artifact_path("MODEL_PATH", DEFAULT_MODEL_PATH),
            metadata_path=_artifact_path("METADATA_PATH", DEFAULT_METADATA_PATH),
            metrics_path=_artifact_path("METRICS_PATH", DEFAULT_METRICS_PATH),
        )
        yield

    app = FastAPI(title="Wine Quality MLOps API", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/model-info")
    def model_info(model_service: ModelService = Depends(get_model_service)) -> dict[str, object]:
        return {
            "model_type": model_service.metadata.get("model_type"),
            "feature_columns": list(model_service.feature_columns),
            "metrics": model_service.metrics,
        }

    @app.post("/predict", response_model=PredictionResponse)
    def predict(
        request: PredictionRequest,
        model_service: ModelService = Depends(get_model_service),
    ) -> PredictionResponse:
        prediction = model_service.predict(request.model_dump())
        return PredictionResponse(
            predicted_quality=prediction,
            model_version=str(model_service.metadata.get("version", "0.1.0")),
        )

    return app


app = create_app()
