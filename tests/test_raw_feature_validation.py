import numpy as np
import pandas as pd
import pytest

from src.data_validation import (
    TAG_COLUMNS,
    RAW_NUMERIC_COLUMNS,
    validate_raw_features,
)


@pytest.fixture
def raw_df():
    """Корректная исходная выборка до преобразований."""
    df = pd.DataFrame({
        "user_id": [101, 102, 103, 104],
        "answered_24h": [0, 1, 0, 1],
        "returned_30d": [0, 1, 1, 0],
        "first_question_at": pd.to_datetime([
            "2023-01-10",
            "2023-03-12",
            "2023-06-15",
            "2023-12-20",
        ]),
        "account_age_group": [
            "under_one_day",
            "thirty_plus_days",
            "one_to_thirty_days",
            "under_one_day",
        ],
        "title_length": [12, 25, 19, 32],
        "tags_count": [1, 3, 2, 5],
        "question_hour": [0, 9, 23, 14],
        "question_month": [1, 3, 6, 12],
        "question_weekday": [1, 3, 5, 7],
    })

    for tag in TAG_COLUMNS:
        df[tag] = [0, 1, 0, 1]

    return df


def validate(df):
    validate_raw_features(
        df,
        dataset_name="Тестовая исходная выборка",
    )


def test_valid_raw_data(raw_df):
    validate(raw_df)


@pytest.mark.parametrize("tag", TAG_COLUMNS)
def test_invalid_tag_string(raw_df, tag):
    df = raw_df.copy()
    df[tag] = df[tag].astype(object)
    df.loc[0, tag] = "unknown"

    with pytest.raises(ValueError, match=tag):
        validate(df)


@pytest.mark.parametrize("tag", TAG_COLUMNS)
def test_invalid_tag_value(raw_df, tag):
    df = raw_df.copy()
    df.loc[0, tag] = 2

    with pytest.raises(ValueError, match=tag):
        validate(df)


@pytest.mark.parametrize("tag", TAG_COLUMNS)
def test_float_tag_type(raw_df, tag):
    df = raw_df.copy()
    df[tag] = df[tag].astype(float)

    with pytest.raises(ValueError, match="целые значения"):
        validate(df)


@pytest.mark.parametrize("column", RAW_NUMERIC_COLUMNS)
def test_numeric_feature_as_string(raw_df, column):
    df = raw_df.copy()
    df[column] = df[column].astype(str)

    with pytest.raises(ValueError, match="числовой тип"):
        validate(df)


def test_missing_raw_column(raw_df):
    df = raw_df.drop(columns=["has_regression"])

    with pytest.raises(ValueError, match="отсутствуют столбцы"):
        validate(df)


def test_missing_question_timestamp(raw_df):
    df = raw_df.copy()
    df.loc[0, "first_question_at"] = pd.NaT

    with pytest.raises(ValueError, match="пропуски"):
        validate(df)


def test_invalid_hour(raw_df):
    df = raw_df.copy()
    df.loc[0, "question_hour"] = 24

    with pytest.raises(ValueError, match="question_hour"):
        validate(df)


def test_infinite_numeric_feature(raw_df):
    df = raw_df.copy()
    df["title_length"] = df["title_length"].astype(float)
    df.loc[0, "title_length"] = np.inf

    with pytest.raises(ValueError, match="бесконечные"):
        validate(df)


def test_boolean_tags_are_valid(raw_df):
    df = raw_df.copy()

    for tag in TAG_COLUMNS:
        df[tag] = df[tag].astype(bool)

    validate(df)