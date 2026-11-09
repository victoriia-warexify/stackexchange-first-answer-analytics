CREATE OR REPLACE VIEW analytics.comments_return_2023 AS

SELECT
    f.user_id,
    f.first_question_at,

    COUNT(c.comment_id) AS comment_events_30d,

    COUNT(c.comment_id) > 0
        AS returned_with_comment_30d

FROM raw.first_questions_2023 f

LEFT JOIN raw.comments_activity c
    ON c.user_id = f.user_id
   AND c.event_at >
       f.first_question_at + INTERVAL '24 hours'
   AND c.event_at <=
       f.first_question_at + INTERVAL '30 days'

GROUP BY
    f.user_id,
    f.first_question_at;