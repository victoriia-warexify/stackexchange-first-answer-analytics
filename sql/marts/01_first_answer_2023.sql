CREATE OR REPLACE VIEW analytics.first_answer_2023 AS

SELECT
    f.user_id,
    f.first_question_id,
    f.first_question_at,

    MIN(a.answer_at) AS first_answer_at,

    ROUND(
        (
            EXTRACT(
                EPOCH FROM (
                    MIN(a.answer_at) - f.first_question_at
                )
            ) / 3600
        )::NUMERIC,
        2
    ) AS first_answer_hours,

    COALESCE(
        MIN(a.answer_at) <=
            f.first_question_at + INTERVAL '24 hours',
        FALSE
    ) AS answered_24h

FROM raw.first_questions_2023 f

LEFT JOIN raw.answers_to_2023_questions a
    ON a.question_id = f.first_question_id
    AND a.answer_author_id IS NOT NULL
    AND a.answer_author_id <> f.user_id
    AND a.answer_at >= f.first_question_at

GROUP BY
    f.user_id,
    f.first_question_id,
    f.first_question_at;
