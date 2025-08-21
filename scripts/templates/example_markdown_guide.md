---
guide:
  name: "Quick Start Performance Check"
  category: "Quick Start"
  short_description: "A 5-minute performance health check for your campaigns."
  tags: ["quick start", "performance", "health check"]
  icon: "Zap"
  difficulty_level: "beginner"
  estimated_time_minutes: 5
  is_published: true

queries:
  - title: "Campaign Health Check"
    description: "Quick overview of campaign performance"
    display_order: 1
    query_type: "main_analysis"
    sql_query: |
      SELECT 
          COUNT(DISTINCT campaign_id) as total_campaigns,
          COUNT(DISTINCT user_id) as total_users,
          COUNT(*) as total_events,
          MIN(event_dt) as earliest_data,
          MAX(event_dt) as latest_data
      FROM sponsored_ads_traffic
      WHERE event_dt >= DATE_ADD('day', -{{days}}, CURRENT_DATE)
    parameters_schema:
      days:
        type: "integer"
        default: 7
        description: "Days to look back"
    default_parameters:
      days: 7

metrics:
  - metric_name: "total_campaigns"
    display_name: "Total Campaigns"
    definition: "Number of unique campaigns with activity"
    metric_type: "metric"
  - metric_name: "total_users"
    display_name: "Total Users"
    definition: "Number of unique users exposed to campaigns"
    metric_type: "metric"
  - metric_name: "total_events"
    display_name: "Total Events"
    definition: "Total number of traffic events"
    metric_type: "metric"
---

# Quick Start Performance Check

This guide provides a rapid health check of your campaign performance data.

## What You'll Learn

This 5-minute check will tell you:

- How many campaigns are active
- Your total user reach
- Data freshness and availability

## When to Use This

Perfect for:
- New users getting started
- Weekly performance reviews
- Troubleshooting data issues
- Quick sanity checks

## Next Steps

After running this health check, consider exploring:
- Campaign Performance Overview guide
- ASIN Attribution Analysis guide
- Creative Performance Analysis guide
