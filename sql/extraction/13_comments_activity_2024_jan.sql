SELECT
    Id AS comment_id,
    UserId AS user_id,
    PostId AS post_id,
    CreationDate AS event_at
FROM Comments
WHERE UserId IS NOT NULL
  AND CreationDate >= '2024-01-01'
  AND CreationDate < '2024-01-31'
ORDER BY CreationDate, Id;