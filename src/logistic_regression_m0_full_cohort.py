import argparse

import numpy as np
import pandas as pd
import psycopg
import statsmodels.api as sm

from data_validation import (
    validate_model_data,
    verify_reference_counts,
)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--verify-reference",
    action="store_true",
    help="Проверить совпадение с исходной когортой 2023 года",
)

args = parser.parse_args()


# 1. Загружаем данные из PostgreSQL
query = """
SELECT
    user_id,
    answered_24h::INT AS answered_24h,
    returned_30d::INT AS returned_30d
FROM analytics.user_model_features_2023
"""

with psycopg.connect("dbname=stackexchange_analytics") as conn:
    rows = conn.execute(query).fetchall()

df = pd.DataFrame(
    rows,
    columns=[
        "user_id",
        "answered_24h",
        "returned_30d",
    ],
)

# 2. Проверяем качество данных
validate_model_data(
    df,
    required_columns=[],
    dataset_name="M0: полная когорта",
)

# Дополнительная сверка с историческими результатами
if args.verify_reference:
    verify_reference_counts(
        df,
        expected_users=5240,
        expected_returns=550,
        expected_answers=2119,
    )

print("Количество пользователей:", len(df))
print("\nТаблица сопряжённости:")
print(pd.crosstab(
    df["answered_24h"],
    df["returned_30d"]
))

# 3. Строим логистическую регрессию
X = sm.add_constant(df[["answered_24h"]])
y = df["returned_30d"]

model = sm.Logit(y, X)
result = model.fit(disp=False)

# 4. Извлекаем основной коэффициент
coef = result.params["answered_24h"]
p_value = result.pvalues["answered_24h"]

ci_lower, ci_upper = result.conf_int().loc[
    "answered_24h"
]

# 5. Переводим коэффициент в Odds Ratio
odds_ratio = np.exp(coef)
or_lower = np.exp(ci_lower)
or_upper = np.exp(ci_upper)

print("\n=== Логистическая регрессия M0 ===")
print(result.summary())

print("\n=== Основной результат ===")
print(f"Коэффициент: {coef:.4f}")
print(f"Odds Ratio: {odds_ratio:.4f}")
print(f"95% CI: [{or_lower:.4f}; {or_upper:.4f}]")
print(f"p-value: {p_value:.6f}")
print(f"Сходимость: {result.mle_retvals['converged']}")