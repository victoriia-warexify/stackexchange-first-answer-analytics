WITH user_data AS (
    SELECT
        u.user_id,
        r.answered_24h,
        a.returned_outside_first_thread_30d,

        CASE
            WHEN u.account_created_at >
                 u.first_question_at
                THEN '01. Отрицательный возраст'

            WHEN u.account_created_at =
                 u.first_question_at
                THEN '02. Совпадение дат'

            WHEN u.first_question_at -
                 u.account_created_at < INTERVAL '1 day'
                THEN '03. Менее суток'

            WHEN u.first_question_at -
                 u.account_created_at < INTERVAL '30 days'
                THEN '04. От 1 до 30 дней'

            ELSE '05. Более 30 дней'
        END AS age_group

    FROM raw.user_registration_2023 u

    JOIN analytics.user_retention_2023 r
        ON u.user_id = r.user_id

    JOIN analytics.return_outside_first_thread_2023 a
        ON u.user_id = a.user_id
)

SELECT
    age_group,
    answered_24h,

    COUNT(*) AS users_count,

    COUNT(*) FILTER (
        WHERE returned_outside_first_thread_30d
    ) AS returned_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE returned_outside_first_thread_30d
        ) / COUNT(*),
        2
    ) AS return_rate_30d

FROM user_data

GROUP BY age_group, answered_24h

ORDER BY age_group, answered_24h DESC;