SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT first_question_id) AS unique_questions,
    COUNT(*) - COUNT(user_id) AS missing_user_ids,
    COUNT(*) - COUNT(first_question_id) AS missing_question_ids,
    COUNT(*) - COUNT(first_question_at) AS missing_dates,
    MIN(first_question_at) AS min_date,
    MAX(first_question_at) AS max_date
FROM raw.first_questions_2023;