SELECT
    COUNT(*) AS total_users,

    COUNT(DISTINCT user_id) AS unique_users,

    COUNT(*) FILTER (
        WHERE answered_24h
    ) AS answered_24h,

    COUNT(*) FILTER (
        WHERE returned_30d
    ) AS returned_users,

    COUNT(*) FILTER (
        WHERE invalid_account_age
    ) AS invalid_account_ages,

    COUNT(*) FILTER (
        WHERE account_age_days IS NULL
    ) AS missing_account_ages,

    COUNT(*) FILTER (
        WHERE title_length IS NULL
    ) AS missing_titles,

    COUNT(*) FILTER (
        WHERE tags_count IS NULL
    ) AS missing_tags,

    MIN(title_length) AS min_title_length,
    MAX(title_length) AS max_title_length

FROM analytics.user_features_2023;