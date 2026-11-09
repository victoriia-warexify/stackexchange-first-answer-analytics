SELECT
    YEAR(CreationDate) AS year,
    COUNT(*) AS questions_count,
    COUNT(DISTINCT OwnerUserId) AS unique_authors
FROM Posts
WHERE PostTypeId = 1
    AND CreationDate >= '2023-01-01'
    AND CreationDate < '2026-01-01'
GROUP BY YEAR(CreationDate)
ORDER BY year;
