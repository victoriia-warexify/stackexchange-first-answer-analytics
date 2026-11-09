SELECT
    COUNT(*) AS total_rows,

    COUNT(DISTINCT user_id) AS unique_users,

    COUNT(*) FILTER (
        WHERE answered_24h IS NULL
           OR returned_with_post_30d IS NULL
           OR returned_with_comment_30d IS NULL
           OR returned_30d IS NULL
    ) AS rows_with_missing_flags

FROM analytics.user_retention_2023;


SELECT
    COUNT(*) FILTER (
        WHERE answered_24h
    ) AS answered_24h,

    COUNT(*) FILTER (
        WHERE returned_with_post_30d
    ) AS post_returns,

    COUNT(*) FILTER (
        WHERE returned_with_comment_30d
    ) AS comment_returns,

    COUNT(*) FILTER (
        WHERE returned_with_post_30d
          AND returned_with_comment_30d
    ) AS both_types,

    COUNT(*) FILTER (
        WHERE returned_30d
    ) AS returned_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE returned_30d
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS return_rate_30d

FROM analytics.user_retention_2023;