SELECT
    CASE
        WHEN u.answered_24h
            THEN 'Ответ за 24 часа'
        ELSE 'Нет ответа за 24 часа'
    END AS answer_group,

    COUNT(*) AS users_count,

    -- Исходная возвращаемость
    COUNT(*) FILTER (
        WHERE u.returned_30d
    ) AS original_returns,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE u.returned_30d
        ) / COUNT(*),
        2
    ) AS original_return_rate,

    -- Возвращаемость вне первого обсуждения
    COUNT(*) FILTER (
        WHERE r.returned_outside_first_thread_30d
    ) AS new_returns,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE r.returned_outside_first_thread_30d
        ) / COUNT(*),
        2
    ) AS new_return_rate,

    -- Пользователи, исключённые из новой метрики
    COUNT(*) FILTER (
        WHERE u.returned_30d
          AND NOT r.returned_outside_first_thread_30d
    ) AS excluded_users

FROM analytics.user_retention_2023 u

JOIN analytics.return_outside_first_thread_2023 r
    ON u.user_id = r.user_id

GROUP BY u.answered_24h
ORDER BY u.answered_24h DESC;