WITH first_questions AS (
    SELECT
        OwnerUserId AS user_id,
        MIN(CreationDate) AS first_question_at
    FROM Posts
    WHERE PostTypeId = 1
      AND OwnerUserId IS NOT NULL
    GROUP BY OwnerUserId
)

SELECT
    YEAR(first_question_at) AS first_question_year,
    COUNT(*) AS new_authors
FROM first_questions
WHERE first_question_at >= '2023-01-01'
  AND first_question_at < '2026-01-01'
GROUP BY YEAR(first_question_at)
ORDER BY first_question_year;