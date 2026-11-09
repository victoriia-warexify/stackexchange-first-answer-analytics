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
),

first_posts AS (
    SELECT
        c.user_id,
        c.first_question_at,
        MIN(p.Id) AS first_question_id
    FROM cohort c
    JOIN Posts p
        ON p.OwnerUserId = c.user_id
       AND p.CreationDate = c.first_question_at
       AND p.PostTypeId = 1
    GROUP BY
        c.user_id,
        c.first_question_at
),

answer_flags AS (
    SELECT
        f.user_id,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM Posts a
                WHERE a.PostTypeId = 2
                  AND a.ParentId = f.first_question_id
                  AND a.OwnerUserId <> f.user_id
                  AND a.CreationDate <= DATEADD(
                      HOUR, 24, f.first_question_at
                  )
            )
            THEN 1 ELSE 0
        END AS answered_24h
    FROM first_posts f
)

SELECT
    COUNT(*) AS new_authors,
    SUM(answered_24h) AS answered_24h,
    COUNT(*) - SUM(answered_24h) AS not_answered_24h,
    CAST(
        100.0 * SUM(answered_24h)
        / NULLIF(COUNT(*), 0)
        AS DECIMAL(5, 2)
    ) AS answer_rate_24h
FROM answer_flags;
