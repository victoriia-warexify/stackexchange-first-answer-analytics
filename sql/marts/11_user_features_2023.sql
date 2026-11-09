CREATE OR REPLACE VIEW analytics.user_features_2023 AS

SELECT
    f.user_id,
    f.first_question_id,
    f.first_question_at,

    -- Основной исследуемый фактор
    a.answered_24h,

    -- Целевая переменная
    r.returned_outside_first_thread_30d AS returned_30d,

    -- Возраст аккаунта
    CASE
        WHEN u.account_created_at > f.first_question_at
            THEN NULL
        ELSE ROUND(
            (
                EXTRACT(EPOCH FROM (
                    f.first_question_at - u.account_created_at
                )) / 86400.0
            )::NUMERIC,
            2
        )
    END AS account_age_days,

    -- Признак некорректной даты регистрации
    (
        u.account_created_at > f.first_question_at
    ) AS invalid_account_age,

    -- Характеристики первого вопроса
    CHAR_LENGTH(m.initial_title) AS title_length,

    CASE
        WHEN m.initial_tags ~ '^(<[^<>]+>)+$'
            THEN REGEXP_COUNT(
                m.initial_tags, '<[^<>]+>'
            )
        ELSE NULL
    END AS tags_count,

    -- Временные характеристики
    EXTRACT(MONTH FROM f.first_question_at)::INT
        AS question_month,

    EXTRACT(ISODOW FROM f.first_question_at)::INT
        AS question_weekday,

    EXTRACT(HOUR FROM f.first_question_at)::INT
        AS question_hour

FROM raw.first_questions_2023 f

LEFT JOIN raw.user_registration_2023 u
    ON f.user_id = u.user_id

LEFT JOIN raw.initial_question_metadata_2023 m
    ON f.first_question_id = m.question_id

LEFT JOIN analytics.first_answer_2023 a
    ON f.user_id = a.user_id

LEFT JOIN analytics.return_outside_first_thread_2023 r
    ON f.user_id = r.user_id;