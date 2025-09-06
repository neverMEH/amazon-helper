import type { FC } from 'react';
import { Pie, Doughnut } from 'react-chartjs-2';
import type { ChartData, ChartOptions } from 'chart.js';
import { BaseChart, CHART_COLORS_ARRAY, formatNumber, formatPercentage } from './BaseChart';

interface PieChartProps {
  title?: string;
  description?: string;
  data: {
    labels: string[];
    values: number[];
    backgroundColor?: string[];
    borderColor?: string | string[];
  };
  loading?: boolean;
  error?: string;
  height?: number;
  showLegend?: boolean;
  legendPosition?: 'top' | 'bottom' | 'left' | 'right';
  showPercentages?: boolean;
  className?: string;
  customOptions?: Partial<ChartOptions<'pie'>>;
}

export const PieChart: FC<PieChartProps> = ({
  title,
  description,
  data,
  loading = false,
  error,
  height = 300,
  showLegend = true,
  legendPosition = 'right',
  showPercentages = true,
  className = '',
  customOptions = {}
}) => {
  // Calculate total for percentage calculations
  const total = data.values.reduce((sum, value) => sum + value, 0);

  // Prepare chart data with default styling
  const chartData: ChartData<'pie'> = {
    labels: data.labels,
    datasets: [{
      data: data.values,
      backgroundColor: data.backgroundColor || CHART_COLORS_ARRAY.slice(0, data.labels.length),
      borderColor: data.borderColor || '#ffffff',
      borderWidth: 2,
      hoverOffset: 4
    }]
  };

  // Create chart options
  const options: ChartOptions<'pie'> = {
    responsive: true,
    maintainAspectRatio: false,
    ...customOptions,
    plugins: {
      ...customOptions.plugins,
      legend: {
        display: showLegend,
        position: legendPosition,
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12
          },
          generateLabels: function(chart) {
            const data = chart.data;
            if (data.labels && data.labels.length && data.datasets && data.datasets.length) {
              const dataset = data.datasets[0];
              const values = dataset.data as number[];
              
              return data.labels.map((label, i) => {
                const value = values[i];
                const percentage = total > 0 ? (value / total * 100) : 0;
                
                return {
                  text: showPercentages 
                    ? `${label}: ${formatPercentage(percentage)}`
                    : `${label}: ${formatNumber(value)}`,
                  fillStyle: Array.isArray(dataset.backgroundColor) 
                    ? dataset.backgroundColor[i] 
                    : dataset.backgroundColor,
                  strokeStyle: Array.isArray(dataset.borderColor)
                    ? dataset.borderColor[i]
                    : dataset.borderColor,
                  lineWidth: dataset.borderWidth as number,
                  hidden: false,
                  index: i
                };
              });
            }
            return [];
          }
        }
      },
      tooltip: {
        ...customOptions.plugins?.tooltip,
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const percentage = total > 0 ? (value / total * 100) : 0;
            
            if (showPercentages) {
              return `${label}: ${formatNumber(value)} (${formatPercentage(percentage)})`;
            } else {
              return `${label}: ${formatNumber(value)}`;
            }
          }
        }
      }
    }
  };

  return (
    <BaseChart
      title={title}
      description={description}
      loading={loading}
      error={error}
      className={className}
    >
      <div style={{ height: `${height}px` }}>
        <Pie data={chartData} options={options} />
      </div>
    </BaseChart>
  );
};

// Doughnut Chart variant
interface DoughnutChartProps extends PieChartProps {
  cutout?: string | number;
  centerText?: string;
}

export const DoughnutChart: FC<DoughnutChartProps> = ({
  cutout = '50%',
  centerText,
  ...props
}) => {
  const doughnutOptions: ChartOptions<'doughnut'> = {
    ...props.customOptions,
    cutout,
    plugins: {
      ...props.customOptions?.plugins,
      // Add center text plugin if provided
      ...(centerText ? {
        beforeDraw: function(chart: any) {
          const { ctx, chartArea: { width, height } } = chart;
          ctx.save();
          ctx.font = 'bold 20px sans-serif';
          ctx.fillStyle = '#1f2937';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(centerText, width / 2, height / 2);
          ctx.restore();
        }
      } : {})
    }
  };

  // Prepare chart data (same as pie)
  const total = props.data.values.reduce((sum, value) => sum + value, 0);
  const chartData: ChartData<'doughnut'> = {
    labels: props.data.labels,
    datasets: [{
      data: props.data.values,
      backgroundColor: props.data.backgroundColor || CHART_COLORS_ARRAY.slice(0, props.data.labels.length),
      borderColor: props.data.borderColor || '#ffffff',
      borderWidth: 2,
      hoverOffset: 4
    }]
  };

  return (
    <BaseChart
      title={props.title}
      description={props.description}
      loading={props.loading}
      error={props.error}
      className={props.className}
    >
      <div style={{ height: `${props.height || 300}px` }}>
        <Doughnut data={chartData} options={doughnutOptions as ChartOptions<'doughnut'>} />
      </div>
    </BaseChart>
  );
};