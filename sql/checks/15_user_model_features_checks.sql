SELECT
    COUNT(*) AS total_users,
    COUNT(DISTINCT user_id) AS unique_users,

    COUNT(*) FILTER (WHERE answered_24h)
        AS answered_users,

    COUNT(*) FILTER (WHERE returned_30d)
        AS returned_users,

    SUM(has_regression) AS regression_users,
    SUM(has_r) AS r_users,
    SUM(has_machine_learning) AS ml_users,
    SUM(has_hypothesis_testing) AS hypothesis_users,
    SUM(has_time_series) AS time_series_users,
    SUM(has_probability) AS probability_users,
    SUM(has_mathematical_statistics) AS math_stats_users,
    SUM(has_mixed_model) AS mixed_model_users,
    SUM(has_statistical_significance) AS significance_users,

    COUNT(*) FILTER (WHERE account_age_days IS NULL)
        AS missing_account_age

FROM analytics.user_model_features_2023;