CREATE OR REPLACE VIEW analytics.user_model_features_2023 AS

WITH question_tags AS (
    SELECT
        f.user_id,
        t.tag_name

    FROM raw.first_questions_2023 f

    JOIN raw.initial_question_metadata_2023 m
        ON f.first_question_id = m.question_id

    CROSS JOIN LATERAL regexp_split_to_table(
        TRIM(BOTH '<>' FROM m.initial_tags),
        '><'
    ) AS t(tag_name)

    WHERE m.initial_tags ~ '^(<[^<>]+>)+$'
),

tag_features AS (
    SELECT
        user_id,

        COUNT(*) FILTER (
            WHERE tag_name = 'regression'
        ) > 0 AS has_regression,

        COUNT(*) FILTER (
            WHERE tag_name = 'r'
        ) > 0 AS has_r,

        COUNT(*) FILTER (
            WHERE tag_name = 'machine-learning'
        ) > 0 AS has_machine_learning,

        COUNT(*) FILTER (
            WHERE tag_name = 'hypothesis-testing'
        ) > 0 AS has_hypothesis_testing,

        COUNT(*) FILTER (
            WHERE tag_name = 'time-series'
        ) > 0 AS has_time_series,

        COUNT(*) FILTER (
            WHERE tag_name = 'probability'
        ) > 0 AS has_probability,

        COUNT(*) FILTER (
            WHERE tag_name = 'mathematical-statistics'
        ) > 0 AS has_mathematical_statistics,

        COUNT(*) FILTER (
            WHERE tag_name = 'mixed-model'
        ) > 0 AS has_mixed_model,

        COUNT(*) FILTER (
            WHERE tag_name = 'statistical-significance'
        ) > 0 AS has_statistical_significance

    FROM question_tags

    GROUP BY user_id
)

SELECT
    u.*,

    COALESCE(t.has_regression, FALSE)::INT
        AS has_regression,

    COALESCE(t.has_r, FALSE)::INT
        AS has_r,

    COALESCE(t.has_machine_learning, FALSE)::INT
        AS has_machine_learning,

    COALESCE(t.has_hypothesis_testing, FALSE)::INT
        AS has_hypothesis_testing,

    COALESCE(t.has_time_series, FALSE)::INT
        AS has_time_series,

    COALESCE(t.has_probability, FALSE)::INT
        AS has_probability,

    COALESCE(t.has_mathematical_statistics, FALSE)::INT
        AS has_mathematical_statistics,

    COALESCE(t.has_mixed_model, FALSE)::INT
        AS has_mixed_model,

    COALESCE(t.has_statistical_significance, FALSE)::INT
        AS has_statistical_significance

FROM analytics.user_features_2023 u

LEFT JOIN tag_features t
    ON u.user_id = t.user_id;