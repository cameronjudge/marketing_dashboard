#updated to core metrics
awesome_downgrade_rate = """
SELECT
    DATE_TRUNC('week', created_at)::date as week_start,
    CASE
        WHEN downgrade_route::VARCHAR = 'From cancelled' OR downgrade_route::VARCHAR = 'Mistakenly cancelled shop while it should have been cancelling Awesome plan' THEN 'cancelled'
        WHEN downgrade_route = 'free_trial' THEN 'free_trial'
        WHEN downgrade_route::VARCHAR = 'From downgrade' THEN 'downgrade'
        ELSE 'other'
    END AS downgrade_path,
    COUNT(*) as count_of_downgrades
FROM dbt.mp__evt_shop_downgrades
WHERE date(created_at) >= DATEADD(YEAR, -1, CURRENT_DATE)
AND DATE_TRUNC('week', created_at) < DATE_TRUNC('week', CURRENT_DATE)
GROUP BY
    week_start,
    downgrade_path
ORDER BY
    week_start DESC,
    downgrade_path
"""