SELECT
    YEAR(CreationDate) AS event_year,
    MONTH(CreationDate) AS event_month,
    COUNT(*) AS comments_count,
    SUM(COUNT(*)) OVER () AS total_comments
FROM Comments
WHERE UserId IS NOT NULL
  AND CreationDate >= '2023-01-01'
  AND CreationDate < '2024-01-31'
GROUP BY
    YEAR(CreationDate),
    MONTH(CreationDate)
ORDER BY
    event_year,
    event_month;