DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'raw.first_questions_2023'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE raw.first_questions_2023
        ADD CONSTRAINT pk_first_questions_2023
        PRIMARY KEY (user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'raw.answers_to_2023_questions'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE raw.answers_to_2023_questions
        ADD CONSTRAINT pk_answers_to_2023_questions
        PRIMARY KEY (answer_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'raw.posts_activity_2023'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE raw.posts_activity_2023
        ADD CONSTRAINT pk_posts_activity_2023
        PRIMARY KEY (post_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'raw.comments_activity'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE raw.comments_activity
        ADD CONSTRAINT pk_comments_activity
        PRIMARY KEY (comment_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'raw.user_registration_2023'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE raw.user_registration_2023
        ADD CONSTRAINT pk_user_registration_2023
        PRIMARY KEY (user_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'raw.initial_question_metadata_2023'::regclass
          AND contype = 'p'
    ) THEN
        ALTER TABLE raw.initial_question_metadata_2023
        ADD CONSTRAINT pk_initial_question_metadata_2023
        PRIMARY KEY (question_id);
    END IF;
END $$;