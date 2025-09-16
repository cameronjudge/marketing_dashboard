-- Showing First Review Metric
-- This query tracks shops that have displayed their first piece of social proof
-- Includes: App installation, widget enablement, and first review addition
-- Weekly aggregation for the last 12 months

-- IMPORTANT: This query may take time to run due to the large data volumes
-- Consider running with smaller date ranges first for testing

WITH date_bounds AS (
    -- Dynamic 12-month window
    SELECT
        DATE_TRUNC('week', DATEADD(month, -12, CURRENT_DATE)) AS start_date,
        DATE_TRUNC('week', CURRENT_DATE) AS end_date
),

-- Get shops with core extension installed (app download)
-- The core extension indicates the main Judge.me app is installed
core_extension_shops AS (
    SELECT
        shop_id,
        MIN(created_at) AS app_installed_at
    FROM pg.extensions
    WHERE key = 'core'
      AND deleted_at IS NULL
    GROUP BY shop_id
),

-- Get shops that have enabled widgets
-- This indicates they have product review widgets active on their site
widget_enabled_shops AS (
    SELECT
        shop_id,
        MIN(created_at) AS widget_enabled_at  -- First time widget was enabled
    FROM dbt.installed_widgets_by_shops
    WHERE installed_widgets_count > 0
    GROUP BY shop_id
),

-- Get first review for each shop by source
-- Only counting published, visible reviews as "social proof"
first_reviews AS (
    SELECT
        r.shop_id,
        MIN(r.created_at) AS first_review_at,
        MIN(CASE WHEN r.source = 'aliexpress' THEN r.created_at END) AS first_aliexpress_review_at,
        MIN(CASE WHEN r.source = 'email' THEN r.created_at END) AS first_email_review_at,
        MIN(CASE WHEN r.source = 'import' THEN r.created_at END) AS first_import_review_at,
        MIN(CASE WHEN r.source = 'web' THEN r.created_at END) AS first_web_review_at,
        COUNT(DISTINCT r.id) AS total_reviews
    FROM pg.reviews r
    INNER JOIN pg.products p ON r.product_id = p.id
    WHERE r.hidden = '0'  -- Only visible reviews count as social proof
      AND r.curated != 'unpublished'  -- Only published reviews
    GROUP BY r.shop_id
),

-- Combine all metrics to determine when each shop first showed social proof
shop_milestones AS (
    SELECT
        s.id AS shop_id,
        s.domain,
        s.platform,
        s.plan,
        s.awesome,
        s.created_at AS shop_created_at,
        ce.app_installed_at,
        we.widget_enabled_at,
        fr.first_review_at,
        fr.first_aliexpress_review_at,
        fr.first_email_review_at,
        fr.first_import_review_at,
        fr.first_web_review_at,
        fr.total_reviews,
        -- A shop "shows first review" when ALL conditions are met:
        -- 1. App is installed (core extension present)
        -- 2. Widget is enabled (can display reviews)
        -- 3. Has at least one published review
        -- The date is the latest of these three events
        CASE
            WHEN ce.app_installed_at IS NOT NULL
                AND we.widget_enabled_at IS NOT NULL
                AND fr.first_review_at IS NOT NULL
            THEN GREATEST(
                ce.app_installed_at,
                we.widget_enabled_at,
                fr.first_review_at
            )
            ELSE NULL
        END AS first_review_shown_at
    FROM pg.shops s
    LEFT JOIN core_extension_shops ce ON s.id = ce.shop_id
    LEFT JOIN widget_enabled_shops we ON s.id = we.shop_id
    LEFT JOIN first_reviews fr ON s.id = fr.shop_id
    WHERE s.platform = 'shopify'  -- Only Shopify shops
      AND s.plan NOT IN ('cancelled', 'frozen', 'fraudulent')  -- Exclude inactive plans
      AND s.installed = '1'  -- Currently installed shops
),

-- Aggregate by week
weekly_metrics AS (
    SELECT
        DATE_TRUNC('week', first_review_shown_at) AS week,
        COUNT(DISTINCT shop_id) AS shops_showing_first_review_total,

        -- Breakdown by review source (which source provided the first review)
        COUNT(DISTINCT CASE
            WHEN first_review_at = first_aliexpress_review_at
            THEN shop_id
        END) AS shops_first_review_aliexpress,

        COUNT(DISTINCT CASE
            WHEN first_review_at = first_email_review_at
            THEN shop_id
        END) AS shops_first_review_email,

        COUNT(DISTINCT CASE
            WHEN first_review_at = first_import_review_at
            THEN shop_id
        END) AS shops_first_review_import,

        COUNT(DISTINCT CASE
            WHEN first_review_at = first_web_review_at
            THEN shop_id
        END) AS shops_first_review_web,

        -- Breakdown by plan type
        COUNT(DISTINCT CASE WHEN awesome = '1' THEN shop_id END) AS shops_awesome_plan,
        COUNT(DISTINCT CASE WHEN awesome = '0' THEN shop_id END) AS shops_free_plan,

        -- Average reviews per shop
        AVG(total_reviews) AS avg_reviews_per_shop

    FROM shop_milestones
    WHERE first_review_shown_at IS NOT NULL  -- All three conditions must be met
    GROUP BY 1
)

-- Final output with calculated metrics
SELECT
    week,
    shops_showing_first_review_total,
    shops_first_review_aliexpress,
    shops_first_review_email,
    shops_first_review_import,
    shops_first_review_web,
    shops_awesome_plan,
    shops_free_plan,
    ROUND(avg_reviews_per_shop, 2) AS avg_reviews_per_shop,

    -- Calculate percentage breakdowns
    ROUND(100.0 * shops_awesome_plan / NULLIF(shops_showing_first_review_total, 0), 2) AS pct_awesome_plan,
    ROUND(100.0 * shops_free_plan / NULLIF(shops_showing_first_review_total, 0), 2) AS pct_free_plan,

    -- Source percentages
    ROUND(100.0 * shops_first_review_aliexpress / NULLIF(shops_showing_first_review_total, 0), 2) AS pct_first_review_aliexpress,
    ROUND(100.0 * shops_first_review_email / NULLIF(shops_showing_first_review_total, 0), 2) AS pct_first_review_email,
    ROUND(100.0 * shops_first_review_import / NULLIF(shops_showing_first_review_total, 0), 2) AS pct_first_review_import,
    ROUND(100.0 * shops_first_review_web / NULLIF(shops_showing_first_review_total, 0), 2) AS pct_first_review_web

FROM weekly_metrics
CROSS JOIN date_bounds
WHERE week >= start_date
  AND week <= end_date
  AND week IS NOT NULL
ORDER BY week DESC;