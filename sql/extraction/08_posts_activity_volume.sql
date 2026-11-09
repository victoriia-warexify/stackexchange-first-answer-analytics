SELECT
    YEAR(CreationDate) AS year,
    MONTH(CreationDate) AS month,
    COUNT(*) AS posts_count
FROM Posts
WHERE PostTypeId IN (1, 2)
  AND OwnerUserId IS NOT NULL
  AND CreationDate >= '2023-01-01'
  AND CreationDate < '2024-01-31'
GROUP BY
    YEAR(CreationDate),
    MONTH(CreationDate)
ORDER BY year, month;