CREATE TABLE IF NOT EXISTS raw.comments_activity (
    comment_id BIGINT,
    user_id BIGINT,
    post_id BIGINT,
    event_at TIMESTAMP WITHOUT TIME ZONE
);