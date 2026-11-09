import numpy as np
import pandas as pd
import pytest

from src.data_validation import (
    validate_model_data,
    verify_reference_counts,
)


REQUIRED_COLUMNS = [
    "account_age_group",
    "title_length",
    "tags_count",
    "question_hour",
    "question_month",
    "question_weekday",
]


@pytest.fixture
def valid_df():
    """Небольшая корректная модельная выборка."""
    return pd.DataFrame({
        "user_id": [101, 102, 103, 104],
        "answered_24h": [0, 1, 0, 1],
        "returned_30d": [0, 1, 1, 0],
        "account_age_group": [
            "under_one_day",
            "thirty_plus_days",
            "one_to_thirty_days",
            "under_one_day",
        ],
        "title_length": [12, 25, 19, 32],
        "tags_count": [1, 3, 0, 5],
        "question_hour": [0, 9, 23, 14],
        "question_month": [1, 6, 12, 11],
        "question_weekday": [1, 3, 7, 5],
        "title_length_10": [1.2, 2.5, 1.9, 3.2],
    })


def validate(df):
    validate_model_data(
        df,
        required_columns=REQUIRED_COLUMNS + ["title_length_10"],
        dataset_name="Тестовая выборка",
    )


# 1. Корректные данные
def test_valid_data_passes(valid_df):
    validate(valid_df)


# 2. Пустая выборка
def test_empty_dataframe(valid_df):
    with pytest.raises(ValueError, match="выборка пуста"):
        validate(valid_df.iloc[:0])


# 3. Отсутствует обязательный столбец
def test_missing_column(valid_df):
    df = valid_df.drop(columns=["tags_count"])

    with pytest.raises(ValueError, match="отсутствуют столбцы"):
        validate(df)


# 4. Пропущенный user_id
def test_missing_user_id(valid_df):
    df = valid_df.copy()
    df.loc[0, "user_id"] = np.nan

    with pytest.raises(ValueError, match="пропущены user_id"):
        validate(df)


# 5. Дублирующийся user_id
def test_duplicate_user_id(valid_df):
    df = valid_df.copy()
    df.loc[1, "user_id"] = 101

    with pytest.raises(ValueError, match="дубликаты user_id"):
        validate(df)


# 6. Пропуски в модельных признаках
@pytest.mark.parametrize("column", [
    "title_length",
    "tags_count",
    "question_hour",
    "account_age_group",
])
def test_missing_feature(valid_df, column):
    df = valid_df.copy()
    df.loc[0, column] = np.nan

    with pytest.raises(ValueError, match="пропуски"):
        validate(df)


# 7. Недопустимые значения бинарных переменных
@pytest.mark.parametrize("column", [
    "answered_24h",
    "returned_30d",
])
def test_invalid_binary_value(valid_df, column):
    df = valid_df.copy()
    df.loc[0, column] = 2

    with pytest.raises(ValueError, match="недопустимые значения"):
        validate(df)


# 8. В целевой переменной представлен один класс
@pytest.mark.parametrize("column", [
    "answered_24h",
    "returned_30d",
])
def test_single_class(valid_df, column):
    df = valid_df.copy()
    df[column] = 1

    with pytest.raises(ValueError, match="не представлены оба класса"):
        validate(df)


# 9. Нет опорной категории возраста аккаунта
def test_missing_reference_category(valid_df):
    df = valid_df.copy()
    df["account_age_group"] = "thirty_plus_days"

    with pytest.raises(ValueError, match="under_one_day"):
        validate(df)


# 10. Бесконечные числовые значения
@pytest.mark.parametrize("value", [
    np.inf,
    -np.inf,
])
def test_infinite_values(valid_df, value):
    df = valid_df.copy()
    df.loc[0, "title_length_10"] = value

    with pytest.raises(ValueError, match="бесконечные"):
        validate(df)


# 11. Недопустимые диапазоны
@pytest.mark.parametrize("column,value", [
    ("title_length", 0),
    ("tags_count", -1),
    ("question_hour", -1),
    ("question_hour", 24),
    ("question_month", 0),
    ("question_month", 13),
    ("question_weekday", 0),
    ("question_weekday", 8),
])
def test_invalid_range(valid_df, column, value):
    df = valid_df.copy()
    df.loc[0, column] = value

    with pytest.raises(ValueError, match=column):
        validate(df)


# 12. Дробные значения вместо целых
@pytest.mark.parametrize("column,value", [
    ("tags_count", 2.5),
    ("question_hour", 12.5),
    ("question_month", 6.5),
    ("question_weekday", 3.5),
])
def test_non_integer_values(valid_df, column, value):
    df = valid_df.copy()

    df[column] = df[column].astype(float)
    df.loc[0, column] = value

    with pytest.raises(ValueError, match="целые числа"):
        validate(df)


# 13. Нечисловое значение
def test_non_numeric_value(valid_df):
    df = valid_df.copy()
    df["question_hour"] = df["question_hour"].astype(object)
    df.loc[0, "question_hour"] = "unknown"

    with pytest.raises(ValueError, match="нечисловые"):
        validate(df)


# 14. Исторические значения совпадают
def test_reference_counts_match(valid_df):
    verify_reference_counts(
        valid_df,
        expected_users=4,
        expected_returns=2,
        expected_answers=2,
    )


# 15. Исторические значения не совпадают
@pytest.mark.parametrize(
    "expected_users,expected_returns,expected_answers",
    [
        (5, 2, 2),
        (4, 3, 2),
        (4, 2, 3),
    ],
)
def test_reference_counts_mismatch(
    valid_df,
    expected_users,
    expected_returns,
    expected_answers,
):
    with pytest.raises(ValueError, match="не совпадают"):
        verify_reference_counts(
            valid_df,
            expected_users=expected_users,
            expected_returns=expected_returns,
            expected_answers=expected_answers,
        )