import numpy as np
import pandas as pd
import psycopg
import statsmodels.api as sm


# 1. Загружаем данные из PostgreSQL
query = """
SELECT
    answered_24h::INT AS answered_24h,
    returned_30d::INT AS returned_30d
FROM analytics.user_model_features_2023
"""

with psycopg.connect("dbname=stackexchange_analytics") as conn:
    rows = conn.execute(query).fetchall()

df = pd.DataFrame(
    rows,
    columns=["answered_24h", "returned_30d"]
)

# 2. Проверяем данные
assert len(df) == 5240
assert df["answered_24h"].notna().all()
assert df["returned_30d"].notna().all()

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