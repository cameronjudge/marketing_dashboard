gross_installs_wow = """
select DATE_TRUNC('week', created_at)::date as week_start ,count(distinct shop_id) as gross_installs from pg.extensions where key = 'core' and created_at >= DATE_TRUNC('week', CURRENT_DATE - INTERVAL '52 weeks') and created_at < DATE_TRUNC('week', CURRENT_DATE)
group by week_start
order by week_start desc
"""

gross_installs_mom = """
select DATE_TRUNC('month', created_at)::date as month_start ,count(distinct shop_id) as gross_installs from pg.extensions where key = 'core' and created_at >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '12 months') and created_at < DATE_TRUNC('month', CURRENT_DATE)
group by month_start
order by month_start desc
"""


net_growth_installs_wow = """
select * from dbt.agg__weekly_net_shop_growth
where week_start < DATE_TRUNC('week', CURRENT_DATE)
"""

net_growth_installs_mom = """
select * from dbt.agg__monthly_net_shop_growth
"""

net_growth_awesome_plan_wow = """
select * from dbt.agg__weekly_awesome_growth
where week_start < DATE_TRUNC('week', CURRENT_DATE)
"""

net_growth_awesome_plan_mom = """
select * from dbt.agg__monthly_awesome_growth
"""
