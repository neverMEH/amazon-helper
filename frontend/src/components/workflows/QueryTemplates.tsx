import { TrendingUp, Users, ShoppingCart, BarChart } from 'lucide-react';

export interface QueryTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: any;
  sqlTemplate: string;
  requiredParameters: string[];
  tags: string[];
}

export const queryTemplates: QueryTemplate[] = [
  {
    id: 'dsp-campaign-performance',
    name: 'DSP Campaign Performance',
    description: 'Analyze DSP campaign metrics including impressions, clicks, and conversions',
    category: 'DSP',
    icon: TrendingUp,
    sqlTemplate: `-- DSP Campaign Performance Analysis
SELECT 
    campaign_id,
    campaign_name,
    advertiser_id,
    COUNT(DISTINCT user_id) as unique_reach,
    COUNT(*) as total_impressions,
    SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as total_clicks,
    SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) as total_conversions,
    ROUND(SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as ctr_percent,
    ROUND(SUM(CASE WHEN event_type = 'conversion' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as cvr_percent
FROM dsp_impressions
WHERE impression_dt >= '{{start_date}}' 
  AND impression_dt <= '{{end_date}}'
GROUP BY campaign_id, campaign_name, advertiser_id
HAVING COUNT(DISTINCT user_id) >= 10  -- AMC privacy threshold
ORDER BY total_impressions DESC`,
    requiredParameters: ['start_date', 'end_date'],
    tags: ['dsp', 'campaign', 'performance']
  },
  {
    id: 'sponsored-ads-performance',
    name: 'Sponsored Ads Performance by Type',
    description: 'Compare performance across Sponsored Products, Brands, and Display',
    category: 'Sponsored Ads',
    icon: BarChart,
    sqlTemplate: `-- Sponsored Ads Performance by Ad Type
SELECT 
    campaign_id,
    campaign_name,
    ad_type,
    COUNT(DISTINCT user_id) as unique_reach,
    COUNT(*) as impressions,
    SUM(clicks) as total_clicks,
    COUNT(DISTINCT asin) as unique_products,
    ROUND(SUM(clicks) * 100.0 / COUNT(*), 2) as ctr_percent
FROM (
    -- Sponsored Products
    SELECT 
        campaign_id, campaign_name, 'SP' as ad_type,
        user_id, asin, 0 as clicks
    FROM sponsored_ads_impressions
    WHERE ad_type = 'SP' AND impression_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
    
    UNION ALL
    
    SELECT 
        campaign_id, campaign_name, 'SP' as ad_type,
        user_id, asin, 1 as clicks
    FROM sponsored_ads_clicks
    WHERE ad_type = 'SP' AND click_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
    
    UNION ALL
    
    -- Sponsored Brands
    SELECT 
        campaign_id, campaign_name, 'SB' as ad_type,
        user_id, NULL as asin, 0 as clicks
    FROM sb_impressions
    WHERE impression_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
    
    UNION ALL
    
    -- Sponsored Display
    SELECT 
        campaign_id, campaign_name, 'SD' as ad_type,
        user_id, asin, 0 as clicks
    FROM sd_impressions
    WHERE impression_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
)
GROUP BY campaign_id, campaign_name, ad_type
HAVING COUNT(DISTINCT user_id) >= 10
ORDER BY ad_type, impressions DESC`,
    requiredParameters: ['start_date', 'end_date'],
    tags: ['sponsored-ads', 'comparison', 'performance']
  },
  {
    id: 'customer-journey-analysis',
    name: 'Customer Journey Analysis',
    description: 'Track customer touchpoints across DSP and Sponsored Ads',
    category: 'Attribution',
    icon: Users,
    sqlTemplate: `-- Customer Journey Analysis
WITH user_touchpoints AS (
    -- DSP touchpoints
    SELECT 
        user_id,
        'DSP' as channel,
        campaign_id,
        impression_dt as touchpoint_dt,
        'impression' as event_type
    FROM dsp_impressions
    WHERE impression_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
    
    UNION ALL
    
    SELECT 
        user_id,
        'DSP' as channel,
        campaign_id,
        click_dt as touchpoint_dt,
        'click' as event_type
    FROM dsp_clicks
    WHERE click_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
    
    UNION ALL
    
    -- Sponsored Ads touchpoints
    SELECT 
        user_id,
        CONCAT('Sponsored ', ad_type) as channel,
        campaign_id,
        impression_dt as touchpoint_dt,
        'impression' as event_type
    FROM sponsored_ads_impressions
    WHERE impression_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
),
user_journey_summary AS (
    SELECT 
        user_id,
        COUNT(DISTINCT channel) as channels_touched,
        COUNT(*) as total_touchpoints,
        MIN(touchpoint_dt) as first_touch,
        MAX(touchpoint_dt) as last_touch,
        DATEDIFF('day', MIN(touchpoint_dt), MAX(touchpoint_dt)) as journey_days
    FROM user_touchpoints
    GROUP BY user_id
)
SELECT 
    channels_touched,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(total_touchpoints) as avg_touchpoints,
    AVG(journey_days) as avg_journey_days
FROM user_journey_summary
GROUP BY channels_touched
HAVING COUNT(DISTINCT user_id) >= 10
ORDER BY channels_touched`,
    requiredParameters: ['start_date', 'end_date'],
    tags: ['attribution', 'journey', 'cross-channel']
  },
  {
    id: 'conversion-path-analysis',
    name: 'Conversion Path Analysis',
    description: 'Analyze paths to conversion with attribution insights',
    category: 'Attribution',
    icon: ShoppingCart,
    sqlTemplate: `-- Conversion Path Analysis
WITH conversions AS (
    SELECT 
        user_id,
        conversion_dt,
        conversion_value
    FROM conversions
    WHERE conversion_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
),
pre_conversion_touches AS (
    -- DSP touches before conversion
    SELECT 
        c.user_id,
        c.conversion_dt,
        'DSP' as channel,
        di.campaign_id,
        di.impression_dt as touch_dt,
        DATEDIFF('hour', di.impression_dt, c.conversion_dt) as hours_to_conversion
    FROM conversions c
    JOIN dsp_impressions di ON c.user_id = di.user_id
    WHERE di.impression_dt < c.conversion_dt
      AND di.impression_dt >= DATEADD('day', -{{lookback_days}}, c.conversion_dt)
    
    UNION ALL
    
    -- Sponsored Ads touches before conversion
    SELECT 
        c.user_id,
        c.conversion_dt,
        CONCAT('Sponsored ', sa.ad_type) as channel,
        sa.campaign_id,
        sa.impression_dt as touch_dt,
        DATEDIFF('hour', sa.impression_dt, c.conversion_dt) as hours_to_conversion
    FROM conversions c
    JOIN sponsored_ads_impressions sa ON c.user_id = sa.user_id
    WHERE sa.impression_dt < c.conversion_dt
      AND sa.impression_dt >= DATEADD('day', -{{lookback_days}}, c.conversion_dt)
)
SELECT 
    channel,
    COUNT(DISTINCT user_id) as converting_users,
    COUNT(*) as total_touches,
    AVG(hours_to_conversion) as avg_hours_to_conversion,
    COUNT(DISTINCT campaign_id) as campaigns_involved
FROM pre_conversion_touches
GROUP BY channel
HAVING COUNT(DISTINCT user_id) >= 10
ORDER BY converting_users DESC`,
    requiredParameters: ['start_date', 'end_date', 'lookback_days'],
    tags: ['conversion', 'attribution', 'path-analysis']
  },
  {
    id: 'campaign-overlap-analysis',
    name: 'Campaign Audience Overlap',
    description: 'Find audience overlap between campaigns',
    category: 'Audience',
    icon: Users,
    sqlTemplate: `-- Campaign Audience Overlap Analysis
WITH campaign_users AS (
    SELECT DISTINCT
        campaign_id,
        campaign_name,
        user_id
    FROM dsp_impressions
    WHERE impression_dt BETWEEN '{{start_date}}' AND '{{end_date}}'
      AND campaign_id IN ({{campaign_ids}})  -- Comma-separated campaign IDs
)
SELECT 
    c1.campaign_name as campaign_1,
    c2.campaign_name as campaign_2,
    COUNT(DISTINCT c1.user_id) as campaign_1_users,
    COUNT(DISTINCT c2.user_id) as campaign_2_users,
    COUNT(DISTINCT CASE WHEN c1.user_id = c2.user_id THEN c1.user_id END) as overlap_users,
    ROUND(
        COUNT(DISTINCT CASE WHEN c1.user_id = c2.user_id THEN c1.user_id END) * 100.0 / 
        COUNT(DISTINCT c1.user_id), 
        2
    ) as overlap_percent
FROM campaign_users c1
CROSS JOIN campaign_users c2
WHERE c1.campaign_id < c2.campaign_id  -- Avoid duplicates
GROUP BY c1.campaign_name, c2.campaign_name
HAVING COUNT(DISTINCT CASE WHEN c1.user_id = c2.user_id THEN c1.user_id END) >= 10
ORDER BY overlap_users DESC`,
    requiredParameters: ['start_date', 'end_date', 'campaign_ids'],
    tags: ['audience', 'overlap', 'campaign-analysis']
  }
];

interface QueryTemplatesProps {
  onSelectTemplate: (template: QueryTemplate) => void;
}

export default function QueryTemplates({ onSelectTemplate }: QueryTemplatesProps) {
  const categories = [...new Set(queryTemplates.map(t => t.category))];

  return (
    <div className="p-4">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Query Templates</h3>
      <p className="text-sm text-gray-600 mb-6">
        Start with a pre-built AMC query template and customize it for your needs
      </p>

      {categories.map(category => (
        <div key={category} className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">{category}</h4>
          <div className="grid grid-cols-1 gap-3">
            {queryTemplates
              .filter(t => t.category === category)
              .map(template => {
                const Icon = template.icon;
                return (
                  <button
                    key={template.id}
                    onClick={() => onSelectTemplate(template)}
                    className="text-left p-4 border border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-colors"
                  >
                    <div className="flex items-start">
                      <Icon className="h-5 w-5 text-indigo-600 mt-0.5 mr-3 flex-shrink-0" />
                      <div className="flex-1">
                        <h5 className="text-sm font-medium text-gray-900">
                          {template.name}
                        </h5>
                        <p className="text-sm text-gray-600 mt-1">
                          {template.description}
                        </p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {template.tags.map(tag => (
                            <span
                              key={tag}
                              className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
          </div>
        </div>
      ))}
    </div>
  );
}