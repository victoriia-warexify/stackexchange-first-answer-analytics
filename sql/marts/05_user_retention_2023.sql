CREATE OR REPLACE VIEW analytics.user_retention_2023 AS

SELECT
    f.user_id,
    f.first_question_id,
    f.first_question_at,

    -- Первый ответ
    a.first_answer_at,
    a.first_answer_hours,
    a.answered_24h,

    -- Повторные публикации
    p.post_events_30d,
    p.questions_30d,
    p.answers_30d,
    p.returned_with_post_30d,

    -- Повторные комментарии
    c.comment_events_30d,
    c.returned_with_comment_30d,

    -- Общая возвращаемость
    (
        p.returned_with_post_30d
        OR c.returned_with_comment_30d
    ) AS returned_30d

FROM raw.first_questions_2023 f

LEFT JOIN analytics.first_answer_2023 a
    ON f.user_id = a.user_id

LEFT JOIN analytics.posts_return_2023 p
    ON f.user_id = p.user_id

LEFT JOIN analytics.comments_return_2023 c
    ON f.user_id = c.user_id;