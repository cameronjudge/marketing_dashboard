monthly_core_metrics = """

-- Monthly User Growth Metrics: Free vs Awesome Plans with MoM Changes
WITH month_series AS (
    -- Generate series of months for the past 6 months
    SELECT
        DATE_TRUNC('month', DATEADD(month, -n, CURRENT_DATE))::date AS month_start,
        DATEADD(day, -1, DATEADD(month, 1, DATE_TRUNC('month', DATEADD(month, -n, CURRENT_DATE))))::date AS month_end
    FROM (SELECT row_number() over () - 1 as n FROM pg.shops LIMIT 13) series
    WHERE DATE_TRUNC('month', DATEADD(month, -n, CURRENT_DATE)) < DATE_TRUNC('month', CURRENT_DATE)
),

-- Calculate active users at end of each month
monthly_active_users AS (
    SELECT
        m.month_start,
        COUNT(DISTINCT CASE
            WHEN
                -- User is on Free plan if:
                -- 1. Never upgraded, OR
                -- 2. Downgraded and downgrade happened before month end
                (e.upgraded_at IS NULL OR
                 (e.downgraded_at IS NOT NULL AND e.downgraded_at <= m.month_end))
                -- AND shop is not marked as awesome
                AND (s.awesome IS NULL OR s.awesome != '1')
            THEN e.shop_id
        END) AS free_users,
        COUNT(DISTINCT CASE
            WHEN
                -- User is on Awesome plan if:
                -- 1. Shop is marked as awesome, OR
                -- 2. Upgraded before month end AND (not downgraded OR downgraded after month end)
                (s.awesome = '1' OR
                 (e.upgraded_at IS NOT NULL AND e.upgraded_at <= m.month_end
                  AND (e.downgraded_at IS NULL OR e.downgraded_at > m.month_end)))
            THEN e.shop_id
        END) AS awesome_users,
        COUNT(DISTINCT e.shop_id) AS total_users
    FROM month_series m
    JOIN pg.extensions e
        ON e.created_at <= m.month_end
        AND (e.deleted_at IS NULL OR e.deleted_at > m.month_end)
        AND e.key = 'core'
    JOIN pg.shops s
        ON e.shop_id = s.id
        AND s.platform = 'shopify'
    GROUP BY m.month_start
),

-- Calculate month-over-month changes
monthly_metrics AS (
    SELECT
        month_start,
        total_users,
        free_users,
        awesome_users,
        -- Previous month values
        LAG(total_users, 1) OVER (ORDER BY month_start) AS prev_month_total,
        LAG(free_users, 1) OVER (ORDER BY month_start) AS prev_month_free,
        LAG(awesome_users, 1) OVER (ORDER BY month_start) AS prev_month_awesome,
        -- Month-over-month changes
        total_users - LAG(total_users, 1) OVER (ORDER BY month_start) AS total_user_change,
        free_users - LAG(free_users, 1) OVER (ORDER BY month_start) AS free_user_change,
        awesome_users - LAG(awesome_users, 1) OVER (ORDER BY month_start) AS awesome_user_change
    FROM monthly_active_users
)

-- Final output with all metrics
SELECT
    TO_CHAR(m.month_start, 'YYYY-MM') AS month,

    -- Current Month Counts
    m.total_users,
    m.free_users,
    m.awesome_users,

    -- Month-over-Month Changes (absolute numbers)
    m.total_user_change AS total_change,
    m.free_user_change AS free_change,
    m.awesome_user_change AS awesome_change,

    -- Growth Rates (percentages) - Formula: ((This month - Last month) / Last month) * 100
    CASE
        WHEN m.prev_month_total > 0
        THEN ROUND((m.total_user_change::FLOAT / m.prev_month_total::FLOAT) * 100, 2)
        ELSE NULL
    END AS total_growth_rate_pct,

    CASE
        WHEN m.prev_month_free > 0
        THEN ROUND((m.free_user_change::FLOAT / m.prev_month_free::FLOAT) * 100, 2)
        ELSE NULL
    END AS free_growth_rate_pct,

    CASE
        WHEN m.prev_month_awesome > 0
        THEN ROUND((m.awesome_user_change::FLOAT / m.prev_month_awesome::FLOAT) * 100, 2)
        ELSE NULL
    END AS awesome_growth_rate_pct,

    -- Composition Percentages
    ROUND((m.free_users::FLOAT / NULLIF(m.total_users, 0)::FLOAT) * 100, 2) AS free_pct_of_total,
    ROUND((m.awesome_users::FLOAT / NULLIF(m.total_users, 0)::FLOAT) * 100, 2) AS awesome_pct_of_total

FROM monthly_metrics m
ORDER BY m.month_start DESC;

"""