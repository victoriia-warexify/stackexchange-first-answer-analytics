WITH account_data AS (
    SELECT
        u.user_id,
        u.first_question_at,
        u.account_created_at,

        EXTRACT(
            EPOCH FROM (
                u.first_question_at - u.account_created_at
            )
        ) / 86400.0 AS account_age_days,

        r.returned_outside_first_thread_30d

    FROM raw.user_registration_2023 u

    JOIN analytics.return_outside_first_thread_2023 r
        ON u.user_id = r.user_id
),

age_groups AS (
    SELECT
        *,
        CASE
            WHEN account_age_days < 0
                THEN '01. Отрицательный возраст'
            WHEN account_age_days = 0
                THEN '02. Совпадение дат'
            WHEN account_age_days < 1
                THEN '03. Менее суток'
            WHEN account_age_days < 30
                THEN '04. От 1 до 30 дней'
            ELSE '05. Более 30 дней'
        END AS age_group

    FROM account_data
)

SELECT
    age_group,

    COUNT(*) AS users_count,

    ROUND(
        100.0 * COUNT(*)
        / SUM(COUNT(*)) OVER (),
        2
    ) AS users_pct,

    COUNT(*) FILTER (
        WHERE returned_outside_first_thread_30d
    ) AS returned_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE returned_outside_first_thread_30d
        ) / COUNT(*),
        2
    ) AS return_rate_30d

FROM age_groups
GROUP BY age_group
ORDER BY age_group;