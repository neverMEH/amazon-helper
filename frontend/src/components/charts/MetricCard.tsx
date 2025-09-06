import type { FC } from 'react';
import { formatNumber, formatPercentage, formatCurrency } from './BaseChart';

interface MetricCardProps {
  title: string;
  value: number | string;
  format?: 'number' | 'currency' | 'percentage' | 'custom';
  prefix?: string;
  suffix?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
    label?: string;
  };
  comparison?: {
    value: number | string;
    label: string;
  };
  icon?: React.ReactNode;
  color?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  loading?: boolean;
  error?: string;
  className?: string;
  onClick?: () => void;
}

export const MetricCard: FC<MetricCardProps> = ({
  title,
  value,
  format = 'number',
  prefix = '',
  suffix = '',
  trend,
  comparison,
  icon,
  color = 'default',
  loading = false,
  error,
  className = '',
  onClick
}) => {
  // Format the main value
  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;
    
    switch (format) {
      case 'currency':
        return formatCurrency(val);
      case 'percentage':
        return formatPercentage(val);
      case 'number':
        return formatNumber(val);
      case 'custom':
        return `${prefix}${val}${suffix}`;
      default:
        return val.toString();
    }
  };

  // Get color classes based on color prop
  const getColorClasses = () => {
    switch (color) {
      case 'success':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200';
      case 'danger':
        return 'bg-red-50 border-red-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-white border-gray-200';
    }
  };

  // Get trend icon and color
  const getTrendIcon = () => {
    if (!trend) return null;
    
    const isPositive = trend.direction === 'up';
    const isNeutral = trend.direction === 'neutral';
    
    const trendColor = isNeutral 
      ? 'text-gray-500' 
      : isPositive 
        ? 'text-green-600' 
        : 'text-red-600';
    
    const trendBg = isNeutral
      ? 'bg-gray-100'
      : isPositive
        ? 'bg-green-100'
        : 'bg-red-100';
    
    return (
      <div className={`flex items-center mt-2 text-sm ${trendColor}`}>
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full ${trendBg}`}>
          {isNeutral ? (
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
            </svg>
          ) : isPositive ? (
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          ) : (
            <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
            </svg>
          )}
          <span className="font-medium">
            {format === 'percentage' ? formatPercentage(Math.abs(trend.value)) : formatNumber(Math.abs(trend.value))}
          </span>
        </span>
        {trend.label && <span className="ml-2 text-gray-600">{trend.label}</span>}
      </div>
    );
  };

  if (loading) {
    return (
      <div className={`rounded-lg border p-6 ${getColorClasses()} ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`rounded-lg border border-red-200 bg-red-50 p-6 ${className}`}>
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  const cardContent = (
    <>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {formatValue(value)}
          </p>
          {getTrendIcon()}
          {comparison && (
            <p className="mt-2 text-sm text-gray-500">
              <span className="font-medium">{comparison.value}</span> {comparison.label}
            </p>
          )}
        </div>
        {icon && (
          <div className="ml-4 flex-shrink-0">
            <div className="p-3 bg-gray-100 rounded-lg">
              {icon}
            </div>
          </div>
        )}
      </div>
    </>
  );

  if (onClick) {
    return (
      <button
        onClick={onClick}
        className={`w-full text-left rounded-lg border p-6 transition-all hover:shadow-md ${getColorClasses()} ${className}`}
      >
        {cardContent}
      </button>
    );
  }

  return (
    <div className={`rounded-lg border p-6 ${getColorClasses()} ${className}`}>
      {cardContent}
    </div>
  );
};

// Mini metric card for compact displays
interface MiniMetricCardProps {
  label: string;
  value: number | string;
  format?: 'number' | 'currency' | 'percentage' | 'custom';
  trend?: number;
  className?: string;
}

export const MiniMetricCard: FC<MiniMetricCardProps> = ({
  label,
  value,
  format = 'number',
  trend,
  className = ''
}) => {
  const formatValue = (val: number | string): string => {
    if (typeof val === 'string') return val;
    
    switch (format) {
      case 'currency':
        return formatCurrency(val);
      case 'percentage':
        return formatPercentage(val);
      case 'number':
        return formatNumber(val);
      default:
        return val.toString();
    }
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-4 ${className}`}>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
      <div className="mt-1 flex items-baseline">
        <p className="text-xl font-semibold text-gray-900">{formatValue(value)}</p>
        {trend !== undefined && (
          <span className={`ml-2 text-sm font-medium ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend >= 0 ? '+' : ''}{formatPercentage(trend, 1)}
          </span>
        )}
      </div>
    </div>
  );
};