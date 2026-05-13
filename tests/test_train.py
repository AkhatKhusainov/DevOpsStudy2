from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from wine_quality_mlops.schema import ALL_COLUMNS
from wine_quality_mlops.train import train_model


def test_train_model_persists_artifacts(tmp_path: Path) -> None:
    train_path = tmp_path / "train.csv"
    test_path = tmp_path / "test.csv"
    artifacts_dir = tmp_path / "artifacts"
    config_path = tmp_path / "config.ini"

    frame = pd.DataFrame(
        [
            [7.4, 0.70, 0.00, 1.9, 0.076, 11, 34, 0.9978, 3.51, 0.56, 9.4, 5],
            [7.8, 0.88, 0.00, 2.6, 0.098, 25, 67, 0.9968, 3.20, 0.68, 9.8, 5],
            [11.2, 0.28, 0.56, 1.9, 0.075, 17, 60, 0.9980, 3.16, 0.58, 9.8, 6],
            [7.9, 0.60, 0.06, 1.6, 0.069, 15, 59, 0.9964, 3.30, 0.46, 9.4, 5],
            [7.3, 0.65, 0.02, 2.1, 0.070, 10, 37, 0.9966, 3.39, 0.47, 10.0, 7],
            [7.5, 0.50, 0.36, 6.1, 0.071, 17, 102, 0.9980, 3.35, 0.80, 10.5, 7],
            [6.7, 0.45, 0.12, 3.2, 0.066, 12, 48, 0.9956, 3.28, 0.54, 11.2, 6],
            [6.2, 0.39, 0.24, 2.7, 0.070, 23, 85, 0.9963, 3.26, 0.63, 10.8, 6],
        ],
        columns=ALL_COLUMNS,
    )
    frame.iloc[:6].to_csv(train_path, index=False)
    frame.iloc[6:].to_csv(test_path, index=False)
    config_path.write_text(
        """
[app]
project_name = Test
version = 0.1.0

[data]
test_size = 0.25
random_state = 42
drop_duplicates = true

[model]
model_type = random_forest_regressor
n_estimators = 20
max_depth = 5
min_samples_split = 2
""".strip(),
        encoding="utf-8",
    )

    metrics = train_model(train_path, test_path, artifacts_dir, config_path)

    assert (artifacts_dir / "model.joblib").exists()
    assert (artifacts_dir / "metrics.json").exists()
    assert (artifacts_dir / "model_metadata.json").exists()
    assert metrics["model_type"] == "random_forest_regressor"

    persisted_metrics = json.loads((artifacts_dir / "metrics.json").read_text(encoding="utf-8"))
    assert "mae" in persisted_metrics
    assert "rmse" in persisted_metrics
    assert "r2" in persisted_metrics
