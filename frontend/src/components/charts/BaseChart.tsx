import type { FC, ReactNode } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend, TimeScale } from 'chart.js';
import type { ChartOptions } from 'chart.js';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface BaseChartProps {
  title?: string;
  description?: string;
  loading?: boolean;
  error?: string;
  children: ReactNode;
  className?: string;
}

export const BaseChart: FC<BaseChartProps> = ({
  title,
  description,
  loading = false,
  error,
  children,
  className = ''
}) => {
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="animate-pulse">
          {title && <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>}
          <div className="h-64 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="text-red-500 text-center py-8">
          <svg className="mx-auto h-12 w-12 text-red-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {title && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
        </div>
      )}
      <div className="relative">
        {children}
      </div>
    </div>
  );
};

// Common chart options factory
export const createChartOptions = (type: 'line' | 'bar' | 'pie', customOptions?: Partial<ChartOptions>): ChartOptions => {
  const baseOptions: ChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12
          }
        }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleFont: {
          size: 13
        },
        bodyFont: {
          size: 12
        },
        padding: 10,
        cornerRadius: 4
      }
    }
  };

  if (type === 'line' || type === 'bar') {
    baseOptions.scales = {
      x: {
        grid: {
          display: false
        },
        ticks: {
          font: {
            size: 11
          }
        }
      },
      y: {
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          font: {
            size: 11
          }
        }
      }
    };
  }

  return { ...baseOptions, ...customOptions } as ChartOptions;
};

// Chart color palette
export const CHART_COLORS = {
  primary: 'rgb(59, 130, 246)',      // blue-500
  secondary: 'rgb(16, 185, 129)',    // emerald-500
  tertiary: 'rgb(251, 146, 60)',     // orange-400
  quaternary: 'rgb(168, 85, 247)',   // purple-500
  quinary: 'rgb(236, 72, 153)',      // pink-500
  senary: 'rgb(245, 158, 11)',       // amber-500
  septenary: 'rgb(6, 182, 212)',     // cyan-500
  octonary: 'rgb(239, 68, 68)',      // red-500
  nonary: 'rgb(34, 197, 94)',        // green-500
  denary: 'rgb(99, 102, 241)'        // indigo-500
};

export const CHART_COLORS_ARRAY = Object.values(CHART_COLORS);

// Utility function to format large numbers
export const formatNumber = (value: number): string => {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toLocaleString();
};

// Utility function to format percentages
export const formatPercentage = (value: number, decimals = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

// Utility function to format currency
export const formatCurrency = (value: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};