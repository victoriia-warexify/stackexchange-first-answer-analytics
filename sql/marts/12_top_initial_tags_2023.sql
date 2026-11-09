WITH question_tags AS (
    SELECT
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
)

SELECT
    tag_name,

    COUNT(DISTINCT user_id) AS users_count,

    ROUND(
        100.0 * COUNT(DISTINCT user_id)
        / (
            SELECT COUNT(*)
            FROM raw.first_questions_2023
        ),
        2
    ) AS share_of_users_pct

FROM question_tags

GROUP BY tag_name

ORDER BY users_count DESC, tag_name

LIMIT 20;