from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from wine_quality_mlops.data import prepare_dataset
from wine_quality_mlops.schema import ALL_COLUMNS


def test_prepare_dataset_creates_expected_outputs(tmp_path: Path) -> None:
    raw_path = tmp_path / "sample.csv"
    output_dir = tmp_path / "processed"
    config_path = tmp_path / "config.ini"

    raw_frame = pd.DataFrame(
        {
            "fixed acidity": [7.4, 7.8, 7.8, 11.2, 7.4, 7.9, 7.3, 7.8, 7.5, 6.7],
            "volatile acidity": [0.70, 0.88, 0.76, 0.28, 0.66, 0.60, 0.65, 0.58, 0.50, 0.45],
            "citric acid": [0.00, 0.00, 0.04, 0.56, 0.00, 0.06, 0.02, 0.02, 0.36, 0.12],
            "residual sugar": [1.9, 2.6, 2.3, 1.9, 1.8, 1.6, 2.1, 1.8, 6.1, 3.2],
            "chlorides": [0.076, 0.098, 0.092, 0.075, 0.075, 0.069, 0.070, 0.073, 0.071, 0.066],
            "free sulfur dioxide": [11, 25, 15, 17, 13, 15, 10, 9, 17, 12],
            "total sulfur dioxide": [34, 67, 54, 60, 40, 59, 37, 18, 102, 48],
            "density": [0.9978, 0.9968, 0.9970, 0.9980, 0.9978, 0.9964, 0.9966, 0.9968, 0.9980, 0.9956],
            "pH": [3.51, 3.20, 3.26, 3.16, 3.51, 3.30, 3.39, 3.36, 3.35, 3.28],
            "sulphates": [0.56, 0.68, 0.65, 0.58, 0.56, 0.46, 0.47, 0.57, 0.80, 0.54],
            "alcohol": [9.4, 9.8, 9.8, 9.8, 9.4, 9.4, 10.0, 9.5, 10.5, 11.2],
            "quality": [5, 5, 5, 6, 5, 5, 7, 6, 7, 6],
        }
    )
    raw_frame.to_csv(raw_path, sep=";", index=False)
    config_path.write_text(
        """
[app]
project_name = Test
version = 0.1.0

[data]
test_size = 0.3
random_state = 42
drop_duplicates = false

[model]
model_type = random_forest_regressor
n_estimators = 10
max_depth = 4
min_samples_split = 2
""".strip(),
        encoding="utf-8",
    )

    summary = prepare_dataset(raw_path, output_dir, config_path)

    assert (output_dir / "train.csv").exists()
    assert (output_dir / "test.csv").exists()
    assert (output_dir / "summary.json").exists()
    assert summary["rows_before"] == 10
    assert summary["rows_after"] == 10

    train_frame = pd.read_csv(output_dir / "train.csv")
    assert tuple(train_frame.columns) == ALL_COLUMNS

    persisted_summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert persisted_summary["target_column"] == "quality"
