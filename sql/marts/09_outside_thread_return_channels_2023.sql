SELECT
    CASE
        WHEN u.answered_24h
            THEN 'Ответ за 24 часа'
        ELSE 'Нет ответа за 24 часа'
    END AS answer_group,

    COUNT(*) AS users_count,

    -- Возвращение через публикации
    COUNT(*) FILTER (
        WHERE r.other_posts_30d > 0
    ) AS post_returns,

    -- Возвращение через комментарии
    COUNT(*) FILTER (
        WHERE r.other_comments_30d > 0
    ) AS comment_returns,

    -- Оба типа активности
    COUNT(*) FILTER (
        WHERE r.other_posts_30d > 0
          AND r.other_comments_30d > 0
    ) AS both_types,

    -- Только публикации
    COUNT(*) FILTER (
        WHERE r.other_posts_30d > 0
          AND r.other_comments_30d = 0
    ) AS post_only,

    -- Только комментарии
    COUNT(*) FILTER (
        WHERE r.other_posts_30d = 0
          AND r.other_comments_30d > 0
    ) AS comment_only,

    -- Общая возвращаемость
    COUNT(*) FILTER (
        WHERE r.returned_outside_first_thread_30d
    ) AS total_returns

FROM analytics.user_retention_2023 u

JOIN analytics.return_outside_first_thread_2023 r
    ON u.user_id = r.user_id

GROUP BY u.answered_24h
ORDER BY u.answered_24h DESC;