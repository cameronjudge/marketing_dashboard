new_awesome_by_source = """
SELECT
    DATE_TRUNC('week', created_at)::date as week_start,
    CASE
        WHEN plan_route = 'direct' AND upgrade_route::VARCHAR = 'From upgrade' THEN 'direct'
        WHEN plan_route = 'free_trial' THEN 'free_trial'
        WHEN upgrade_route::VARCHAR = 'From uncancelled' THEN 'reopened'
        ELSE 'other'
    END AS upgrade_path,
    COUNT(*) as count_of_upgrades
FROM dbt.mp__evt_shop_upgrades
WHERE date(created_at) >= DATEADD(YEAR, -1, CURRENT_DATE)
AND DATE_TRUNC('week', created_at) < DATE_TRUNC('week', CURRENT_DATE)
GROUP BY
    week_start,
    upgrade_path
ORDER BY
    week_start DESC,
    upgrade_path
"""