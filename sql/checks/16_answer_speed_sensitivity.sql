WITH thresholds AS (
    SELECT *
    FROM (VALUES (6), (12), (24)) AS t(hours)
),

classified AS (
    SELECT
        t.hours AS threshold_hours,
        a.user_id,

        COALESCE(
            a.first_answer_at >= a.first_question_at
            AND a.first_answer_at <=
                a.first_question_at
                + t.hours * INTERVAL '1 hour',
            FALSE
        ) AS answered_within_threshold,

        r.returned_outside_first_thread_30d
            AS returned_30d

    FROM analytics.first_answer_2023 a

    CROSS JOIN thresholds t

    JOIN analytics.return_outside_first_thread_2023 r
        ON a.user_id = r.user_id
)

SELECT
    threshold_hours,
    answered_within_threshold,

    COUNT(*) AS users_count,

    COUNT(*) FILTER (
        WHERE returned_30d
    ) AS returned_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE returned_30d
        ) / COUNT(*),
        2
    ) AS return_rate_pct

FROM classified

GROUP BY
    threshold_hours,
    answered_within_threshold

ORDER BY
    threshold_hours,
    answered_within_threshold DESC;