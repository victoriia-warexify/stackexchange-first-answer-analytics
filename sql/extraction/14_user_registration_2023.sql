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
    c.first_question_at,
    u.CreationDate AS account_created_at

FROM cohort c

LEFT JOIN Users u
    ON c.user_id = u.Id

ORDER BY c.user_id;