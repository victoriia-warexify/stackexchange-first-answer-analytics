CREATE OR REPLACE VIEW
analytics.return_outside_first_thread_2023 AS

WITH post_activity AS (
    SELECT
        f.user_id,
        COUNT(p.post_id) AS other_posts_30d

    FROM raw.first_questions_2023 f

    LEFT JOIN raw.posts_activity_2023 p
        ON p.user_id = f.user_id
       AND p.event_at >
           f.first_question_at + INTERVAL '24 hours'
       AND p.event_at <=
           f.first_question_at + INTERVAL '30 days'

       AND (
           -- Новый вопрос
           p.post_type_id = 1

           OR (
               -- Ответ не на свой первый вопрос
               p.post_type_id = 2
               AND NOT EXISTS (
                   SELECT 1
                   FROM raw.answers_to_2023_questions a
                   WHERE a.answer_id = p.post_id
                     AND a.question_id = f.first_question_id
               )
           )
       )

    GROUP BY f.user_id
),

comment_activity AS (
    SELECT
        f.user_id,
        COUNT(c.comment_id) AS other_comments_30d

    FROM raw.first_questions_2023 f

    LEFT JOIN raw.comments_activity c
        ON c.user_id = f.user_id
       AND c.event_at >
           f.first_question_at + INTERVAL '24 hours'
       AND c.event_at <=
           f.first_question_at + INTERVAL '30 days'

       -- Исключаем комментарии к первому вопросу
       AND c.post_id <> f.first_question_id

       -- Исключаем комментарии к ответам
       -- на первый вопрос
       AND NOT EXISTS (
           SELECT 1
           FROM raw.answers_to_2023_questions a
           WHERE a.answer_id = c.post_id
             AND a.question_id = f.first_question_id
       )

    GROUP BY f.user_id
)

SELECT
    f.user_id,

    p.other_posts_30d,
    c.other_comments_30d,

    (
        p.other_posts_30d > 0
        OR c.other_comments_30d > 0
    ) AS returned_outside_first_thread_30d

FROM raw.first_questions_2023 f

JOIN post_activity p
    ON f.user_id = p.user_id

JOIN comment_activity c
    ON f.user_id = c.user_id;