#updated to core metrics
trial_categories_categories = """
select * from dbt.agg_weekly_trial_campaign_metrics
where week < DATE_TRUNC('week', CURRENT_DATE)
and week >= DATE_TRUNC('week', CURRENT_DATE - INTERVAL '12 weeks')
"""