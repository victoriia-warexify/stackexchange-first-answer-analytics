WITH questions_2023 AS (
    SELECT
        Id AS question_id
    FROM Posts
    WHERE PostTypeId = 1
      AND CreationDate >= '2023-01-01'
      AND CreationDate < '2024-01-01'
)

SELECT
    q.question_id,

    MAX(
        CASE
            WHEN h.PostHistoryTypeId = 1
            THEN h.Text
        END
    ) AS initial_title,

    MAX(
        CASE
            WHEN h.PostHistoryTypeId = 3
            THEN h.Text
        END
    ) AS initial_tags,

    COUNT(
        CASE
            WHEN h.PostHistoryTypeId = 1
            THEN 1
        END
    ) AS title_events,

    COUNT(
        CASE
            WHEN h.PostHistoryTypeId = 3
            THEN 1
        END
    ) AS tag_events

FROM questions_2023 q

LEFT JOIN PostHistory h
    ON h.PostId = q.question_id
   AND h.PostHistoryTypeId IN (1, 3)

GROUP BY q.question_id
ORDER BY q.question_id;