SELECT
    COUNT(*) AS total_posts,
    COUNT(DISTINCT post_id) AS unique_posts,
    COUNT(DISTINCT user_id) AS unique_users,

    COUNT(*) FILTER (
        WHERE post_type_id = 1
    ) AS questions_count,

    COUNT(*) FILTER (
        WHERE post_type_id = 2
    ) AS answers_count,

    COUNT(*) FILTER (
        WHERE post_id IS NULL
           OR user_id IS NULL
           OR post_type_id IS NULL
           OR event_at IS NULL
    ) AS rows_with_nulls,

    MIN(event_at) AS min_date,
    MAX(event_at) AS max_date

FROM raw.posts_activity_2023;