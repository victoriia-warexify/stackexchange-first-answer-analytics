SELECT
    Id AS post_id,
    OwnerUserId AS user_id,
    PostTypeId AS post_type_id,
    CreationDate AS event_at
FROM Posts
WHERE PostTypeId IN (1, 2)
  AND OwnerUserId IS NOT NULL
  AND CreationDate >= '2023-01-01'
  AND CreationDate < '2024-01-31'
ORDER BY CreationDate, Id;