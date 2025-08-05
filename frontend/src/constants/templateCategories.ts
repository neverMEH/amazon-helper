export interface TemplateCategory {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  templates?: string[];
}

export const TEMPLATE_CATEGORIES: Record<string, TemplateCategory> = {
  'path-to-conversion': {
    id: 'path-to-conversion',
    name: 'Path to Conversion',
    description: 'Analyze customer conversion journeys and attribution',
    icon: 'TrendingUp',
    templates: [
      'Path to conversion by campaign',
      'Multi-touch attribution analysis',
      'Conversion funnel analysis',
      'Time to conversion analysis'
    ]
  },
  'overlap-analysis': {
    id: 'overlap-analysis',
    name: 'Overlap Analysis',
    description: 'Understand audience and channel overlaps',
    icon: 'Users',
    templates: [
      'Sponsored ads and DSP overlap',
      'Cross-channel performance',
      'Audience overlap insights',
      'Channel attribution overlap'
    ]
  },
  'product-analysis': {
    id: 'product-analysis',
    name: 'Product Analysis',
    description: 'ASIN and product performance insights',
    icon: 'Package',
    templates: [
      'Sponsored ads ASIN cross-purchase',
      'ASIN conversions tracked item vs tracked asin',
      'Product purchase journeys',
      'New-to-brand analysis by ASIN'
    ]
  },
  'upselling-cross-selling': {
    id: 'upselling-cross-selling',
    name: 'Upselling & Cross-selling',
    description: 'Identify upsell and cross-sell opportunities',
    icon: 'ShoppingCart',
    templates: [
      'ASIN purchase overlap for upselling',
      'Complementary product analysis',
      'Bundle opportunity identification',
      'Repeat purchase patterns'
    ]
  },
  'audience-insights': {
    id: 'audience-insights',
    name: 'Audience Insights',
    description: 'Deep dive into audience behavior',
    icon: 'Target',
    templates: [
      'Audience segmentation analysis',
      'Geographic performance',
      'Device and browser analysis',
      'Demographic insights'
    ]
  },
  'campaign-performance': {
    id: 'campaign-performance',
    name: 'Campaign Performance',
    description: 'Campaign effectiveness and optimization',
    icon: 'BarChart',
    templates: [
      'Campaign performance summary',
      'Cost per acquisition analysis',
      'ROAS by campaign type',
      'Campaign pacing analysis'
    ]
  },
  'custom-queries': {
    id: 'custom-queries',
    name: 'Custom Queries',
    description: 'Build your own custom analysis',
    icon: 'Code',
    templates: [
      'Blank query template',
      'Basic SELECT template',
      'JOIN template',
      'Window functions template'
    ]
  }
};

export const getFlatTemplateList = (): string[] => {
  return Object.values(TEMPLATE_CATEGORIES).flatMap(cat => cat.templates || []);
};

export const getCategoryByTemplate = (templateName: string): TemplateCategory | undefined => {
  return Object.values(TEMPLATE_CATEGORIES).find(cat => 
    cat.templates?.includes(templateName)
  );
};

export const getCategoryCount = (categoryId: string): number => {
  const category = TEMPLATE_CATEGORIES[categoryId];
  return category?.templates?.length || 0;
};