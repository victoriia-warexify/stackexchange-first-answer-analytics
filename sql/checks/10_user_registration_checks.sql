SELECT
    COUNT(*) AS total_users,

    COUNT(DISTINCT user_id) AS unique_users,

    COUNT(*) FILTER (
        WHERE account_created_at IS NULL
    ) AS missing_registration_dates,

    COUNT(*) FILTER (
        WHERE account_created_at > first_question_at
    ) AS invalid_account_dates,

    COUNT(*) FILTER (
        WHERE account_created_at = first_question_at
    ) AS same_timestamp,

    ROUND(
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY EXTRACT(
                EPOCH FROM (
                    first_question_at - account_created_at
                )
            ) / 86400.0
        )::NUMERIC,
        2
    ) AS median_account_age_days

FROM raw.user_registration_2023;