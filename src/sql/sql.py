time_to_value_query = """
"""


test_query = """
select * from pg.extensions limit 1

"""

time_to_first_review_query = """
-- Time to Show First Review - Weekly Metric
-- Measures average days from extension download → widget enabled → first review shown
-- Removes outliers (shops taking > 180 days)

WITH
-- Extension download dates
core_extensions AS (
    SELECT
        shop_id,
        MIN(created_at) AS extension_installed_at
    FROM pg.extensions
    WHERE key = 'core'
      AND deleted_at IS NULL
    GROUP BY shop_id
),

-- Widget enablement (combining explicit logs and auto-installed)
widget_enabled AS (
    -- Explicit enablement from logs
    SELECT
        shop_id,
        MIN(created_at) AS widget_enabled_at
    FROM pg.setting_logs
    WHERE key IN ('review_widget_enabled', 'shopify_core_embed_block_enabled')
      AND new_value = 'true'
    GROUP BY shop_id

    UNION ALL

    -- Auto-installed widgets
    SELECT
        s.shop_id,
        e.created_at AS widget_enabled_at
    FROM pg.settings s
    INNER JOIN pg.extensions e ON s.shop_id = e.shop_id
    INNER JOIN dbt.installed_widgets_by_shops iw ON s.shop_id = iw.shop_id
    WHERE s.auto_install_widget = '1'
      AND e.key = 'core'
      AND e.deleted_at IS NULL
      AND iw.installed_widgets_count > 0
      AND s.shop_id NOT IN (
          SELECT DISTINCT shop_id
          FROM pg.setting_logs
          WHERE key IN ('review_widget_enabled', 'shopify_core_embed_block_enabled')
            AND new_value = 'true'
      )
),

widget_enabled_dedup AS (
    SELECT
        shop_id,
        MIN(widget_enabled_at) AS widget_enabled_at
    FROM widget_enabled
    GROUP BY shop_id
),

-- First published review
first_reviews AS (
    SELECT
        shop_id,
        MIN(made_at) AS first_review_date
    FROM pg.reviews
    WHERE curated = 'ok'
      AND hidden = 0
      AND made_at IS NOT NULL
    GROUP BY shop_id
),

-- Calculate journey for each shop
shop_journeys AS (
    SELECT
        s.id AS shop_id,
        s.awesome,
        ce.extension_installed_at,
        we.widget_enabled_at,
        fr.first_review_date,

        -- The "first review shown" happens when all three conditions are met
        GREATEST(
            ce.extension_installed_at,
            COALESCE(we.widget_enabled_at, ce.extension_installed_at),
            fr.first_review_date
        ) AS first_review_shown_date,

        -- Calculate days from extension install to first review shown as decimal
        -- Using DATEDIFF with hours and dividing by 24.0 to get fractional days
        DATEDIFF(
            hour,
            ce.extension_installed_at,
            GREATEST(
                ce.extension_installed_at,
                COALESCE(we.widget_enabled_at, ce.extension_installed_at),
                fr.first_review_date
            )
        ) / 24.0 AS days_to_first_review

    FROM pg.shops s
    INNER JOIN core_extensions ce ON s.id = ce.shop_id
    INNER JOIN first_reviews fr ON s.id = fr.shop_id
    LEFT JOIN widget_enabled_dedup we ON s.id = we.shop_id
    
    -- Filter for shops that have completed the journey
    WHERE ce.extension_installed_at IS NOT NULL
      AND fr.first_review_date IS NOT NULL
      -- Uncomment if widget enablement is required
      -- AND we.widget_enabled_at IS NOT NULL
)

-- Weekly aggregation with outlier removal
SELECT
    DATE_TRUNC('week', first_review_shown_date)::date AS week,

    -- Volume metrics
    COUNT(*) AS shops_showing_first_review,

    -- Core metric: Average time to first review (removing outliers)
    AVG(CASE
        WHEN days_to_first_review BETWEEN 0 AND 180
        THEN days_to_first_review
    END)::DECIMAL(10,2) AS avg_days_to_first_review,

    -- Median is less sensitive to outliers
    MEDIAN(CASE
        WHEN days_to_first_review BETWEEN 0 AND 180
        THEN days_to_first_review
    END)::DECIMAL(10,2) AS median_days_to_first_review,

    -- By plan type
    AVG(CASE
        WHEN awesome = '1' AND days_to_first_review BETWEEN 0 AND 180
        THEN days_to_first_review
    END)::DECIMAL(10,2) AS avg_days_awesome_plan,

    AVG(CASE
        WHEN awesome = '0' AND days_to_first_review BETWEEN 0 AND 180
        THEN days_to_first_review
    END)::DECIMAL(10,2) AS avg_days_free_plan

FROM shop_journeys
WHERE first_review_shown_date >= DATE_TRUNC('week', DATEADD(month, -12, CURRENT_DATE))
  AND first_review_shown_date <= DATE_TRUNC('week', CURRENT_DATE)
GROUP BY 1
ORDER BY 1 DESC
"""