SELECT
    COUNT(*) AS total_users,

    COUNT(*) FILTER (
        WHERE returned_with_comment_30d
    ) AS returned_users,

    COUNT(*) FILTER (
        WHERE NOT returned_with_comment_30d
    ) AS not_returned_users,

    SUM(comment_events_30d) AS total_comment_events,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE returned_with_comment_30d
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS comment_return_rate_30d

FROM analytics.comments_return_2023;