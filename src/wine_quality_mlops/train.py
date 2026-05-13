from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from wine_quality_mlops.config import load_settings
from wine_quality_mlops.schema import FEATURE_COLUMNS, TARGET_COLUMN


def build_model(config_path: str | Path) -> RandomForestRegressor:
    settings = load_settings(config_path)

    if settings.model.model_type != "random_forest_regressor":
        raise ValueError(f"Unsupported model type: {settings.model.model_type}")

    return RandomForestRegressor(
        n_estimators=settings.model.n_estimators,
        max_depth=settings.model.max_depth,
        min_samples_split=settings.model.min_samples_split,
        random_state=settings.data.random_state,
        n_jobs=-1,
    )


def train_model(
    train_path: str | Path,
    test_path: str | Path,
    artifacts_dir: str | Path,
    config_path: str | Path,
) -> dict[str, object]:
    train_frame = pd.read_csv(train_path)
    test_frame = pd.read_csv(test_path)
    artifacts_path = Path(artifacts_dir)
    artifacts_path.mkdir(parents=True, exist_ok=True)
    settings = load_settings(config_path)

    model = build_model(config_path)
    model.fit(train_frame.loc[:, FEATURE_COLUMNS], train_frame[TARGET_COLUMN])

    predictions = model.predict(test_frame.loc[:, FEATURE_COLUMNS])
    rmse = math.sqrt(mean_squared_error(test_frame[TARGET_COLUMN], predictions))
    metrics = {
        "model_type": settings.model.model_type,
        "mae": round(float(mean_absolute_error(test_frame[TARGET_COLUMN], predictions)), 6),
        "rmse": round(float(rmse), 6),
        "r2": round(float(r2_score(test_frame[TARGET_COLUMN], predictions)), 6),
        "train_rows": int(len(train_frame)),
        "test_rows": int(len(test_frame)),
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    metadata = {
        "feature_columns": list(FEATURE_COLUMNS),
        "target_column": TARGET_COLUMN,
        "model_type": settings.model.model_type,
        "version": settings.app.version,
        "trained_at": metrics["trained_at"],
    }

    joblib.dump(model, artifacts_path / "model.joblib")
    (artifacts_path / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (artifacts_path / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train wine quality model.")
    parser.add_argument("--train-path", required=True)
    parser.add_argument("--test-path", required=True)
    parser.add_argument("--artifacts-dir", required=True)
    parser.add_argument("--config", default="config.ini")
    args = parser.parse_args()

    metrics = train_model(args.train_path, args.test_path, args.artifacts_dir, args.config)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
