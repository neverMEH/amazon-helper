export interface SchemaField {
  name: string;
  type: string;
  description?: string;
  icon?: string;
}

export interface SchemaTable {
  name: string;
  category: string;
  description?: string;
  fields: SchemaField[];
}

export const AMC_SCHEMA: Record<string, SchemaTable> = {
  // Campaign Data Tables
  'amazon_attributed_events': {
    name: 'amazon_attributed_events',
    category: 'Campaign Data',
    description: 'Attribution events from Amazon Advertising campaigns',
    fields: [
      { name: 'event_dt', type: 'date', description: 'Event date', icon: 'calendar' },
      { name: 'user_id', type: 'string', description: 'Unique user identifier', icon: 'user' },
      { name: 'campaign_id', type: 'bigint', description: 'Campaign identifier', icon: 'hash' },
      { name: 'ad_group_id', type: 'bigint', description: 'Ad group identifier', icon: 'folder' },
      { name: 'creative_id', type: 'bigint', description: 'Creative identifier', icon: 'image' },
      { name: 'event_type', type: 'string', description: 'Type of event (impression, click, conversion)', icon: 'activity' },
      { name: 'conversion_value', type: 'decimal', description: 'Value of conversion', icon: 'dollar-sign' },
      { name: 'attributed_units', type: 'integer', description: 'Number of units attributed', icon: 'package' }
    ]
  },
  'dsp_impressions': {
    name: 'dsp_impressions',
    category: 'Campaign Data',
    description: 'Display advertising impressions data',
    fields: [
      { name: 'impression_dt', type: 'timestamp', description: 'Impression timestamp', icon: 'clock' },
      { name: 'user_id', type: 'string', description: 'User identifier', icon: 'user' },
      { name: 'campaign_id', type: 'string', description: 'DSP campaign ID', icon: 'hash' },
      { name: 'creative_id', type: 'string', description: 'Creative ID', icon: 'image' },
      { name: 'placement_id', type: 'string', description: 'Placement ID', icon: 'layout' },
      { name: 'impression_cost', type: 'decimal', description: 'Cost of impression', icon: 'dollar-sign' },
      { name: 'device_type', type: 'string', description: 'Device type', icon: 'smartphone' },
      { name: 'browser', type: 'string', description: 'Browser type', icon: 'globe' }
    ]
  },
  'dsp_clicks': {
    name: 'dsp_clicks',
    category: 'Campaign Data',
    description: 'Display advertising click data',
    fields: [
      { name: 'click_dt', type: 'timestamp', description: 'Click timestamp', icon: 'clock' },
      { name: 'user_id', type: 'string', description: 'User identifier', icon: 'user' },
      { name: 'campaign_id', type: 'string', description: 'DSP campaign ID', icon: 'hash' },
      { name: 'creative_id', type: 'string', description: 'Creative ID', icon: 'image' },
      { name: 'click_cost', type: 'decimal', description: 'Cost of click', icon: 'dollar-sign' },
      { name: 'landing_page', type: 'string', description: 'Landing page URL', icon: 'link' }
    ]
  },
  'sponsored_ads_traffic': {
    name: 'sponsored_ads_traffic',
    category: 'Campaign Data',
    description: 'Sponsored Products, Brands, and Display traffic data',
    fields: [
      { name: 'event_dt', type: 'date', description: 'Event date', icon: 'calendar' },
      { name: 'campaign_id', type: 'bigint', description: 'Campaign ID', icon: 'hash' },
      { name: 'campaign_name', type: 'string', description: 'Campaign name', icon: 'tag' },
      { name: 'ad_type', type: 'string', description: 'SP, SB, or SD', icon: 'type' },
      { name: 'impressions', type: 'bigint', description: 'Number of impressions', icon: 'eye' },
      { name: 'clicks', type: 'bigint', description: 'Number of clicks', icon: 'mouse-pointer' },
      { name: 'spend', type: 'decimal', description: 'Ad spend', icon: 'dollar-sign' },
      { name: 'conversions', type: 'bigint', description: 'Number of conversions', icon: 'trending-up' },
      { name: 'sales', type: 'decimal', description: 'Attributed sales', icon: 'shopping-cart' }
    ]
  },

  // Product Data Tables
  'product_views': {
    name: 'product_views',
    category: 'Product Data',
    description: 'Product detail page views',
    fields: [
      { name: 'view_dt', type: 'timestamp', description: 'View timestamp', icon: 'clock' },
      { name: 'user_id', type: 'string', description: 'User identifier', icon: 'user' },
      { name: 'asin', type: 'string', description: 'Product ASIN', icon: 'package' },
      { name: 'marketplace_id', type: 'string', description: 'Marketplace ID', icon: 'globe' },
      { name: 'session_id', type: 'string', description: 'Session identifier', icon: 'key' },
      { name: 'referrer', type: 'string', description: 'Referrer URL', icon: 'link' },
      { name: 'is_prime', type: 'boolean', description: 'Prime member flag', icon: 'star' }
    ]
  },
  'cart_additions': {
    name: 'cart_additions',
    category: 'Product Data',
    description: 'Products added to cart',
    fields: [
      { name: 'add_dt', type: 'timestamp', description: 'Addition timestamp', icon: 'clock' },
      { name: 'user_id', type: 'string', description: 'User identifier', icon: 'user' },
      { name: 'asin', type: 'string', description: 'Product ASIN', icon: 'package' },
      { name: 'quantity', type: 'integer', description: 'Quantity added', icon: 'hash' },
      { name: 'price', type: 'decimal', description: 'Product price', icon: 'dollar-sign' },
      { name: 'session_id', type: 'string', description: 'Session identifier', icon: 'key' }
    ]
  },
  'purchases': {
    name: 'purchases',
    category: 'Product Data',
    description: 'Completed purchases',
    fields: [
      { name: 'purchase_dt', type: 'timestamp', description: 'Purchase timestamp', icon: 'clock' },
      { name: 'user_id', type: 'string', description: 'User identifier', icon: 'user' },
      { name: 'order_id', type: 'string', description: 'Order identifier', icon: 'file-text' },
      { name: 'asin', type: 'string', description: 'Product ASIN', icon: 'package' },
      { name: 'quantity', type: 'integer', description: 'Quantity purchased', icon: 'hash' },
      { name: 'revenue', type: 'decimal', description: 'Purchase revenue', icon: 'dollar-sign' },
      { name: 'is_subscribe_save', type: 'boolean', description: 'Subscribe & Save flag', icon: 'repeat' },
      { name: 'is_new_to_brand', type: 'boolean', description: 'New to brand flag', icon: 'award' }
    ]
  },

  // User Data Tables
  'user_segments': {
    name: 'user_segments',
    category: 'User Data',
    description: 'User segment assignments',
    fields: [
      { name: 'user_id', type: 'string', description: 'User identifier', icon: 'user' },
      { name: 'segment_id', type: 'string', description: 'Segment identifier', icon: 'users' },
      { name: 'segment_name', type: 'string', description: 'Segment name', icon: 'tag' },
      { name: 'assignment_dt', type: 'date', description: 'Assignment date', icon: 'calendar' },
      { name: 'confidence_score', type: 'decimal', description: 'Confidence score', icon: 'percent' }
    ]
  },
  'user_actions': {
    name: 'user_actions',
    category: 'User Data',
    description: 'User action events',
    fields: [
      { name: 'action_dt', type: 'timestamp', description: 'Action timestamp', icon: 'clock' },
      { name: 'user_id', type: 'string', description: 'User identifier', icon: 'user' },
      { name: 'action_type', type: 'string', description: 'Type of action', icon: 'activity' },
      { name: 'action_value', type: 'string', description: 'Action value or details', icon: 'info' },
      { name: 'session_id', type: 'string', description: 'Session identifier', icon: 'key' }
    ]
  },

  // Aggregated Tables
  'campaign_performance': {
    name: 'campaign_performance',
    category: 'Aggregated Data',
    description: 'Pre-aggregated campaign performance metrics',
    fields: [
      { name: 'date', type: 'date', description: 'Date', icon: 'calendar' },
      { name: 'campaign_id', type: 'bigint', description: 'Campaign ID', icon: 'hash' },
      { name: 'impressions', type: 'bigint', description: 'Total impressions', icon: 'eye' },
      { name: 'clicks', type: 'bigint', description: 'Total clicks', icon: 'mouse-pointer' },
      { name: 'spend', type: 'decimal', description: 'Total spend', icon: 'dollar-sign' },
      { name: 'conversions', type: 'bigint', description: 'Total conversions', icon: 'trending-up' },
      { name: 'revenue', type: 'decimal', description: 'Total revenue', icon: 'shopping-cart' },
      { name: 'roas', type: 'decimal', description: 'Return on ad spend', icon: 'percent' }
    ]
  }
};

export const getTablesByCategory = (category: string): SchemaTable[] => {
  return Object.values(AMC_SCHEMA).filter(table => table.category === category);
};

export const getCategories = (): string[] => {
  const categories = new Set<string>();
  Object.values(AMC_SCHEMA).forEach(table => {
    categories.add(table.category);
  });
  return Array.from(categories);
};

export const searchTables = (query: string): SchemaTable[] => {
  const lowerQuery = query.toLowerCase();
  return Object.values(AMC_SCHEMA).filter(table => 
    table.name.toLowerCase().includes(lowerQuery) ||
    table.description?.toLowerCase().includes(lowerQuery) ||
    table.fields.some(field => 
      field.name.toLowerCase().includes(lowerQuery) ||
      field.description?.toLowerCase().includes(lowerQuery)
    )
  );
};