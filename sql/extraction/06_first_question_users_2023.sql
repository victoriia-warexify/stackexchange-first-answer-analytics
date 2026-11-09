
WITH first_questions AS (
    SELECT
        OwnerUserId AS user_id,
        MIN(CreationDate) AS first_question_at
    FROM Posts
    WHERE PostTypeId = 1
      AND OwnerUserId IS NOT NULL
    GROUP BY OwnerUserId
),

cohort AS (
    SELECT
        user_id,
        first_question_at
    FROM first_questions
    WHERE first_question_at >= '2023-01-01'
      AND first_question_at < '2024-01-01'
)

SELECT
    c.user_id,
    MIN(p.Id) AS first_question_id,
    c.first_question_at
FROM cohort c
JOIN Posts p
    ON p.OwnerUserId = c.user_id
   AND p.CreationDate = c.first_question_at
   AND p.PostTypeId = 1
GROUP BY
    c.user_id,
    c.first_question_at
ORDER BY c.user_id;
