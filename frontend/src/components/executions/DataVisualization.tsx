import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  ScatterChart,
  Scatter
} from 'recharts';
import { TrendingUp, TrendingDown, Minus, AlertCircle } from 'lucide-react';

interface DataVisualizationProps {
  data: any[];
  columns: string[];
  title?: string;
  brands?: string[];
}

const COLORS = [
  '#6366f1', // indigo
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#f59e0b', // amber
  '#10b981', // emerald
  '#3b82f6', // blue
  '#ef4444', // red
  '#84cc16', // lime
  '#06b6d4', // cyan
  '#f97316', // orange
];

export default function DataVisualization({ data, columns, title, brands }: DataVisualizationProps) {
  // Detect data types and patterns
  const dataAnalysis = useMemo(() => {
    if (!data || data.length === 0) return null;

    const analysis: any = {
      numericColumns: [],
      dateColumns: [],
      categoricalColumns: [],
      trends: {},
      aggregations: {}
    };

    // Analyze each column
    columns.forEach(col => {
      const values = data.map(row => row[col]).filter(v => v !== null && v !== undefined);
      if (values.length === 0) return;

      const firstValue = values[0];
      
      // Check if numeric
      if (typeof firstValue === 'number' || !isNaN(Number(firstValue))) {
        analysis.numericColumns.push(col);
        
        // Calculate stats
        const numbers = values.map(v => Number(v));
        const sum = numbers.reduce((a, b) => a + b, 0);
        const avg = sum / numbers.length;
        const max = Math.max(...numbers);
        const min = Math.min(...numbers);
        
        analysis.aggregations[col] = {
          sum: sum.toFixed(2),
          avg: avg.toFixed(2),
          max,
          min,
          count: numbers.length
        };

        // Calculate trend
        if (numbers.length > 1) {
          const firstHalf = numbers.slice(0, Math.floor(numbers.length / 2));
          const secondHalf = numbers.slice(Math.floor(numbers.length / 2));
          const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
          const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
          
          analysis.trends[col] = {
            direction: secondAvg > firstAvg ? 'up' : secondAvg < firstAvg ? 'down' : 'stable',
            change: ((secondAvg - firstAvg) / firstAvg * 100).toFixed(1)
          };
        }
      }
      // Check if date
      else if (col.toLowerCase().includes('date') || col.toLowerCase().includes('time')) {
        analysis.dateColumns.push(col);
      }
      // Otherwise categorical
      else {
        analysis.categoricalColumns.push(col);
      }
    });

    return analysis;
  }, [data, columns]);

  // Prepare data for time series chart if dates are present
  const timeSeriesData = useMemo(() => {
    if (!dataAnalysis || dataAnalysis.dateColumns.length === 0) return null;
    
    const dateCol = dataAnalysis.dateColumns[0];
    const numericCol = dataAnalysis.numericColumns[0];
    
    if (!numericCol) return null;

    return data.map(row => ({
      date: new Date(row[dateCol]).toLocaleDateString(),
      value: Number(row[numericCol]),
      ...row
    })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [data, dataAnalysis]);

  // Prepare data for category distribution
  const categoryData = useMemo(() => {
    if (!dataAnalysis || dataAnalysis.categoricalColumns.length === 0) return null;
    
    const catCol = dataAnalysis.categoricalColumns[0];
    const distribution: { [key: string]: number } = {};
    
    data.forEach(row => {
      const value = row[catCol];
      if (value) {
        distribution[value] = (distribution[value] || 0) + 1;
      }
    });

    return Object.entries(distribution).map(([name, value]) => ({
      name,
      value
    }));
  }, [data, dataAnalysis]);

  // Prepare correlation data for scatter plot
  const correlationData = useMemo(() => {
    if (!dataAnalysis || dataAnalysis.numericColumns.length < 2) return null;
    
    const xCol = dataAnalysis.numericColumns[0];
    const yCol = dataAnalysis.numericColumns[1];
    
    return data.map(row => ({
      x: Number(row[xCol]),
      y: Number(row[yCol]),
      label: row[dataAnalysis.categoricalColumns[0]] || ''
    }));
  }, [data, dataAnalysis]);

  if (!dataAnalysis) {
    return (
      <div className="text-center py-8 text-gray-500">
        <AlertCircle className="h-8 w-8 mx-auto mb-2" />
        <p>No data available for visualization</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {title && (
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      )}

      {/* Key Metrics */}
      {dataAnalysis.numericColumns.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {dataAnalysis.numericColumns.slice(0, 4).map((col: string) => (
            <div key={col} className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                {col.replace(/_/g, ' ')}
              </div>
              <div className="text-2xl font-bold text-gray-900">
                {dataAnalysis.aggregations[col].sum}
              </div>
              <div className="flex items-center mt-2 text-sm">
                {dataAnalysis.trends[col] && (
                  <>
                    {dataAnalysis.trends[col].direction === 'up' ? (
                      <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                    ) : dataAnalysis.trends[col].direction === 'down' ? (
                      <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
                    ) : (
                      <Minus className="h-4 w-4 text-gray-400 mr-1" />
                    )}
                    <span className={
                      dataAnalysis.trends[col].direction === 'up' ? 'text-green-600' :
                      dataAnalysis.trends[col].direction === 'down' ? 'text-red-600' :
                      'text-gray-600'
                    }>
                      {dataAnalysis.trends[col].change}%
                    </span>
                  </>
                )}
                <span className="text-gray-500 ml-2">
                  Avg: {dataAnalysis.aggregations[col].avg}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Time Series Chart */}
      {timeSeriesData && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Trend Over Time</h4>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timeSeriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#6366f1" 
                fill="#6366f1" 
                fillOpacity={0.3}
                name={dataAnalysis.numericColumns[0]}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Category Distribution */}
      {categoryData && categoryData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Distribution by Category</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Category Breakdown</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Correlation Scatter Plot */}
      {correlationData && dataAnalysis.numericColumns.length >= 2 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Correlation: {dataAnalysis.numericColumns[0]} vs {dataAnalysis.numericColumns[1]}
          </h4>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="x" 
                name={dataAnalysis.numericColumns[0]}
                type="number"
              />
              <YAxis 
                dataKey="y"
                name={dataAnalysis.numericColumns[1]}
                type="number"
              />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter 
                name="Data Points" 
                data={correlationData} 
                fill="#6366f1"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Comparison by Brand */}
      {brands && brands.length > 0 && dataAnalysis.numericColumns.length > 0 && (
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Performance by Brand</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart 
              data={brands.map(brand => {
                const brandData = data.filter((row: any) => 
                  Object.values(row).some(v => 
                    typeof v === 'string' && v.toLowerCase().includes(brand.toLowerCase())
                  )
                );
                return {
                  brand,
                  ...dataAnalysis.numericColumns.reduce((acc: any, col: string) => {
                    const values = brandData.map(row => Number(row[col as string]) || 0);
                    acc[col] = values.reduce((a, b) => a + b, 0);
                    return acc;
                  }, {} as any)
                };
              })}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="brand" />
              <YAxis />
              <Tooltip />
              <Legend />
              {dataAnalysis.numericColumns.slice(0, 3).map((col: string, idx: number) => (
                <Bar 
                  key={col}
                  dataKey={col} 
                  fill={COLORS[idx % COLORS.length]}
                  name={col.replace(/_/g, ' ')}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}