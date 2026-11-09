import psycopg
from pathlib import Path
import pandas as pd
from statsmodels.stats.proportion import (
    proportions_ztest,
    confint_proportions_2indep,
)


QUERY = """
SELECT
    u.answered_24h,
    COUNT(*) AS total_users,
    COUNT(*) FILTER (
        WHERE u.returned_30d
    ) AS original_returns,
    COUNT(*) FILTER (
        WHERE r.returned_outside_first_thread_30d
    ) AS outside_returns
FROM analytics.user_retention_2023 u
JOIN analytics.return_outside_first_thread_2023 r
    ON u.user_id = r.user_id
GROUP BY u.answered_24h;
"""


def compare_proportions(x1, n1, x0, n0):
    """Сравнение двух независимых долей."""

    p1 = x1 / n1
    p0 = x0 / n0

    z_stat, p_value = proportions_ztest(
        count=[x1, x0],
        nobs=[n1, n0],
        alternative="two-sided",
    )

    ci_low, ci_high = confint_proportions_2indep(
        count1=x1,
        nobs1=n1,
        count2=x0,
        nobs2=n0,
        compare="diff",
        method="newcomb",
        alpha=0.05,
    )

    print(f"Ответ за 24 часа: {p1:.2%} ({x1}/{n1})")
    print(f"Без ответа за 24 часа: {p0:.2%} ({x0}/{n0})")
    print(f"Разница: {(p1 - p0) * 100:+.2f} п. п.")
    print(f"z-статистика: {z_stat:.4f}")
    print(f"p-value: {p_value:.6f}")
    print(
        f"95% ДИ: [{ci_low * 100:+.2f}; "
        f"{ci_high * 100:+.2f}] п. п."
    )


def main():
    with psycopg.connect("dbname=stackexchange_analytics") as conn:
        with conn.cursor() as cursor:
            cursor.execute(QUERY)
            rows = cursor.fetchall()

    groups = {
        answered: (total, original, outside)
        for answered, total, original, outside in rows
    }

    if set(groups) != {True, False}:
        raise ValueError("Ожидались две группы пользователей")

    n1, original1, outside1 = groups[True]
    n0, original0, outside0 = groups[False]

    # Экспорт фактической возвращаемости
    results_dir = (
        Path(__file__).resolve().parents[1]
        / "reports"
        / "data"
    )
    results_dir.mkdir(parents=True, exist_ok=True)

    retention = pd.DataFrame([
        {
            "answered_24h": 0,
            "users": n0,
            "returned": outside0,
        },
        {
            "answered_24h": 1,
            "users": n1,
            "returned": outside1,
        },
    ])

    retention.to_csv(
        results_dir / "retention_results.csv",
        index=False,
    )

    print("=== Исходная метрика ===")
    compare_proportions(original1, n1, original0, n0)

    print("\n=== Вне первого обсуждения ===")
    compare_proportions(outside1, n1, outside0, n0)


if __name__ == "__main__":
    main()