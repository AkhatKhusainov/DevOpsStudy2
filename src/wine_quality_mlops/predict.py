from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import joblib
import pandas as pd


class ModelService:
    def __init__(self, model: object, metadata: dict[str, object], metrics: dict[str, object]) -> None:
        self._model = model
        self.metadata = metadata
        self.metrics = metrics
        self.feature_columns = tuple(metadata["feature_columns"])

    @classmethod
    def from_paths(
        cls,
        model_path: str | Path,
        metadata_path: str | Path,
        metrics_path: str | Path,
    ) -> "ModelService":
        model = joblib.load(model_path)
        metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
        metrics = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
        return cls(model=model, metadata=metadata, metrics=metrics)

    def predict(self, payload: Mapping[str, float]) -> float:
        row = pd.DataFrame([[payload[column] for column in self.feature_columns]], columns=self.feature_columns)
        prediction = float(self._model.predict(row)[0])
        return round(prediction, 4)
