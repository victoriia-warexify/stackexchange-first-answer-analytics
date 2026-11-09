SELECT
    CASE
        WHEN answered_24h
            THEN 'Ответ за 24 часа'
        ELSE 'Нет ответа за 24 часа'
    END AS answer_group,

    COUNT(*) AS users_count,

    COUNT(*) FILTER (
        WHERE returned_30d
    ) AS returned_users,

    COUNT(*) FILTER (
        WHERE NOT returned_30d
    ) AS not_returned_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE returned_30d
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS return_rate_30d

FROM analytics.user_retention_2023

GROUP BY answered_24h
ORDER BY answered_24h DESC;