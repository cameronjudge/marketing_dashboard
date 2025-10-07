core_metrics = """
-- Combined Net Upgrades and Upgrade Type Breakdown with Trial Conversion Tracking
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
      AND upgraded_at >= DATEADD(WEEK, -30, CURRENT_DATE)
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
      AND downgraded_at >= DATEADD(WEEK, -30, CURRENT_DATE)
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
    SELECT * FROM dbt.agg_weekly_trial_campaign_metrics
    WHERE week < DATE_TRUNC('week', CURRENT_DATE)
    AND week >= DATE_TRUNC('week', CURRENT_DATE - INTERVAL '30 weeks')
),

-- NEW: Trial Conversion Tracking
weekly_trial_starts AS (
    SELECT
        ts.shop_id,
        DATE_TRUNC('week', ts.trial_start_date)::date AS trial_week,
        ts.trial_start_date,
        ts.trial_expiration_date::timestamp AS trial_expiration_date,
        ts.trial_campaign_handle::VARCHAR AS trial_campaign_handle,
        CASE
            WHEN ts.trial_campaign_handle LIKE '%home%' THEN 'home'
            WHEN ts.trial_campaign_handle LIKE '%upsell%' THEN 'upsell'
            WHEN ts.trial_campaign_handle LIKE '%opt-in%' AND ts.trial_campaign_handle NOT LIKE '%home%' THEN 'optin'
            WHEN ts.trial_campaign_handle LIKE '%article%' THEN 'article'
            WHEN ts.trial_campaign_handle LIKE '%welcome%' AND ts.trial_campaign_handle NOT LIKE '%opt-in%' THEN 'welcome'
            WHEN ts.trial_campaign_handle LIKE '%cs_%' OR ts.trial_campaign_handle LIKE '%cs-%' THEN 'cs'
            ELSE 'other'
        END AS campaign_type
    FROM dbt.mp__evt_trial_started ts
    WHERE ts.trial_start_date IS NOT NULL
        AND ts.trial_expiration_date IS NOT NULL
        AND ts.trial_start_date >= DATEADD(WEEK, -30, CURRENT_DATE)
        AND DATE_TRUNC('week', ts.trial_start_date) < DATE_TRUNC('week', CURRENT_DATE)
),

trial_conversions AS (
    SELECT
        wts.trial_week,
        wts.campaign_type,
        COUNT(CASE WHEN wts.trial_expiration_date < CURRENT_DATE THEN 1 END) AS completed_trials,
        SUM(CASE
            WHEN ext.upgraded_at IS NOT NULL
                AND (ext.downgraded_at IS NULL OR ext.downgraded_at > wts.trial_expiration_date)
                AND (ext.deleted_at IS NULL OR ext.deleted_at > wts.trial_expiration_date)
                AND wts.trial_expiration_date < CURRENT_DATE
            THEN 1
            ELSE 0
        END) AS successful_conversions
    FROM weekly_trial_starts wts
    LEFT JOIN pg.extensions ext
        ON wts.shop_id = ext.shop_id
        AND ext.key = 'core'
        AND (ext.deleted_at IS NULL OR ext.deleted_at > wts.trial_start_date)
    GROUP BY wts.trial_week, wts.campaign_type
),

trial_conversion_pivot AS (
    SELECT
        trial_week,
        SUM(CASE WHEN campaign_type = 'home' THEN completed_trials ELSE 0 END) as home_completed,
        SUM(CASE WHEN campaign_type = 'home' THEN successful_conversions ELSE 0 END) as home_conversions,
        SUM(CASE WHEN campaign_type = 'upsell' THEN completed_trials ELSE 0 END) as upsell_completed,
        SUM(CASE WHEN campaign_type = 'upsell' THEN successful_conversions ELSE 0 END) as upsell_conversions,
        SUM(CASE WHEN campaign_type = 'optin' THEN completed_trials ELSE 0 END) as optin_completed,
        SUM(CASE WHEN campaign_type = 'optin' THEN successful_conversions ELSE 0 END) as optin_conversions,
        SUM(CASE WHEN campaign_type = 'article' THEN completed_trials ELSE 0 END) as article_completed,
        SUM(CASE WHEN campaign_type = 'article' THEN successful_conversions ELSE 0 END) as article_conversions,
        SUM(CASE WHEN campaign_type = 'welcome' THEN completed_trials ELSE 0 END) as welcome_completed,
        SUM(CASE WHEN campaign_type = 'welcome' THEN successful_conversions ELSE 0 END) as welcome_conversions
    FROM trial_conversions
    GROUP BY trial_week
),

installs as (
    SELECT
        DATE_TRUNC('week', created_at)::date AS week_start,
        count(*) AS count_of_installs
    FROM pg.extensions
    WHERE key = 'core'
      AND created_at >= DATEADD(WEEK, -30, CURRENT_DATE)
      AND DATE_TRUNC('week', created_at) < DATE_TRUNC('week', CURRENT_DATE)
    GROUP BY week_start
),

uninstalls as (
    SELECT
        DATE_TRUNC('week', deleted_at)::date AS week_start,
        count(*) AS count_of_uninstalls
    FROM pg.extensions
    WHERE key = 'core'
      AND deleted_at IS NOT NULL
      AND created_at >= DATEADD(WEEK, -30, CURRENT_DATE)
      AND DATE_TRUNC('week', deleted_at) < DATE_TRUNC('week', CURRENT_DATE)
    GROUP BY week_start
),

net_installs as (
    SELECT
        i.week_start,
        i.count_of_installs - u.count_of_uninstalls AS net_installs
    FROM installs i
    LEFT JOIN uninstalls u
      ON i.week_start = u.week_start
)

SELECT
    TO_CHAR(w.week_start, 'YYYY-MM-DD') as week,
    COALESCE(uc.count_of_upgrades, 0) AS core_upgrades,
    COALESCE(d.count_of_downgrades, 0) AS core_downgrades,
    COALESCE(uc.count_of_upgrades, 0) - COALESCE(d.count_of_downgrades, 0) AS core_net_upgrades,
    COALESCE(ub.direct_upgrades, 0) as direct_upgrades,
    COALESCE(ub.trial_conversions, 0) as trial_conversions,
    COALESCE(ub.reopened_shops, 0) as reopened_shops,

    -- Trial Starts (from existing metrics)
    COALESCE(tc.home_trials, 0) as home_trials,
    COALESCE(tc.upsell_trials, 0) as upsell_trials,
    COALESCE(tc.optin_trials, 0) as optin_trials,
    COALESCE(tc.article_trials, 0) as article_trials,
    COALESCE(tc.welcome_trials, 0) as welcome_trials,

    -- Trial Conversions (NEW)
    COALESCE(tcp.home_conversions, 0) as home_conversions,
    COALESCE(tcp.home_completed, 0) as home_completed,
    ROUND(100.0 * COALESCE(tcp.home_conversions, 0) / NULLIF(COALESCE(tcp.home_completed, 0), 0), 2) as home_cvr_pct,

    COALESCE(tcp.upsell_conversions, 0) as upsell_conversions,
    COALESCE(tcp.upsell_completed, 0) as upsell_completed,
    ROUND(100.0 * COALESCE(tcp.upsell_conversions, 0) / NULLIF(COALESCE(tcp.upsell_completed, 0), 0), 2) as upsell_cvr_pct,

    COALESCE(tcp.optin_conversions, 0) as optin_conversions,
    COALESCE(tcp.optin_completed, 0) as optin_completed,
    ROUND(100.0 * COALESCE(tcp.optin_conversions, 0) / NULLIF(COALESCE(tcp.optin_completed, 0), 0), 2) as optin_cvr_pct,

    COALESCE(tcp.article_conversions, 0) as article_conversions,
    COALESCE(tcp.article_completed, 0) as article_completed,
    ROUND(100.0 * COALESCE(tcp.article_conversions, 0) / NULLIF(COALESCE(tcp.article_completed, 0), 0), 2) as article_cvr_pct,

    COALESCE(tcp.welcome_conversions, 0) as welcome_conversions,
    COALESCE(tcp.welcome_completed, 0) as welcome_completed,
    ROUND(100.0 * COALESCE(tcp.welcome_conversions, 0) / NULLIF(COALESCE(tcp.welcome_completed, 0), 0), 2) as welcome_cvr_pct,

    COALESCE(ni.net_installs, 0) as net_installs

FROM all_weeks w
    LEFT JOIN upgrade_counts uc ON w.week_start = uc.week_start
    LEFT JOIN downgrades d ON w.week_start = d.week_start
    LEFT JOIN upgrade_breakdown ub ON w.week_start = ub.week_start
    LEFT JOIN trial_campaign_metrics tc ON tc.week = w.week_start
    LEFT JOIN trial_conversion_pivot tcp ON tcp.trial_week = w.week_start
    LEFT JOIN net_installs ni ON ni.week_start = w.week_start
ORDER BY w.week_start DESC;
"""