WITH user_activity AS (
    SELECT
        u.user_id,
        u.answered_24h,

        -- Новые вопросы
        COUNT(p.post_id) FILTER (
            WHERE p.post_type_id = 1
        ) AS new_questions,

        -- Ответы вне первого обсуждения
        COUNT(p.post_id) FILTER (
            WHERE p.post_type_id = 2
              AND NOT EXISTS (
                  SELECT 1
                  FROM raw.answers_to_2023_questions a
                  WHERE a.answer_id = p.post_id
                    AND a.question_id = u.first_question_id
              )
        ) AS other_answers

    FROM analytics.user_retention_2023 u

    LEFT JOIN raw.posts_activity_2023 p
        ON p.user_id = u.user_id
       AND p.event_at >
           u.first_question_at + INTERVAL '24 hours'
       AND p.event_at <=
           u.first_question_at + INTERVAL '30 days'

    GROUP BY
        u.user_id,
        u.answered_24h
)

SELECT
    CASE
        WHEN answered_24h
            THEN 'Ответ за 24 часа'
        ELSE 'Нет ответа за 24 часа'
    END AS answer_group,

    COUNT(*) AS users_count,

    COUNT(*) FILTER (
        WHERE new_questions > 0
    ) AS new_question_authors,

    COUNT(*) FILTER (
        WHERE other_answers > 0
    ) AS other_answer_authors,

    COUNT(*) FILTER (
        WHERE new_questions > 0
          AND other_answers > 0
    ) AS both_post_types,

    COUNT(*) FILTER (
        WHERE new_questions > 0
           OR other_answers > 0
    ) AS total_post_returns

FROM user_activity
GROUP BY answered_24h
ORDER BY answered_24h DESC;