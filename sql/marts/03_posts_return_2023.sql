CREATE OR REPLACE VIEW analytics.posts_return_2023 AS

SELECT
    f.user_id,
    f.first_question_id,
    f.first_question_at,

    COUNT(p.post_id) AS post_events_30d,

    COUNT(p.post_id) FILTER (
        WHERE p.post_type_id = 1
    ) AS questions_30d,

    COUNT(p.post_id) FILTER (
        WHERE p.post_type_id = 2
    ) AS answers_30d,

    COUNT(p.post_id) > 0 AS returned_with_post_30d

FROM raw.first_questions_2023 f

LEFT JOIN raw.posts_activity_2023 p
    ON p.user_id = f.user_id
   AND p.event_at >
       f.first_question_at + INTERVAL '24 hours'
   AND p.event_at <=
       f.first_question_at + INTERVAL '30 days'

GROUP BY
    f.user_id,
    f.first_question_id,
    f.first_question_at;