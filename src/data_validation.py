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