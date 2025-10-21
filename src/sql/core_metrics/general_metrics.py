general_metrics = """ SELECT
    week,
    key,
    value
FROM (
    SELECT
        DATE_TRUNC('week', metric_timestamp)::date AS week,
        key,
        value,
        ROW_NUMBER() OVER (
            PARTITION BY DATE_TRUNC('week', metric_timestamp), key
            ORDER BY metric_timestamp DESC
        ) AS rn
    FROM pg.general_metrics
    WHERE DATE_TRUNC('week', metric_timestamp) < DATE_TRUNC('week', CURRENT_DATE)
) ranked
WHERE rn = 1
ORDER BY week, key

"""