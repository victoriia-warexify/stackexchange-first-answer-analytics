
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

user_activity AS (
    SELECT
        c.user_id,

        CASE WHEN EXISTS (
            SELECT 1
            FROM Posts p
            WHERE p.OwnerUserId = c.user_id
              AND p.PostTypeId IN (1, 2)
              AND p.CreationDate >
                  DATEADD(HOUR, 24, c.first_question_at)
              AND p.CreationDate <=
                  DATEADD(DAY, 30, c.first_question_at)
        )
        THEN 1 ELSE 0 END AS returned_with_post,

        CASE WHEN EXISTS (
            SELECT 1
            FROM Comments cm
            WHERE cm.UserId = c.user_id
              AND cm.CreationDate >
                  DATEADD(HOUR, 24, c.first_question_at)
              AND cm.CreationDate <=
                  DATEADD(DAY, 30, c.first_question_at)
        )
        THEN 1 ELSE 0 END AS returned_with_comment

    FROM cohort c
)

SELECT
    COUNT(*) AS new_authors,

    SUM(returned_with_post) AS post_returns,

    SUM(returned_with_comment) AS comment_returns,

    SUM(
        CASE
            WHEN returned_with_post = 1
              OR returned_with_comment = 1
            THEN 1 ELSE 0
        END
    ) AS returned_30d,

    CAST(
        100.0 * SUM(
            CASE
                WHEN returned_with_post = 1
                  OR returned_with_comment = 1
                THEN 1 ELSE 0
            END
        ) / NULLIF(COUNT(*), 0)
        AS DECIMAL(5, 2)
    ) AS return_rate_30d

FROM user_activity;
