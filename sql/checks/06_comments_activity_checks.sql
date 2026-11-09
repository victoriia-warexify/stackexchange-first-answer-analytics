SELECT
    COUNT(*) AS total_comments,

    COUNT(DISTINCT comment_id) AS unique_comments,

    COUNT(*) - COUNT(DISTINCT comment_id) AS duplicate_ids,

    COUNT(DISTINCT user_id) AS unique_users,

    COUNT(*) FILTER (
        WHERE comment_id IS NULL
           OR user_id IS NULL
           OR post_id IS NULL
           OR event_at IS NULL
    ) AS rows_with_nulls,

    MIN(event_at) AS min_date,
    MAX(event_at) AS max_date

FROM raw.comments_activity;