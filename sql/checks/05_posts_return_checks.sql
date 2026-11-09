SELECT
    COUNT(*) AS total_users,

    COUNT(*) FILTER (
        WHERE returned_with_post_30d
    ) AS returned_users,

    COUNT(*) FILTER (
        WHERE NOT returned_with_post_30d
    ) AS not_returned_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE returned_with_post_30d
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS post_return_rate_30d

FROM analytics.posts_return_2023;