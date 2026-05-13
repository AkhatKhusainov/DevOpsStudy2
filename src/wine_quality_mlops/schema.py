from __future__ import annotations

FEATURE_COLUMNS: tuple[str, ...] = (
    "fixed_acidity",
    "volatile_acidity",
    "citric_acid",
    "residual_sugar",
    "chlorides",
    "free_sulfur_dioxide",
    "total_sulfur_dioxide",
    "density",
    "ph",
    "sulphates",
    "alcohol",
)

TARGET_COLUMN = "quality"
ALL_COLUMNS: tuple[str, ...] = FEATURE_COLUMNS + (TARGET_COLUMN,)
