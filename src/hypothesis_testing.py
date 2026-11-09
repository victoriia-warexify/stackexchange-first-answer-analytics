import psycopg
from statsmodels.stats.proportion import (
    proportions_ztest,
    confint_proportions_2indep,
)


QUERY = """
SELECT
    answered_24h,
    COUNT(*) AS total_users,
    COUNT(*) FILTER (WHERE returned_30d) AS returned_users
FROM analytics.user_retention_2023
GROUP BY answered_24h;
"""


def main():
    # Получаем данные из PostgreSQL
    with psycopg.connect("dbname=stackexchange_analytics") as conn:
        with conn.cursor() as cursor:
            cursor.execute(QUERY)
            rows = cursor.fetchall()

    groups = {
        answered: (returned, total)
        for answered, total, returned in rows
    }

    if set(groups) != {True, False}:
        raise ValueError("Ожидались две группы пользователей")

    # Группа с ответом за 24 часа
    x1, n1 = groups[True]

    # Группа без ответа за 24 часа
    x0, n0 = groups[False]

    # Доли вернувшихся пользователей
    p1 = x1 / n1
    p0 = x0 / n0

    difference = p1 - p0

    # Двусторонний z-тест для двух долей
    z_stat, p_value = proportions_ztest(
        count=[x1, x0],
        nobs=[n1, n0],
        alternative="two-sided",
    )

    # 95% доверительный интервал Ньюкомба
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
    print(f"Разница: {difference * 100:+.2f} п. п.")
    print(f"z-статистика: {z_stat:.4f}")
    print(f"p-value: {p_value:.4f}")
    print(
        f"95% ДИ: [{ci_low * 100:+.2f}; "
        f"{ci_high * 100:+.2f}] п. п."
    )

    if p_value < 0.05:
        print("Различие статистически значимо")
    else:
        print("Статистически значимое различие не выявлено")


if __name__ == "__main__":
    main()