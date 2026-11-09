import argparse

import numpy as np
import pandas as pd
import psycopg
import statsmodels.formula.api as smf

from data_validation import (
    validate_model_data,
    verify_reference_counts,
)


parser = argparse.ArgumentParser()

parser.add_argument(
    "--verify-reference",
    action="store_true",
    help="Проверить совпадение с исходной выборкой 2023 года",
)

args = parser.parse_args()


query = """
SELECT
    u.user_id,
    u.answered_24h::INT AS answered_24h,
    u.returned_30d::INT AS returned_30d,

    CASE
        WHEN r.account_created_at = u.first_question_at
            THEN 'same_timestamp'

        WHEN u.first_question_at - r.account_created_at
             < INTERVAL '1 day'
            THEN 'under_one_day'

        WHEN u.first_question_at - r.account_created_at
             < INTERVAL '30 days'
            THEN 'one_to_thirty_days'

        ELSE 'thirty_plus_days'
    END AS account_age_group

FROM analytics.user_model_features_2023 u

JOIN raw.user_registration_2023 r
    ON u.user_id = r.user_id

WHERE r.account_created_at <= u.first_question_at
"""

with psycopg.connect("dbname=stackexchange_analytics") as conn:
    rows = conn.execute(query).fetchall()

df = pd.DataFrame(
    rows,
    columns=[
        "user_id",
        "answered_24h",
        "returned_30d",
        "account_age_group",
    ],
)

# Проверка качества данных
validate_model_data(
    df,
    required_columns=["account_age_group"],
    dataset_name="M1: регрессионная выборка",
)

# Дополнительная сверка с историческими результатами
if args.verify_reference:
    verify_reference_counts(
        df,
        expected_users=5140,
        expected_returns=539,
        expected_answers=2076,
    )

print("Размер выборки:", len(df))

print("\nРаспределение возраста аккаунта:")
print(df["account_age_group"].value_counts())

# M0 на той же выборке, что и M1
m0 = smf.logit(
    "returned_30d ~ answered_24h",
    data=df,
).fit(disp=False)

# M1: добавляем возраст аккаунта
m1 = smf.logit(
    "returned_30d ~ answered_24h + "
    "C(account_age_group, "
    "Treatment(reference='under_one_day'))",
    data=df,
).fit(disp=False)

# Проверяем одинаковое количество наблюдений
if int(m0.nobs) != len(df) or int(m1.nobs) != len(df):
    raise ValueError(
        "M0 и M1 обучены не на всей проверенной выборке"
    )

def print_main_result(name, result):
    coef = result.params["answered_24h"]
    ci = result.conf_int().loc["answered_24h"]

    print(f"\n=== {name} ===")
    print(f"Коэффициент: {coef:.4f}")
    print(f"Odds Ratio: {np.exp(coef):.4f}")
    print(
        "95% CI: "
        f"[{np.exp(ci.iloc[0]):.4f}; "
        f"{np.exp(ci.iloc[1]):.4f}]"
    )
    print(
        f"p-value: "
        f"{result.pvalues['answered_24h']:.6f}"
    )
    print(
        f"Pseudo R²: "
        f"{result.prsquared:.5f}"
    )
    print(
        f"Сходимость: "
        f"{result.mle_retvals['converged']}"
    )


print_main_result("M0: без корректировки", m0)
print_main_result("M1: с учётом возраста", m1)

print("\n=== Полные результаты M1 ===")
print(m1.summary())