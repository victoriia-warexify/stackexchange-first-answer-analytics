DO $$
DECLARE
    cohort_count BIGINT;
    features_count BIGINT;
BEGIN
    -- 1. Когорта не должна быть пустой
    SELECT COUNT(*) INTO cohort_count
    FROM raw.first_questions_2023;

    IF cohort_count = 0 THEN
        RAISE EXCEPTION 'Когорта пользователей пуста';
    END IF;

    -- 2. Корректность первых вопросов
    IF EXISTS (
        SELECT 1
        FROM raw.first_questions_2023
        WHERE first_question_id IS NULL
           OR first_question_at IS NULL
           OR first_question_at < TIMESTAMP '2023-01-01'
           OR first_question_at >= TIMESTAMP '2024-01-01'
    ) THEN
        RAISE EXCEPTION
            'Некорректные идентификаторы или даты первых вопросов';
    END IF;

    -- 3. Корректность выгрузки ответов
    IF EXISTS (
        SELECT 1
        FROM raw.answers_to_2023_questions
        WHERE question_id IS NULL
           OR answer_at IS NULL
    ) THEN
        RAISE EXCEPTION 'Некорректные записи ответов';
    END IF;

    -- 4. Корректность публикаций
    IF EXISTS (
        SELECT 1
        FROM raw.posts_activity_2023
        WHERE user_id IS NULL
           OR post_type_id IS NULL
           OR post_type_id NOT IN (1, 2)
           OR event_at IS NULL
           OR event_at < TIMESTAMP '2023-01-01'
           OR event_at >= TIMESTAMP '2024-01-31'
    ) THEN
        RAISE EXCEPTION 'Некорректные события публикаций';
    END IF;

    -- 5. Корректность комментариев
    IF EXISTS (
        SELECT 1
        FROM raw.comments_activity
        WHERE user_id IS NULL
           OR post_id IS NULL
           OR event_at IS NULL
           OR event_at < TIMESTAMP '2023-01-01'
           OR event_at >= TIMESTAMP '2024-01-31'
    ) THEN
        RAISE EXCEPTION 'Некорректные события комментариев';
    END IF;

    -- 6. Регистрационные данные должны
    -- соответствовать пользовательской когорте
    IF EXISTS (
        SELECT 1
        FROM raw.first_questions_2023 f
        LEFT JOIN raw.user_registration_2023 r
            ON f.user_id = r.user_id
        WHERE r.user_id IS NULL
           OR r.first_question_at IS DISTINCT FROM f.first_question_at
    ) THEN
        RAISE EXCEPTION
            'Регистрационные данные не соответствуют когорте';
    END IF;

    -- 7. Проверка связи с метаданными вопроса
    IF EXISTS (
        SELECT 1
        FROM raw.first_questions_2023 f
        LEFT JOIN raw.initial_question_metadata_2023 m
            ON f.first_question_id = m.question_id
        WHERE m.question_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Отсутствуют метаданные первых вопросов';
    END IF;

    -- 8. Проверка размера модельной витрины
    SELECT COUNT(*) INTO features_count
    FROM analytics.user_model_features_2023;

    IF features_count <> cohort_count THEN
        RAISE EXCEPTION
            'Размер витрины (%) не совпадает с когортой (%)',
            features_count, cohort_count;
    END IF;

    -- 9. Уникальность пользователей в витрине
    IF EXISTS (
        SELECT 1
        FROM analytics.user_model_features_2023
        GROUP BY user_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'В модельной витрине обнаружены дубликаты';
    END IF;

    -- 10. Полнота обязательных признаков
    IF EXISTS (
        SELECT 1
        FROM analytics.user_model_features_2023
        WHERE answered_24h IS NULL
           OR returned_30d IS NULL
           OR title_length IS NULL
           OR tags_count IS NULL
           OR question_month IS NULL
           OR question_weekday IS NULL
           OR question_hour IS NULL
    ) THEN
        RAISE EXCEPTION
            'В модельной витрине отсутствуют обязательные признаки';
    END IF;

    -- 11. Строгая метрика возвращаемости
    -- должна быть подмножеством первоначальной
    IF EXISTS (
        SELECT 1
        FROM analytics.user_model_features_2023 v
        JOIN analytics.user_retention_2023 u
            ON v.user_id = u.user_id
        WHERE v.returned_30d
          AND NOT COALESCE(u.returned_30d, FALSE)
    ) THEN
        RAISE EXCEPTION
            'Нарушена согласованность метрик возвращаемости';
    END IF;

    RAISE NOTICE
        'Проверки качества пройдены. Пользователей: %',
        cohort_count;
END $$;