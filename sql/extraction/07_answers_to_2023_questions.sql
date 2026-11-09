SELECT
    a.Id AS answer_id,
    a.ParentId AS question_id,
    a.OwnerUserId AS answer_author_id,
    a.CreationDate AS answer_at

FROM Posts q
JOIN Posts a
    ON a.ParentId = q.Id

WHERE q.PostTypeId = 1
  AND a.PostTypeId = 2

  -- Вопросы, опубликованные в 2023 году
  AND q.CreationDate >= '2023-01-01'
  AND q.CreationDate < '2024-01-01'

  -- Ответы в течение первых 30 дней
  AND a.CreationDate >= q.CreationDate
  AND a.CreationDate <= DATEADD(
      DAY, 30, q.CreationDate
  );