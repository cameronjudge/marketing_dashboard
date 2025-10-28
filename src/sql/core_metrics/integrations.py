integrations = """
WITH all_integrations AS (
    -- OAuth-based integrations
    SELECT
        s.id AS shop_id,
        s.awesome,
        oa.name AS integration_name,
        'OAuth' AS integration_source,
        e.created_at AS extension_installed,
        e.deleted_at AS extension_deleted,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.oauth_access_tokens oat
    JOIN pg.oauth_applications oa ON oat.application_id = oa.id
    JOIN pg.shops s ON oat.resource_owner_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE oat.revoked_at IS NULL
        AND s.platform = 'shopify'

    UNION ALL

    -- Coupon-based integrations with proper naming
    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        CASE ac.integration_name
            WHEN 'smile' THEN 'Smile: Rewards & Loyalty'
            WHEN 'lion' THEN 'LoyaltyLion'
            WHEN 'swell' THEN 'Swell - Yotpo Loyalty & Rewards'
            WHEN 'flits' THEN 'Flits: Customer Account Page'
            WHEN 'beans' THEN 'Beans: Loyalty & Rewards'
            WHEN 'ekoma' THEN 'Ekoma'
            ELSE CONCAT('Coupon - ', ac.integration_name)
        END AS integration_name,
        'Coupon Integration' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.assigned_coupons ac
    JOIN pg.shops s ON ac.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE ac.integration_name IS NOT NULL
        AND ac.integration_name != ''
        AND s.platform = 'shopify'

    UNION ALL

    -- Settings-based integrations
    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'AfterShip (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.aftership_api_token IS NOT NULL
        AND st.aftership_api_token != ''
        AND st.aftership_active = '1'
        AND s.platform = 'shopify'

    UNION ALL

    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'Swell (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.swell_api_token IS NOT NULL
        AND st.swell_api_token != ''
        AND s.platform = 'shopify'

    UNION ALL

    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'Beans (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.beans_api_token IS NOT NULL
        AND st.beans_api_token != ''
        AND s.platform = 'shopify'

    UNION ALL

    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'Lion Loyalty (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.lion_loyalty_token IS NOT NULL
        AND st.lion_loyalty_token != ''
        AND s.platform = 'shopify'

    UNION ALL

    -- TikTok Shop integration
    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'TikTok Shop' AS integration_name,
        'Sync Logs' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.tiktok_shop_sync_logs tsl
    JOIN pg.shops s ON tsl.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE s.platform = 'shopify'

    UNION ALL

    -- Webhook-based integrations
    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        CASE
            WHEN w.url LIKE '%zapier%' THEN 'Zapier'
            WHEN w.url LIKE '%klaviyo%' THEN 'Klaviyo (Webhook)'
            WHEN w.url LIKE '%gorgias%' THEN 'Gorgias (Webhook)'
            WHEN w.url LIKE '%omnisend%' THEN 'Omnisend (Webhook)'
            WHEN w.url LIKE '%mailchimp%' THEN 'Mailchimp'
            WHEN w.url LIKE '%hubspot%' THEN 'HubSpot'
            WHEN w.url LIKE '%zendesk%' THEN 'Zendesk'
            WHEN w.url LIKE '%intercom%' THEN 'Intercom'
        END AS integration_name,
        'Webhook' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.webhooks w
    JOIN pg.shops s ON w.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE s.platform = 'shopify'
        AND w.url IS NOT NULL
        AND (w.url LIKE '%zapier%' OR w.url LIKE '%klaviyo%' OR w.url LIKE '%gorgias%'
             OR w.url LIKE '%omnisend%' OR w.url LIKE '%mailchimp%' OR w.url LIKE '%hubspot%'
             OR w.url LIKE '%zendesk%' OR w.url LIKE '%intercom%')
),

-- Aggregate integration metrics
integration_summary AS (
    SELECT
        integration_name,
        integration_source,
        COUNT(DISTINCT shop_id) AS shops,
        COUNT(DISTINCT CASE WHEN awesome = '1' THEN shop_id END) AS awesome_shops,
        COUNT(DISTINCT CASE WHEN extension_deleted IS NULL THEN shop_id END) AS active_shops,
        COUNT(DISTINCT CASE WHEN upgraded_at IS NOT NULL THEN shop_id END) AS upgraded_shops,
        COUNT(DISTINCT CASE WHEN downgraded_at IS NOT NULL THEN shop_id END) AS downgraded_shops,
        COUNT(DISTINCT CASE WHEN extension_deleted IS NOT NULL THEN shop_id END) AS churned_shops,
        ROUND(AVG(lifetime_days), 0) AS avg_lifetime_days,
        ROUND(SUM(CASE WHEN awesome = '1' THEN 15 * lifetime_days / 30.0 ELSE 0 END) /
              NULLIF(COUNT(DISTINCT shop_id), 0), 2) AS avg_ltv
    FROM all_integrations
    GROUP BY integration_name, integration_source
),

-- Enhanced catalog matching with all sources
final_catalog_matching AS (
    SELECT DISTINCT
        i.integration_name,
        i.integration_source,
        i.shops,
        i.awesome_shops,
        i.active_shops,
        i.upgraded_shops,
        i.downgraded_shops,
        i.churned_shops,
        i.avg_lifetime_days,
        i.avg_ltv,
        ROUND(i.awesome_shops::FLOAT / NULLIF(i.shops, 0) * 100, 1) AS awesome_pct,
        ROUND(i.churned_shops::FLOAT / NULLIF(i.shops, 0) * 100, 1) AS churn_pct,
        ROUND(i.upgraded_shops::FLOAT / NULLIF(i.shops, 0) * 100, 1) AS upgrade_rate,
        ROUND(i.downgraded_shops::FLOAT / NULLIF(i.upgraded_shops, 0) * 100, 1) AS downgrade_rate,

        -- Comprehensive tier assignment based on both catalogs and manual mapping
        CASE
            -- Check partner_integrations first (highest priority)
            WHEN MAX(pi.only_awesome) = '1' THEN 'Awesome-Only'
            WHEN MAX(pi.only_awesome) = '0' THEN 'Available-to-All'

            -- Check integration_apps second
            WHEN MAX(ia.awesome) = '1' THEN 'Awesome-Only'
            WHEN MAX(ia.awesome) = '0' THEN 'Available-to-All'

            -- Manual mappings for known variations (from provided data)
            -- Awesome-Only mappings
            WHEN i.integration_name IN (
                'BOGOS', 'Joy Loyalty (Prod)', 'BLOY Loyalty Rewards',
                'Commslayer: AI Helpdesk & Chat', 'Casa', 'Love Loyalty',
                'Redeemly', 'MambaSMS Email &SMS Marketing', 'AfterShip Feed',
                'easyPoints', 'Akohub', 'TikTok Shop',
                -- From integration_apps data
                'AVADA Sales Pop: Trust Badges', 'Gameball: Badges & Rewards',
                'Rebuy Engine', 'Nector: Loyalty and Rewards', 'The Convert Way',
                'BoostCommerce', 'Gratisfaction', 'Recently', 'Searchanise',
                'Fomo', 'Make', 'MR POINT: Customer Points App', 'Wiser AI - Upsell & Cross Sell',
                'Shopney', 'SentimoAI: Sentiment Analysis, Automatic Moderation',
                'ToastiBar', 'SMSBump', 'Contlo', 'MESA', 'Shopify Flow',
                'Pushowl by Brevo', 'Sparq', 'Appstle', 'Rise.ai - Gift Card and Loyalty',
                'Casa Loyalty', 'ProveSource', 'AVADA: SMS, Email Marketing', 'Slack',
                'viaSocket', 'Love Loyalty', 'Redeeemly Store Credit', 'Amplify Loyalty',
                'Google Business Profile', 'TikTok Shop (Beta)', 'Koin Cashback & Store Credit',
                'Shopify store review sync', 'Rivo: Loyalty Program, Rewards', 'Meta',
                'Zapier', 'Smile.io', 'Froonze Loyalty & Wishlist', 'Dollarback - Cashback and Loyalty',
                'Koala App', 'Flash Search', 'Seguno'
            ) THEN 'Awesome-Only'

            -- Available-to-All mappings
            WHEN i.integration_name IN (
                'BON Loyalty', 'PushOwl Prod', 'Marsello', 'Raleon',
                'Outfy - Automated Social Media Management',
                -- From integration_apps data
                'ReConvert - Post Purchase Upsell', 'Also Bought • Recommendations',
                'Frequently Bought Together', 'Personalizer by LimeSpot', 'SEO-Meta Manager',
                'Recomatic Related Products', 'Obviyo', 'Pumper Bundles Quantity Breaks',
                'TinyIMG SEO & Image Optimizer', 'Frankie', 'Avada SEO: Image Optimizer',
                'Schema Plus for SEO', 'Tapita SEO Optimizer & Speed', 'Zipify',
                'Plug in SEO', 'Product Options by Bold', 'Reviewbit', 'Vajro - Mobile App Builder',
                'LayoutHub Easy Page Builder', 'Yotpo Loyalty & Rewards', 'ROASberry MTA & Tracking',
                'Shoelace', 'MBC Bundles', 'Boomerang Bounce Back', 'Shop', 'Tapcart',
                'Espresso Live Metafields', 'Libautech: Sticky Add to Cart', 'Simple Bundles & Kits',
                'BeyondCart Mobile app builder', 'Foxify - Smart Page builder', 'Yoast SEO',
                'Pushowl', 'Amazon', 'Dondy', 'DECO Product Labels and Badges',
                'SEO, JSON-LD, Schema', 'Marsello: Loyalty Program', 'Checkout Promotions & Upsells',
                'iCart', 'Webrex SEO AI Optimizer Schema', 'Qikify Checkout Plus',
                'Veda Landing Page Builder', 'PageFly Advanced Page Builder', 'AMP by Ampify Me',
                'AMP by Shop Sheriff', 'Etsy', 'Aliexpress', 'LEO ‑ Mobile App Builder',
                'X social sharing', 'Amazon review importer', 'Mechanic', 'SEO Booster',
                'Smart SEO', 'Kimonix', 'EasyAccordion', 'GemPages Page Builder & Funnel',
                'Outfy - Automated Social Media Marketing', 'Lantern AI Quiz Builder',
                'QuickReply.ai', 'JSON-LD for SEO', 'LinkShop ‑ Link in Bio Shop',
                'Moast: Shoppable Videos & UGC', 'Daily Deals', 'EasyDisplay: Product Showcase',
                'Loyoly: Loyalty and Retention Platform', 'EasyTabs'
            ) THEN 'Available-to-All'

            -- Settings-based are all Awesome-Only
            WHEN i.integration_source = 'Settings Token' THEN 'Awesome-Only'

            ELSE 'Not Matched'
        END AS tier,

        -- Source information for debugging
        CASE
            WHEN MAX(pi.only_awesome) IS NOT NULL THEN 'Partner Integrations'
            WHEN MAX(ia.awesome) IS NOT NULL THEN 'Integration Apps'
            WHEN i.integration_name IN (
                'BOGOS', 'Joy Loyalty (Prod)', 'BLOY Loyalty Rewards', 'BON Loyalty',
                'PushOwl Prod', 'Marsello', 'Raleon', 'TikTok Shop'
            ) THEN 'Manual Mapping'
            WHEN i.integration_source = 'Settings Token' THEN 'Settings-Based'
            ELSE 'Not Found'
        END AS match_source

    FROM integration_summary i
    LEFT JOIN pg.partner_integrations pi ON
        LOWER(TRIM(i.integration_name)) = LOWER(TRIM(pi.name))
        AND pi.published_at IS NOT NULL
    LEFT JOIN pg.integration_apps ia ON
        LOWER(TRIM(i.integration_name)) = LOWER(TRIM(ia.name))
        AND ia.active = '1'
    GROUP BY
        i.integration_name, i.integration_source, i.shops, i.awesome_shops,
        i.active_shops, i.upgraded_shops, i.downgraded_shops, i.churned_shops,
        i.avg_lifetime_days, i.avg_ltv
)

-- =====================================================
-- 2. MAIN RESULTS: ALL INTEGRATIONS WITH TIER CLASSIFICATION
-- =====================================================

SELECT
    integration_name AS "Integration",
    integration_source AS "Source",
    tier AS "Tier",
    match_source AS "Match From",
    shops AS "Total Shops",
    awesome_shops AS "Awesome",
    active_shops AS "Active",
    upgraded_shops AS "Upgraded",
    downgraded_shops AS "Downgraded",
    awesome_pct AS "Awesome %",
    upgrade_rate AS "Upgrade %",
    downgrade_rate AS "Downgrade %",
    churn_pct AS "Churn %",
    avg_lifetime_days AS "Avg Days",
    avg_ltv AS "Avg LTV"
FROM final_catalog_matching
WHERE shops >= 10
ORDER BY shops DESC
LIMIT 100;



-- =====================================================
-- APP_CONVERT.SQL - INTEGRATION PERFORMANCE VS BENCHMARKS
-- =====================================================
-- Compares integration tier performance against average Judge.me users
-- Shows numerical differences for churn rates, downgrades, and LTV

-- =====================================================
-- 1. BENCHMARK COMPARISON: INTEGRATIONS VS AVERAGE USERS
-- =====================================================
WITH overall_benchmarks AS (
    SELECT
        COUNT(DISTINCT s.id) AS total_shops,
        COUNT(DISTINCT CASE WHEN s.awesome = '1' THEN s.id END) AS awesome_shops,
        COUNT(DISTINCT CASE WHEN s.awesome != '1' OR s.awesome IS NULL THEN s.id END) AS free_shops,

        -- Awesome user benchmarks
        ROUND(COUNT(DISTINCT CASE WHEN s.awesome = '1' AND e.downgraded_at IS NOT NULL THEN s.id END)::FLOAT /
              NULLIF(COUNT(DISTINCT CASE WHEN s.awesome = '1' THEN s.id END), 0) * 100, 2) AS awesome_downgrade_rate,
        ROUND(COUNT(DISTINCT CASE WHEN s.awesome = '1' AND e.deleted_at IS NOT NULL THEN s.id END)::FLOAT /
              NULLIF(COUNT(DISTINCT CASE WHEN s.awesome = '1' THEN s.id END), 0) * 100, 2) AS awesome_churn_rate,
        ROUND(AVG(CASE WHEN s.awesome = '1' THEN DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) END), 0) AS awesome_avg_lifetime,
        ROUND(AVG(CASE WHEN s.awesome = '1' THEN 15 * DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) / 30.0 END), 2) AS awesome_avg_ltv,

        -- Free user benchmarks
        ROUND(COUNT(DISTINCT CASE WHEN (s.awesome != '1' OR s.awesome IS NULL) AND e.deleted_at IS NOT NULL THEN s.id END)::FLOAT /
              NULLIF(COUNT(DISTINCT CASE WHEN s.awesome != '1' OR s.awesome IS NULL THEN s.id END), 0) * 100, 2) AS free_churn_rate,
        ROUND(AVG(CASE WHEN s.awesome != '1' OR s.awesome IS NULL THEN DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) END), 0) AS free_avg_lifetime

    FROM pg.shops s
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30
),

-- =====================================================
-- 2. COLLECT ALL INTEGRATIONS FROM ALL SOURCES
-- =====================================================

all_integrations AS (
    -- OAuth-based integrations
    SELECT
        s.id AS shop_id,
        s.awesome,
        oa.name AS integration_name,
        'OAuth' AS integration_source,
        e.created_at AS extension_installed,
        e.deleted_at AS extension_deleted,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.oauth_access_tokens oat
    JOIN pg.oauth_applications oa ON oat.application_id = oa.id
    JOIN pg.shops s ON oat.resource_owner_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE oat.revoked_at IS NULL
        AND s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30

    UNION ALL

    -- Coupon-based integrations
    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        CASE ac.integration_name
            WHEN 'smile' THEN 'Smile: Rewards & Loyalty'
            WHEN 'flits' THEN 'Flits: Customer Account Page'
            WHEN 'lion' THEN 'LoyaltyLion'
            WHEN 'swell' THEN 'Swell - Yotpo Loyalty & Rewards'
            WHEN 'beans' THEN 'Beans: Loyalty & Rewards'
            WHEN 'ekoma' THEN 'Ekoma'
            ELSE CONCAT('Coupon - ', ac.integration_name)
        END AS integration_name,
        'Coupon Integration' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.assigned_coupons ac
    JOIN pg.shops s ON ac.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE ac.integration_name IN ('smile', 'flits', 'lion', 'swell', 'beans', 'ekoma')
        AND s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30

    UNION ALL

    -- TikTok Shop integration
    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'TikTok Shop' AS integration_name,
        'Sync Logs' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.tiktok_shop_sync_logs tsl
    JOIN pg.shops s ON tsl.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30

    UNION ALL

    -- Settings-based integrations
    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'AfterShip (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.aftership_api_token IS NOT NULL
        AND st.aftership_api_token != ''
        AND st.aftership_active = '1'
        AND s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30

    UNION ALL

    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'Swell (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.swell_api_token IS NOT NULL
        AND st.swell_api_token != ''
        AND s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30

    UNION ALL

    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'Beans (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.beans_api_token IS NOT NULL
        AND st.beans_api_token != ''
        AND s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30

    UNION ALL

    SELECT DISTINCT
        s.id AS shop_id,
        s.awesome,
        'Lion Loyalty (Settings)' AS integration_name,
        'Settings Token' AS integration_source,
        e.created_at,
        e.deleted_at,
        e.upgraded_at,
        e.downgraded_at,
        DATEDIFF(day, e.created_at, COALESCE(e.deleted_at, CURRENT_DATE)) AS lifetime_days
    FROM pg.settings st
    JOIN pg.shops s ON st.shop_id = s.id
    JOIN pg.extensions e ON s.id = e.shop_id AND e.key = 'core'
    WHERE st.lion_loyalty_token IS NOT NULL
        AND st.lion_loyalty_token != ''
        AND s.platform = 'shopify'
        AND e.created_at >= '2023-01-01'
        AND e.created_at < CURRENT_DATE - 30
),

-- =====================================================
-- 3. CALCULATE METRICS FOR EACH INTEGRATION
-- =====================================================

integration_performance AS (
    SELECT
        ai.integration_name,
        ai.integration_source,

        -- Determine tier based on catalog mappings
        CASE
            WHEN ai.integration_name IN ('Smile: Rewards & Loyalty', 'Gorgias', 'Tidio', 'Customer Accounts Concierge',
                            'Flits: Customer Account Page', 'Joy Loyalty (Prod)', 'BLOY Loyalty Rewards',
                            'Commslayer: AI Helpdesk & Chat', 'BOGOS', 'Casa', 'Love Loyalty', 'Redeemly',
                            'AfterShip Feed', 'AfterShip (Settings)', 'easyPoints', 'Akohub', 'Kangaroo Rewards',
                            'MESA', 'ToastiBar - Sales Popup', 'Beans', 'Beans: Loyalty & Rewards', 'Beans (Settings)',
                            'TikTok Shop', 'LoyaltyLion', 'Lion Loyalty (Settings)',
                            'Swell - Yotpo Loyalty & Rewards', 'Swell (Settings)')
                OR ai.integration_name LIKE '%Swell%' OR ai.integration_name LIKE '%Lion%'
            THEN 'Awesome-Only'
            WHEN ai.integration_name IN ('BON Loyalty', 'PushOwl Prod', 'Marsello', 'Raleon',
                            'Outfy - Automated Social Media Management')
            THEN 'Available-to-All'
            ELSE 'Unknown'
        END AS tier,

        COUNT(DISTINCT ai.shop_id) AS total_shops,
        COUNT(DISTINCT CASE WHEN ai.awesome = '1' THEN ai.shop_id END) AS awesome_shops,
        COUNT(DISTINCT CASE WHEN ai.awesome != '1' OR ai.awesome IS NULL THEN ai.shop_id END) AS free_shops,

        -- Awesome user metrics
        ROUND(COUNT(DISTINCT CASE WHEN ai.awesome = '1' AND ai.downgraded_at IS NOT NULL THEN ai.shop_id END)::FLOAT /
              NULLIF(COUNT(DISTINCT CASE WHEN ai.awesome = '1' THEN ai.shop_id END), 0) * 100, 1) AS awesome_downgrade_rate,
        ROUND(COUNT(DISTINCT CASE WHEN ai.awesome = '1' AND ai.extension_deleted IS NOT NULL THEN ai.shop_id END)::FLOAT /
              NULLIF(COUNT(DISTINCT CASE WHEN ai.awesome = '1' THEN ai.shop_id END), 0) * 100, 1) AS awesome_churn_rate,
        ROUND(AVG(CASE WHEN ai.awesome = '1' THEN ai.lifetime_days END), 0) AS awesome_avg_lifetime,
        ROUND(SUM(CASE WHEN ai.awesome = '1' THEN 15 * ai.lifetime_days / 30.0 END) /
              NULLIF(COUNT(DISTINCT CASE WHEN ai.awesome = '1' THEN ai.shop_id END), 0), 0) AS awesome_ltv,

        -- Free user metrics
        ROUND(COUNT(DISTINCT CASE WHEN (ai.awesome != '1' OR ai.awesome IS NULL) AND ai.extension_deleted IS NOT NULL THEN ai.shop_id END)::FLOAT /
              NULLIF(COUNT(DISTINCT CASE WHEN ai.awesome != '1' OR ai.awesome IS NULL THEN ai.shop_id END), 0) * 100, 1) AS free_churn_rate,
        ROUND(AVG(CASE WHEN ai.awesome != '1' OR ai.awesome IS NULL THEN ai.lifetime_days END), 0) AS free_avg_lifetime,

        -- Overall conversion rate
        ROUND(COUNT(DISTINCT CASE WHEN ai.awesome = '1' THEN ai.shop_id END)::FLOAT /
              NULLIF(COUNT(DISTINCT ai.shop_id), 0) * 100, 1) AS awesome_conversion_rate

    FROM all_integrations ai
    GROUP BY ai.integration_name, ai.integration_source
    HAVING COUNT(DISTINCT ai.shop_id) >= 20  -- Minimum threshold for statistical relevance
)

-- =====================================================
-- 4. MAIN OUTPUT: EACH INTEGRATION VS BENCHMARKS
-- =====================================================

SELECT
    ip.integration_name AS "Integration",
    ip.tier AS "Tier",
    ip.total_shops AS "Total Shops",
    ip.awesome_shops AS "Awesome",
    ip.free_shops AS "Free",

    '--- AWESOME METRICS ---' AS "___",

    -- Downgrade comparison
    ip.awesome_downgrade_rate || '%' AS "Downgrade %",
    b.awesome_downgrade_rate || '%' AS "Benchmark",
    CASE
        WHEN ip.awesome_downgrade_rate IS NULL THEN 'N/A'
        WHEN ip.awesome_downgrade_rate < b.awesome_downgrade_rate
        THEN '↑ ' || ROUND(b.awesome_downgrade_rate - ip.awesome_downgrade_rate, 1) || 'pp better'
        ELSE '↓ ' || ROUND(ip.awesome_downgrade_rate - b.awesome_downgrade_rate, 1) || 'pp worse'
    END AS "vs Avg",

    -- Churn comparison
    ip.awesome_churn_rate || '%' AS "Churn %",
    b.awesome_churn_rate || '%' AS "Benchmark ",
    CASE
        WHEN ip.awesome_churn_rate IS NULL THEN 'N/A'
        WHEN ip.awesome_churn_rate < b.awesome_churn_rate
        THEN '↑ ' || ROUND(b.awesome_churn_rate - ip.awesome_churn_rate, 1) || 'pp better'
        ELSE '↓ ' || ROUND(ip.awesome_churn_rate - b.awesome_churn_rate, 1) || 'pp worse'
    END AS "vs Avg ",

    -- LTV comparison
    '$' || ip.awesome_ltv AS "LTV",
    '$' || ROUND(b.awesome_avg_ltv, 0) AS "Benchmark  ",
    CASE
        WHEN ip.awesome_ltv IS NULL THEN 'N/A'
        WHEN ip.awesome_ltv > b.awesome_avg_ltv
        THEN '+$' || ROUND(ip.awesome_ltv - b.awesome_avg_ltv, 0)
        ELSE '-$' || ROUND(b.awesome_avg_ltv - ip.awesome_ltv, 0)
    END AS "vs Avg  ",

    -- Lifetime comparison
    ip.awesome_avg_lifetime || ' days' AS "Lifetime",
    b.awesome_avg_lifetime || ' days' AS "Benchmark   ",
    CASE
        WHEN ip.awesome_avg_lifetime IS NULL THEN 'N/A'
        WHEN ip.awesome_avg_lifetime > b.awesome_avg_lifetime
        THEN '+' || ROUND(ip.awesome_avg_lifetime - b.awesome_avg_lifetime, 0) || ' days'
        ELSE ROUND(ip.awesome_avg_lifetime - b.awesome_avg_lifetime, 0) || ' days'
    END AS "vs Avg   ",

    '--- FREE METRICS ---' AS "____",

    -- Free churn comparison
    ip.free_churn_rate || '%' AS "Free Churn %",
    b.free_churn_rate || '%' AS "Benchmark    ",
    CASE
        WHEN ip.free_churn_rate IS NULL THEN 'N/A'
        WHEN ip.free_churn_rate < b.free_churn_rate
        THEN '↑ ' || ROUND(b.free_churn_rate - ip.free_churn_rate, 1) || 'pp better'
        ELSE '↓ ' || ROUND(ip.free_churn_rate - b.free_churn_rate, 1) || 'pp worse'
    END AS "vs Avg    ",

    -- Conversion rate
    ip.awesome_conversion_rate || '%' AS "Awesome Conv %"

FROM integration_performance ip
CROSS JOIN overall_benchmarks b
ORDER BY
    CASE ip.tier
        WHEN 'Awesome-Only' THEN 1
        WHEN 'Available-to-All' THEN 2
        ELSE 3
    END,
    ip.total_shops DESC;


"""