google_analytics_query = """
WITH date_filter AS (
  SELECT 
    -- Get the start of the current week (Monday)
    DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)) AS current_week_start,
    -- Get 52 weeks ago from the start of last completed week
    DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)), INTERVAL 53 WEEK) AS start_date,
    -- Last day of the previous completed week (Sunday)
    DATE_SUB(DATE_TRUNC(CURRENT_DATE(), WEEK(MONDAY)), INTERVAL 1 DAY) AS last_completed_day
),

page_locations AS (
  SELECT 
    event_date,
    event_timestamp,
    user_pseudo_id,
    (SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'page_location') AS page_location
  FROM 
    `review-site-307404.analytics_476622290.events_*`,
    date_filter
  WHERE 
    event_name = 'add_to_cart'
    AND PARSE_DATE('%Y%m%d', event_date) >= date_filter.start_date
    AND PARSE_DATE('%Y%m%d', event_date) <= date_filter.last_completed_day
),

parsed_params AS (
  SELECT 
    event_date,
    event_timestamp,
    user_pseudo_id,
    page_location,
    REGEXP_EXTRACT(page_location, r'st_source=([^&]+)') AS st_source_parsed,
    REGEXP_EXTRACT(page_location, r'surface_type=([^&]+)') AS surface_type_parsed,
    REGEXP_EXTRACT(page_location, r'surface_detail=([^&]+)') AS surface_detail_parsed,
    REGEXP_EXTRACT(page_location, r'st_campaign=([^&]+)') AS st_campaign_parsed,
    REGEXP_EXTRACT(page_location, r'utm_campaign=([^&]+)') AS utm_campaign_parsed,
    REGEXP_EXTRACT(page_location, r'utm_medium=([^&]+)') AS utm_medium_parsed,
    REGEXP_EXTRACT(page_location, r'utm_source=([^&]+)') AS utm_source_parsed
  FROM 
    page_locations
),

aggregated_fields AS (
  SELECT 
    *,
    
    -- Medium (Aggregated)
    CASE 
      WHEN LOWER(IFNULL(surface_type_parsed, "")) = "search_ad" THEN "paid_search"
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(utm_medium_parsed, "")), r".*website.*") THEN "website"
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(utm_source_parsed, "")), r".*aeri.*") THEN "app-cross-sell"
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(utm_medium_parsed, "")), r".*partner.*") THEN "partner"
      WHEN LOWER(IFNULL(st_campaign_parsed, "")) = "admin-search" 
        OR LOWER(IFNULL(st_source_parsed, "")) = "autocomplete" 
        OR LOWER(IFNULL(surface_type_parsed, "")) = "search" THEN "organic_search"
      WHEN LOWER(IFNULL(st_source_parsed, "")) = "admin-web" 
        AND LOWER(IFNULL(st_campaign_parsed, "")) != "admin-search" THEN "organic_placement"
      WHEN LOWER(IFNULL(st_source_parsed, "")) = "admin" 
        AND LOWER(IFNULL(st_campaign_parsed, "")) != "admin-search" THEN "organic_placement"
      WHEN LOWER(IFNULL(st_source_parsed, "")) = "admin-mobile-web" 
        AND LOWER(IFNULL(st_campaign_parsed, "")) != "admin-search" THEN "organic_placement"
      WHEN LOWER(IFNULL(st_source_parsed, "")) = "admin-mobile-app" 
        AND LOWER(IFNULL(st_campaign_parsed, "")) != "admin-search" THEN "organic_placement"
      WHEN LOWER(IFNULL(st_source_parsed, "")) = "sidekick" THEN "organic_placement"
      WHEN LOWER(IFNULL(surface_type_parsed, "")) IN ("home","category","navbar","story","app_group",
        "app_details_page","partners","app_details","guided_search","app_comparison") THEN "organic_placement"
      ELSE "organic_uncategorised"
    END AS medium_aggregated,
    
    -- Source (Aggregated)
    CASE 
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(st_source_parsed, '')), r'.+') 
        OR REGEXP_CONTAINS(LOWER(IFNULL(surface_type_parsed, '')), r'.+') 
        OR REGEXP_CONTAINS(LOWER(IFNULL(surface_detail_parsed, '')), r'.+') THEN 'shopify'
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(utm_medium_parsed, '')), r'^shopify$') THEN 'shopify'
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(utm_medium_parsed, '')), r'^website$') THEN 'judgeme'
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(utm_medium_parsed, '')), r'^partner$') 
        THEN LOWER(IFNULL(utm_source_parsed, 'partner'))
      WHEN REGEXP_CONTAINS(LOWER(IFNULL(utm_source_parsed, '')), r'^aeri$') THEN 'aeri'
      WHEN NOT REGEXP_CONTAINS(LOWER(IFNULL(utm_source_parsed, '')), r'.+') 
        AND NOT REGEXP_CONTAINS(LOWER(IFNULL(utm_medium_parsed, '')), r'.+') 
        AND NOT REGEXP_CONTAINS(LOWER(IFNULL(st_source_parsed, '')), r'.+') 
        AND NOT REGEXP_CONTAINS(LOWER(IFNULL(surface_type_parsed, '')), r'.+') 
        AND NOT REGEXP_CONTAINS(LOWER(IFNULL(surface_detail_parsed, '')), r'.+') THEN 'direct'
      ELSE LOWER(IFNULL(utm_source_parsed, '(unknown)'))
    END AS source_aggregated,
    
    -- Campaign (Aggregated)
    CASE 
      WHEN LOWER(IFNULL(surface_type_parsed, '')) IN ('search','search_ad','search ad') 
        THEN surface_type_parsed
      WHEN LOWER(IFNULL(utm_medium_parsed, '')) IN ('website','shopify') 
        THEN utm_source_parsed
      WHEN LOWER(IFNULL(utm_source_parsed, '')) = 'shopify' 
        THEN st_source_parsed
      WHEN LOWER(IFNULL(st_source_parsed, '')) NOT IN ('','null') 
        THEN st_source_parsed
      WHEN (LOWER(IFNULL(surface_type_parsed, '')) != 'null' 
        AND LOWER(IFNULL(st_source_parsed, '')) IN ('','null')) 
        THEN surface_type_parsed
      ELSE ''
    END AS campaign_aggregated,
    
    -- Campaign-details (Aggregated)
    CASE 
      WHEN LOWER(IFNULL(surface_detail_parsed, "")) NOT IN ("","null") 
        THEN surface_detail_parsed
      WHEN LOWER(IFNULL(st_campaign_parsed, "")) NOT IN ("","null") 
        THEN st_campaign_parsed
      ELSE ""
    END AS campaign_details_aggregated
    
  FROM 
    parsed_params
)

SELECT 
  count(*) as events_count,
  event_date,
  st_source_parsed,
  surface_type_parsed,
  surface_detail_parsed,
  st_campaign_parsed,
  utm_campaign_parsed,
  utm_medium_parsed,
  utm_source_parsed,
  medium_aggregated,
  source_aggregated,
  campaign_aggregated,
  campaign_details_aggregated
FROM 
  aggregated_fields

  group by 2,3,4,5,6,7,8,9,10,11,12,13

"""