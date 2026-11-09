import numpy as np
import pandas as pd


def validate_model_data(
    df: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str = "model data",
) -> None:
    """Проверка структуры и качества модельной выборки."""

    if df.empty:
        raise ValueError(f"{dataset_name}: выборка пуста")

    columns = set(required_columns) | {
        "user_id",
        "answered_24h",
        "returned_30d",
    }

    missing_columns = columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{dataset_name}: отсутствуют столбцы "
            f"{sorted(missing_columns)}"
        )

    if df["user_id"].isna().any():
        raise ValueError(
            f"{dataset_name}: пропущены user_id"
        )

    if not df["user_id"].is_unique:
        raise ValueError(
            f"{dataset_name}: обнаружены дубликаты user_id"
        )

    null_counts = (
        df[list(columns)]
        .isna()
        .sum()
    )

    missing = null_counts[null_counts > 0]

    if not missing.empty:
        raise ValueError(
            f"{dataset_name}: пропуски:\n"
            f"{missing.to_string()}"
        )

    for column in ("answered_24h", "returned_30d"):
        if not df[column].isin([0, 1, True, False]).all():
            raise ValueError(
                f"{dataset_name}: недопустимые значения {column}"
            )

        if df[column].nunique() != 2:
            raise ValueError(
                f"{dataset_name}: для {column} "
                "не представлены оба класса"
            )

    if "account_age_group" in required_columns:
        if "under_one_day" not in set(df["account_age_group"]):
            raise ValueError(
                f"{dataset_name}: отсутствует опорная "
                "категория возраста under_one_day"
            )
    
    # Проверка конечности числовых значений
    numeric_columns = [
        col for col in columns
        if pd.api.types.is_numeric_dtype(df[col])
    ]

    if numeric_columns:
        numeric_values = df[numeric_columns].to_numpy(
            dtype=float
        )

        if not np.isfinite(numeric_values).all():
            raise ValueError(
                f"{dataset_name}: обнаружены бесконечные "
                "или некорректные числовые значения"
            )

    # Проверка допустимых диапазонов
    numeric_ranges = {
        "title_length": (1, None),
        "tags_count": (0, None),
        "question_hour": (0, 23),
        "question_month": (1, 12),
        "question_weekday": (1, 7),
    }

    integer_columns = {
        "tags_count",
        "question_hour",
        "question_month",
        "question_weekday",
    }

    for col, (minimum, maximum) in numeric_ranges.items():
        if col not in df.columns:
            continue

        values = pd.to_numeric(df[col], errors="coerce")

        if values.isna().any():
            raise ValueError(
                f"{dataset_name}: столбец {col} содержит "
                "пропуски или нечисловые значения"
            )

        values = values.to_numpy(dtype=float)

        if not np.isfinite(values).all():
            raise ValueError(
                f"{dataset_name}: столбец {col} содержит "
                "NaN или бесконечные значения"
            )

        if (values < minimum).any():
            raise ValueError(
                f"{dataset_name}: значения {col} "
                f"должны быть >= {minimum}"
            )

        if maximum is not None and (values > maximum).any():
            raise ValueError(
                f"{dataset_name}: значения {col} "
                f"должны быть <= {maximum}"
            )

        if col in integer_columns:
            if (values % 1 != 0).any():
                raise ValueError(
                    f"{dataset_name}: столбец {col} "
                    "должен содержать целые числа"
                )



def verify_reference_counts(
    df: pd.DataFrame,
    expected_users: int,
    expected_returns: int,
    expected_answers: int,
) -> None:
    """Сверка с историческим снимком исследования."""

    actual = {
        "users": len(df),
        "returns": int(df["returned_30d"].sum()),
        "answers": int(df["answered_24h"].sum()),
    }

    expected = {
        "users": expected_users,
        "returns": expected_returns,
        "answers": expected_answers,
    }

    if actual != expected:
        raise ValueError(
            "Исторические результаты не совпадают.\n"
            f"Ожидалось: {expected}\n"
            f"Получено: {actual}"
        )

    print("Исторические контрольные значения совпадают")