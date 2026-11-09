SELECT
    COUNT(*) AS total_questions,

    COUNT(DISTINCT question_id) AS unique_questions,

    COUNT(*) FILTER (
        WHERE initial_title IS NULL
           OR TRIM(initial_title) = ''
    ) AS missing_titles,

    COUNT(*) FILTER (
        WHERE initial_tags IS NULL
           OR initial_tags !~ '^(<[^<>]+>)+$'
    ) AS invalid_tags,

    COUNT(*) FILTER (
        WHERE title_events <> 1
           OR tag_events <> 1
    ) AS invalid_history_events

FROM raw.initial_question_metadata_2023;


SELECT
    COUNT(*) AS cohort_users,
    COUNT(m.question_id) AS matched_questions,

    COUNT(*) FILTER (
        WHERE m.question_id IS NULL
    ) AS unmatched_questions

FROM raw.first_questions_2023 f

LEFT JOIN raw.initial_question_metadata_2023 m
    ON f.first_question_id = m.question_id;
