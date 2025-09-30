core_metrics = """
-- Combined Net Upgrades and Upgrade Type Breakdown
WITH upgrades AS (
    SELECT
        DATE_TRUNC('week', upgraded_at)::date AS week_start,
        shop_id,
        upgraded_at,
        created_at,
        downgraded_at
    FROM pg.extensions
    WHERE key = 'core'
      AND upgraded_at IS NOT NULL
      AND upgraded_at >= DATEADD(WEEK, -22, CURRENT_DATE)
      AND DATE_TRUNC('week', upgraded_at) < DATE_TRUNC('week', CURRENT_DATE)
),
upgrade_counts AS (
    SELECT
        week_start,
        COUNT(*) AS count_of_upgrades
    FROM upgrades
    GROUP BY week_start
),
downgrades AS (
    SELECT
        DATE_TRUNC('week', downgraded_at)::date AS week_start,
        COUNT(*) AS count_of_downgrades
    FROM pg.extensions
    WHERE key = 'core'
      AND downgraded_at IS NOT NULL
      AND downgraded_at >= DATEADD(WEEK, -22, CURRENT_DATE)
      AND DATE_TRUNC('week', downgraded_at) < DATE_TRUNC('week', CURRENT_DATE)
    GROUP BY week_start
),
prior_downgrades AS (
    SELECT DISTINCT
        u.week_start,
        e2.shop_id
    FROM pg.extensions e2
    JOIN upgrades u
      ON e2.shop_id = u.shop_id
     AND e2.key = 'core'
     AND e2.downgraded_at IS NOT NULL
     AND e2.downgraded_at < u.upgraded_at
     AND e2.created_at < u.upgraded_at
),
recent_trials AS (
    SELECT DISTINCT
        u.week_start,
        t.shop_id,
        u.upgraded_at
    FROM pg.shop_trials t
    JOIN upgrades u
      ON t.shop_id = u.shop_id
     AND t.created_at < u.upgraded_at
     AND t.created_at > u.upgraded_at - INTERVAL '30 days'
),
categorized_upgrades AS (
    SELECT
        u.week_start,
        u.shop_id,
        u.upgraded_at,
        CASE
            WHEN pd.shop_id IS NOT NULL THEN 'Shop Reopened'
            WHEN rt.shop_id IS NOT NULL THEN 'Free Trial'
            ELSE 'Direct Upgrade'
        END as upgrade_type
    FROM upgrades u
    LEFT JOIN prior_downgrades pd
      ON pd.shop_id = u.shop_id
     AND pd.week_start = u.week_start
    LEFT JOIN recent_trials rt
      ON rt.shop_id = u.shop_id
     AND rt.week_start = u.week_start
     AND rt.upgraded_at = u.upgraded_at
),
upgrade_breakdown AS (
    SELECT
        week_start,
        SUM(CASE WHEN upgrade_type = 'Direct Upgrade' THEN 1 ELSE 0 END) as direct_upgrades,
        SUM(CASE WHEN upgrade_type = 'Free Trial' THEN 1 ELSE 0 END) as trial_conversions,
        SUM(CASE WHEN upgrade_type = 'Shop Reopened' THEN 1 ELSE 0 END) as reopened_shops
    FROM categorized_upgrades
    GROUP BY week_start
),
all_weeks AS (
    SELECT DISTINCT week_start FROM (
        SELECT week_start FROM upgrade_counts
        UNION
        SELECT week_start FROM downgrades
    ) combined
),
trial_campaign_metrics AS (
	select * from dbt.agg_weekly_trial_campaign_metrics
where week < DATE_TRUNC('week', CURRENT_DATE)
and week >= DATE_TRUNC('week', CURRENT_DATE - INTERVAL '52 weeks')
)

SELECT
    TO_CHAR(w.week_start, 'YYYY-MM-DD') as week,
    COALESCE(uc.count_of_upgrades, 0) AS core_upgrades,
    COALESCE(d.count_of_downgrades, 0) AS core_downgrades,
    COALESCE(uc.count_of_upgrades, 0) - COALESCE(d.count_of_downgrades, 0) AS core_net_upgrades,
    COALESCE(ub.direct_upgrades, 0) as direct_upgrades,
    COALESCE(ub.trial_conversions, 0) as trial_conversions,
    COALESCE(ub.reopened_shops, 0) as reopened_shops,
	COALESCE(tc.home_trials, 0) as home_trials,
	COALESCE(tc.upsell_trials, 0) as upsell_trials,
	COALESCE(tc.optin_trials, 0) as optin_trials,
	COALESCE(tc.article_trials, 0) as article_trials,
	COALESCE(tc.welcome_trials, 0) as welcome_trials
-- 	COALESCE(tc.cs_trials, 0) as cs_trials,
-- 	COALESCE(tc.days_7, 0) as days_7_trials,
-- 	COALESCE(tc.days_15, 0) as days_15_trials,
-- 	COALESCE(tc.days_30, 0) as days_30_trials,
-- 	COALESCE(tc.days_45, 0) as days_45_trials

FROM all_weeks w
    LEFT JOIN upgrade_counts uc ON w.week_start = uc.week_start
    LEFT JOIN downgrades d ON w.week_start = d.week_start
    LEFT JOIN upgrade_breakdown ub ON w.week_start = ub.week_start
	LEFT JOIN trial_campaign_metrics tc ON tc.week = w.week_start
ORDER BY w.week_start DESC;
"""