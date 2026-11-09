WITH question_tags AS (
    SELECT DISTINCT
        f.user_id,
        t.tag_name

    FROM raw.first_questions_2023 f

    JOIN raw.initial_question_metadata_2023 m
        ON f.first_question_id = m.question_id

    CROSS JOIN LATERAL regexp_split_to_table(
        TRIM(BOTH '<>' FROM m.initial_tags),
        '><'
    ) AS t(tag_name)

    WHERE m.initial_tags ~ '^(<[^<>]+>)+$'
),

top_tags AS (
    SELECT
        tag_name,
        COUNT(*) AS users_count

    FROM question_tags

    GROUP BY tag_name
    ORDER BY users_count DESC, tag_name
    LIMIT 10
)

SELECT
    t.tag_name,

    COUNT(*) AS users_count,

    COUNT(*) FILTER (
        WHERE u.answered_24h
    ) AS answered_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE u.answered_24h
        ) / COUNT(*),
        2
    ) AS answer_rate_24h,

    COUNT(*) FILTER (
        WHERE u.returned_30d
    ) AS returned_users,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE u.returned_30d
        ) / COUNT(*),
        2
    ) AS return_rate_30d

FROM top_tags t

JOIN question_tags qt
    ON t.tag_name = qt.tag_name

JOIN analytics.user_features_2023 u
    ON qt.user_id = u.user_id

GROUP BY t.tag_name
ORDER BY users_count DESC, t.tag_name;