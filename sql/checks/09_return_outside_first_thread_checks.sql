SELECT
    COUNT(*) AS total_users,

    COUNT(DISTINCT r.user_id) AS unique_users,

    COUNT(*) FILTER (
        WHERE u.returned_30d
    ) AS original_returns,

    COUNT(*) FILTER (
        WHERE r.returned_outside_first_thread_30d
    ) AS new_returns,

    COUNT(*) FILTER (
        WHERE u.returned_30d
          AND NOT r.returned_outside_first_thread_30d
    ) AS excluded_users,

    COUNT(*) FILTER (
        WHERE r.returned_outside_first_thread_30d
          AND NOT u.returned_30d
    ) AS inconsistent_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE r.returned_outside_first_thread_30d
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS new_return_rate_30d

FROM analytics.return_outside_first_thread_2023 r

JOIN analytics.user_retention_2023 u
    ON r.user_id = u.user_id;