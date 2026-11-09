
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
      AND first_question_at < '2026-01-01'
),
user_returns AS (
    SELECT
        c.user_id,
        c.first_question_at,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM Posts p
                WHERE p.PostTypeId = 1
                  AND p.OwnerUserId = c.user_id
                  AND p.CreationDate > c.first_question_at
                  AND p.CreationDate <= DATEADD(
                      DAY, 30, c.first_question_at
                  )
            )
            THEN 1 ELSE 0
        END AS repeat_30d
    FROM cohort c
)
SELECT
    YEAR(first_question_at) AS cohort_year,
    COUNT(*) AS new_authors,
    SUM(repeat_30d) AS repeat_authors_30d,
    CAST(
        100.0 * SUM(repeat_30d)
        / NULLIF(COUNT(*), 0)
        AS DECIMAL(5, 2)
    ) AS repeat_question_rate_30d
FROM user_returns
GROUP BY YEAR(first_question_at)
ORDER BY cohort_year;
