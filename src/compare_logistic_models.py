import numpy as np
import pandas as pd
import psycopg
from pathlib import Path
import statsmodels.formula.api as smf
from scipy.stats import chi2
from scipy.special import expit
from statsmodels.stats.outliers_influence import variance_inflation_factor


query = """
SELECT
    v.*,

    CASE
        WHEN r.account_created_at = v.first_question_at
            THEN 'same_timestamp'
        WHEN v.first_question_at - r.account_created_at
             < INTERVAL '1 day'
            THEN 'under_one_day'
        WHEN v.first_question_at - r.account_created_at
             < INTERVAL '30 days'
            THEN 'one_to_thirty_days'
        ELSE 'thirty_plus_days'
    END AS account_age_group

FROM analytics.user_model_features_2023 v

JOIN raw.user_registration_2023 r
    ON v.user_id = r.user_id

WHERE r.account_created_at <= v.first_question_at

ORDER BY v.user_id
"""

with psycopg.connect("dbname=stackexchange_analytics") as conn:
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [col.name for col in cur.description]
        df = pd.DataFrame(cur.fetchall(), columns=columns)


# Подготовка признаков
df["answered_24h"] = df["answered_24h"].astype(int)
df["returned_30d"] = df["returned_30d"].astype(int)

df["title_length_10"] = df["title_length"] / 10.0

hour_angle = 2 * np.pi * df["question_hour"] / 24
df["hour_sin"] = np.sin(hour_angle)
df["hour_cos"] = np.cos(hour_angle)

tag_columns = [
    "has_regression",
    "has_r",
    "has_machine_learning",
    "has_hypothesis_testing",
    "has_time_series",
    "has_probability",
    "has_mathematical_statistics",
    "has_mixed_model",
    "has_statistical_significance",
]

df[tag_columns] = df[tag_columns].astype(int)

model_columns = [
    "answered_24h",
    "returned_30d",
    "account_age_group",
    "title_length_10",
    "tags_count",
    "question_month",
    "question_weekday",
    "hour_sin",
    "hour_cos",
] + tag_columns

assert len(df) == 5140
assert df["user_id"].is_unique
assert df["returned_30d"].sum() == 539
assert df[model_columns].notna().all().all()


# Формулы моделей
age_term = (
    "C(account_age_group, "
    "Treatment(reference='under_one_day'))"
)

formula_m0 = "returned_30d ~ answered_24h"

formula_m1 = formula_m0 + " + " + age_term

formula_m2 = (
    formula_m1
    + " + title_length_10"
    + " + tags_count"
    + " + C(question_month)"
    + " + C(question_weekday)"
    + " + hour_sin + hour_cos"
    + " + " + " + ".join(tag_columns)
)


# Обучение
models = {}

for name, formula in [
    ("M0", formula_m0),
    ("M1", formula_m1),
    ("M2", formula_m2),
]:
    models[name] = smf.logit(
        formula,
        data=df,
    ).fit(disp=False, maxiter=200)

# Экспорт результатов для визуализации
results_dir = (
    Path(__file__).resolve().parents[1]
    / "reports"
    / "data"
)
results_dir.mkdir(parents=True, exist_ok=True)

model_rows = []

for name, result in models.items():
    ci = result.conf_int().loc["answered_24h"]

    model_rows.append({
        "model": name,
        "n": int(result.nobs),
        "or": float(np.exp(result.params["answered_24h"])),
        "ci_lower": float(np.exp(ci.iloc[0])),
        "ci_upper": float(np.exp(ci.iloc[1])),
        "p_value": float(result.pvalues["answered_24h"]),
    })

pd.DataFrame(model_rows).to_csv(
    results_dir / "model_results.csv",
    index=False,
)

# Сравнение основного коэффициента
print(f"Пользователей: {len(df)}")
print(f"Вернувшихся: {df['returned_30d'].sum()}")

print("\n=== Сравнение моделей ===")

for name, result in models.items():
    coef = result.params["answered_24h"]
    ci = result.conf_int().loc["answered_24h"]

    print(f"\n{name}")
    print(f"OR: {np.exp(coef):.4f}")
    print(
        f"95% CI: [{np.exp(ci.iloc[0]):.4f}; "
        f"{np.exp(ci.iloc[1]):.4f}]"
    )
    print(f"p-value: {result.pvalues['answered_24h']:.6f}")
    print(f"Pseudo R²: {result.prsquared:.5f}")
    print(f"AIC: {result.aic:.2f}")
    print(f"Количество коэффициентов: {len(result.params)}")
    print(f"Сходимость: {result.mle_retvals['converged']}")


# Коэффициенты расширенной модели
m2 = models["M2"]

ci = m2.conf_int()

results_table = pd.DataFrame({
    "OR": np.exp(m2.params),
    "CI_lower": np.exp(ci.iloc[:, 0]),
    "CI_upper": np.exp(ci.iloc[:, 1]),
    "p_value": m2.pvalues,
})

print("\n=== Основные коэффициенты M2 ===")

selected = [
    "answered_24h",
    "title_length_10",
    "tags_count",
] + tag_columns

print(results_table.loc[selected].round(4))


print("\n=== Диагностика M2 ===")

X = m2.model.exog
matrix_rank = np.linalg.matrix_rank(X)
n_parameters = X.shape[1]

print(f"Ранг матрицы: {matrix_rank}")
print(f"Число коэффициентов: {n_parameters}")
print(f"Полный ранг: {matrix_rank == n_parameters}")
print(f"Сходимость: {m2.mle_retvals['converged']}")


# Сравниваем вложенные модели M1 и M2
m1 = models["M1"]

lr_stat = 2 * (m2.llf - m1.llf)
df_diff = int(m2.df_model - m1.df_model)
lr_p_value = chi2.sf(lr_stat, df_diff)

print("\n=== Likelihood Ratio Test: M1 vs M2 ===")
print(f"LR statistic: {lr_stat:.4f}")
print(f"Degrees of freedom: {df_diff}")
print(f"p-value: {lr_p_value:.6f}")


# Проверка мультиколлинеарности M2

print("\n=== Multicollinearity: VIF ===")

X = m2.model.exog
feature_names = m2.model.exog_names

vif_results = pd.DataFrame({
    "feature": feature_names,
    "VIF": [
        variance_inflation_factor(X, i)
        for i in range(X.shape[1])
    ],
})

# Константу не анализируем
vif_results = vif_results[
    vif_results["feature"] != "Intercept"
]

vif_results = vif_results.sort_values(
    "VIF",
    ascending=False,
)

print("\nТоп-15 признаков по VIF:")
print(vif_results.head(15).to_string(index=False))

print("\nVIF основного признака:")
print(
    vif_results.loc[
        vif_results["feature"] == "answered_24h"
    ].to_string(index=False)
)

print("\nКоличество признаков с VIF > 5:")
print((vif_results["VIF"] > 5).sum())

print("\nКоличество признаков с VIF > 10:")
print((vif_results["VIF"] > 10).sum())


def adjusted_probability_difference(result):
    # Матрица признаков и коэффициенты модели
    X = result.model.exog.copy()
    beta = result.params.to_numpy()

    # Находим столбец с основным признаком
    feature_index = result.model.exog_names.index(
        "answered_24h"
    )

    # Два сценария для одних и тех же пользователей
    X0 = X.copy()
    X1 = X.copy()

    X0[:, feature_index] = 0
    X1[:, feature_index] = 1

    # Предсказанные вероятности
    p0 = expit(X0 @ beta)
    p1 = expit(X1 @ beta)

    avg_p0 = p0.mean()
    avg_p1 = p1.mean()

    difference = avg_p1 - avg_p0

    # Стандартная ошибка методом дельта
    gradient = (
        (
            (p1 * (1 - p1))[:, None] * X1
            - (p0 * (1 - p0))[:, None] * X0
        )
    ).mean(axis=0)

    covariance = result.cov_params().to_numpy()

    variance = gradient @ covariance @ gradient
    se = np.sqrt(max(float(variance), 0.0))

    ci_lower = difference - 1.96 * se
    ci_upper = difference + 1.96 * se

    return avg_p0, avg_p1, difference, ci_lower, ci_upper


print("\n=== Скорректированные вероятности ===")

for name in ["M1", "M2"]:
    result = models[name]

    p0, p1, diff, ci_low, ci_high = (
        adjusted_probability_difference(result)
    )

    print(f"\n{name}")
    print(f"Без быстрого ответа: {100 * p0:.2f}%")
    print(f"С быстрым ответом: {100 * p1:.2f}%")
    print(f"Разница: {100 * diff:+.2f} п.п.")
    print(
        f"95% CI: "
        f"[{100 * ci_low:+.2f}; "
        f"{100 * ci_high:+.2f}] п.п."
    )


# Анализ чувствительности:
# включаем пользователей с аномальной датой регистрации

query_all = """
SELECT
    v.*,

    CASE
        WHEN r.account_created_at > v.first_question_at
            THEN 'invalid'

        WHEN r.account_created_at = v.first_question_at
            THEN 'same_timestamp'

        WHEN v.first_question_at - r.account_created_at
             < INTERVAL '1 day'
            THEN 'under_one_day'

        WHEN v.first_question_at - r.account_created_at
             < INTERVAL '30 days'
            THEN 'one_to_thirty_days'

        ELSE 'thirty_plus_days'
    END AS account_age_group

FROM analytics.user_model_features_2023 v

JOIN raw.user_registration_2023 r
    ON v.user_id = r.user_id

ORDER BY v.user_id
"""

with psycopg.connect("dbname=stackexchange_analytics") as conn:
    with conn.cursor() as cur:
        cur.execute(query_all)
        columns = [col.name for col in cur.description]
        df_all = pd.DataFrame(cur.fetchall(), columns=columns)


# Подготавливаем те же признаки, что в M2
df_all["answered_24h"] = df_all["answered_24h"].astype(int)
df_all["returned_30d"] = df_all["returned_30d"].astype(int)

df_all["title_length_10"] = df_all["title_length"] / 10.0

hour_angle = 2 * np.pi * df_all["question_hour"] / 24
df_all["hour_sin"] = np.sin(hour_angle)
df_all["hour_cos"] = np.cos(hour_angle)

df_all[tag_columns] = df_all[tag_columns].astype(int)


# Проверяем полную выборку
assert len(df_all) == 5240
assert df_all["user_id"].is_unique
assert df_all["returned_30d"].sum() == 550
assert df_all["answered_24h"].sum() == 2119

assert (
    (df_all["account_age_group"] == "invalid").sum()
    == 100
)

assert df_all[model_columns].notna().all().all()


print("\n=== Анализ чувствительности ===")

for name, formula in [
    ("M1: вся выборка", formula_m1),
    ("M2: вся выборка", formula_m2),
]:
    result = smf.logit(
        formula,
        data=df_all,
    ).fit(disp=False, maxiter=200)

    coef = result.params["answered_24h"]
    ci = result.conf_int().loc["answered_24h"]

    print(f"\n{name}")
    print(f"Пользователей: {int(result.nobs)}")
    print(f"OR: {np.exp(coef):.4f}")
    print(
        f"95% CI: [{np.exp(ci.iloc[0]):.4f}; "
        f"{np.exp(ci.iloc[1]):.4f}]"
    )
    print(f"p-value: {result.pvalues['answered_24h']:.6f}")
    print(f"Сходимость: {result.mle_retvals['converged']}")


# Анализ чувствительности к порогу быстрого ответа:
# M2 с порогами 6, 12 и 24 часа

print("\n=== M2: альтернативные пороги ответа ===")

with psycopg.connect("dbname=stackexchange_analytics") as conn:
    answer_rows = conn.execute("""
        SELECT user_id, first_answer_at
        FROM analytics.first_answer_2023
    """).fetchall()

answer_times = pd.DataFrame(
    answer_rows,
    columns=["user_id", "first_answer_at"],
)

threshold_df = df.merge(
    answer_times,
    on="user_id",
    how="left",
    validate="one_to_one",
)

assert len(threshold_df) == 5140

hours_to_answer = (
    pd.to_datetime(threshold_df["first_answer_at"])
    - pd.to_datetime(threshold_df["first_question_at"])
).dt.total_seconds() / 3600.0

threshold_rows = []

for threshold in [6, 12, 24]:
    data = threshold_df.copy()

    # Временно используем колонку answered_24h
    # для текущего порога, чтобы переиспользовать формулу M2
    data["answered_24h"] = (
        hours_to_answer.ge(0)
        & hours_to_answer.le(threshold)
    ).astype(int)

    # При 24 часах должны воспроизвести исходные метки
    if threshold == 24:
        assert np.array_equal(
            data["answered_24h"].to_numpy(),
            df["answered_24h"].to_numpy(),
        )

    result = smf.logit(
        formula_m2,
        data=data,
    ).fit(disp=False, maxiter=200)

    coef = result.params["answered_24h"]
    ci = result.conf_int().loc["answered_24h"]

    p0, p1, diff, low, high = (
        adjusted_probability_difference(result)
    )

    threshold_rows.append({
        "threshold_hours": threshold,
        "n": int(result.nobs),
        "or": float(np.exp(coef)),
        "difference_pp": float(100 * diff),
        "ci_lower_pp": float(100 * low),
        "ci_upper_pp": float(100 * high),
    })

    print(f"\nПорог: {threshold} часов")
    print(f"Получили быстрый ответ: {data['answered_24h'].sum()}")
    print(f"OR: {np.exp(coef):.4f}")
    print(
        f"95% CI OR: [{np.exp(ci.iloc[0]):.4f}; "
        f"{np.exp(ci.iloc[1]):.4f}]"
    )
    print(f"p-value: {result.pvalues['answered_24h']:.6f}")
    print(f"Сходимость: {result.mle_retvals['converged']}")
    print(f"Скорректированная разница: {100 * diff:+.2f} п.п.")
    print(
        f"95% CI разницы: "
        f"[{100 * low:+.2f}; {100 * high:+.2f}] п.п."
    )

pd.DataFrame(threshold_rows).to_csv(
    results_dir / "threshold_results.csv",
    index=False,
)