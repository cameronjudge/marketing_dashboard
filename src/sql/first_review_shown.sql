-- download dates of shops

WITH core_extension_shops AS (
	select shop_id
	, min(created_at)
	from pg.extensions
	where key = 'core'
	group by 1
),

-- first widget enabled
first_widget_enabled as (
    SELECT
        sl.shop_id,
        MIN(sl.created_at) AS widget_enabled_at
    FROM pg.setting_logs sl
    WHERE sl.key IN ('review_widget_enabled', 'shopify_core_embed_block_enabled')
      AND sl.new_value = 'true'
     AND date(created_at) >= DATEADD(YEAR, -1, CURRENT_DATE)
    GROUP BY sl.shop_id
    UNION ALL
    SELECT
        s.shop_id,
        e.created_at AS widget_enabled_at
    FROM pg.settings s
    INNER JOIN pg.extensions e ON s.shop_id = e.shop_id
    INNER JOIN dbt.installed_widgets_by_shops iw ON s.shop_id = iw.shop_id
    WHERE s.auto_install_widget = '1'
      AND e.key = 'core'
      AND iw.installed_widgets_count > 0
      -- Exclude shops already captured in setting_logs
      AND s.shop_id NOT IN (
          SELECT DISTINCT shop_id
          FROM pg.setting_logs
          WHERE key IN ('review_widget_enabled', 'shopify_core_embed_block_enabled')
            AND new_value = 'true')
    AND date(e.created_at) >= DATEADD(YEAR, -1, CURRENT_DATE)
),

-- first review date
first_review as (
	select
		shop_id
		, min(made_at) as first_review_date
	from pg.reviews
	where curated = 'ok' AND hidden = 0
	AND date(made_at) >= DATEADD(YEAR, -1, CURRENT_DATE)
	group by 1
)

select

;