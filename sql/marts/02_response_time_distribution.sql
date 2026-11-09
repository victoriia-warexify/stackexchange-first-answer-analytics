WITH response_buckets AS (
    SELECT
        CASE
            WHEN first_answer_at IS NULL
                THEN '06. Нет ответа за 30 дней'

            WHEN first_answer_at <=
                 first_question_at + INTERVAL '1 hour'
                THEN '01. В пределах 1 часа'

            WHEN first_answer_at <=
                 first_question_at + INTERVAL '6 hours'
                THEN '02. От 1 до 6 часов'

            WHEN first_answer_at <=
                 first_question_at + INTERVAL '24 hours'
                THEN '03. От 6 до 24 часов'

            WHEN first_answer_at <=
                 first_question_at + INTERVAL '7 days'
                THEN '04. От 1 до 7 дней'

            ELSE '05. От 7 до 30 дней'
        END AS response_bucket

    FROM analytics.first_answer_2023
)

SELECT
    response_bucket,
    COUNT(*) AS users_count,

    ROUND(
        100.0 * COUNT(*)
        / SUM(COUNT(*)) OVER (),
        2
    ) AS share_pct

FROM response_buckets
GROUP BY response_bucket
ORDER BY response_bucket;