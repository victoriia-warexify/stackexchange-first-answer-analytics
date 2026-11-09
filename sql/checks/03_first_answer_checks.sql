SELECT
    COUNT(*) AS total_users,

    COUNT(*) FILTER (
        WHERE answered_24h = TRUE
    ) AS answered_24h,

    COUNT(*) FILTER (
        WHERE answered_24h = FALSE
    ) AS not_answered_24h,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE answered_24h = TRUE
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS answer_rate_24h

FROM analytics.first_answer_2023;
