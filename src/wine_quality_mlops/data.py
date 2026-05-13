from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from wine_quality_mlops.config import load_settings
from wine_quality_mlops.schema import ALL_COLUMNS, TARGET_COLUMN


def normalize_column_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def prepare_dataset(raw_path: str | Path, output_dir: str | Path, config_path: str | Path) -> dict[str, object]:
    settings = load_settings(config_path)
    input_path = Path(raw_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    dataset = pd.read_csv(input_path, sep=";")
    rows_before = len(dataset)
    dataset.columns = [normalize_column_name(column) for column in dataset.columns]

    missing_columns = sorted(set(ALL_COLUMNS) - set(dataset.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    dataset = dataset.loc[:, list(ALL_COLUMNS)]
    if settings.data.drop_duplicates:
        dataset = dataset.drop_duplicates().reset_index(drop=True)

    rows_after = len(dataset)
    train_frame, test_frame = train_test_split(
        dataset,
        test_size=settings.data.test_size,
        random_state=settings.data.random_state,
        stratify=dataset[TARGET_COLUMN],
    )

    train_frame.to_csv(destination / "train.csv", index=False)
    test_frame.to_csv(destination / "test.csv", index=False)

    summary = {
        "input_path": str(input_path),
        "rows_before": rows_before,
        "rows_after": rows_after,
        "duplicates_removed": rows_before - rows_after,
        "train_rows": len(train_frame),
        "test_rows": len(test_frame),
        "feature_columns": list(ALL_COLUMNS[:-1]),
        "target_column": TARGET_COLUMN,
        "quality_distribution": dataset[TARGET_COLUMN].value_counts().sort_index().to_dict(),
    }

    (destination / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare wine quality dataset.")
    parser.add_argument("--input", required=True, dest="input_path")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config", default="config.ini")
    args = parser.parse_args()

    summary = prepare_dataset(args.input_path, args.output_dir, args.config)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
