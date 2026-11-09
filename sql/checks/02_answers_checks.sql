SELECT
    COUNT(*) AS total_answers,
    COUNT(DISTINCT answer_id) AS unique_answers,
    COUNT(DISTINCT question_id) AS unique_questions,
    COUNT(*) - COUNT(answer_author_id) AS missing_authors,
    MIN(answer_at) AS min_answer_at,
    MAX(answer_at) AS max_answer_at
FROM raw.answers_to_2023_questions;
