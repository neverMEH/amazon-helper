import { BarChart, PieChart, TrendingUp } from 'lucide-react';

interface ResultsVisualizationProps {
  columns: Array<{ name: string; type: string }>;
  rows: any[][];
}

export default function ResultsVisualization({ columns, rows }: ResultsVisualizationProps) {
  // Simple analysis of the data
  const numericColumns = columns
    .map((col, idx) => ({ ...col, index: idx }))
    .filter(col => ['integer', 'numeric', 'float', 'double'].includes(col.type.toLowerCase()));

  const categoricalColumns = columns
    .map((col, idx) => ({ ...col, index: idx }))
    .filter(col => ['varchar', 'text', 'string'].includes(col.type.toLowerCase()));

  // Calculate basic statistics for numeric columns
  const numericStats = numericColumns.map(col => {
    const values = rows.map(row => parseFloat(row[col.index])).filter(v => !isNaN(v));
    const sum = values.reduce((a, b) => a + b, 0);
    const avg = sum / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);
    
    return {
      column: col.name,
      sum,
      avg,
      min,
      max,
      count: values.length
    };
  });

  // Count unique values for categorical columns (for first 3 categorical columns)
  const categoricalStats = categoricalColumns.slice(0, 3).map(col => {
    const valueCounts: Record<string, number> = {};
    rows.forEach(row => {
      const value = String(row[col.index]);
      valueCounts[value] = (valueCounts[value] || 0) + 1;
    });
    
    return {
      column: col.name,
      uniqueValues: Object.keys(valueCounts).length,
      topValues: Object.entries(valueCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([value, count]) => ({ value, count }))
    };
  });

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium">Data Insights</h3>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <BarChart className="h-5 w-5 text-blue-600 mr-2" />
            <h4 className="font-medium text-blue-900">Total Rows</h4>
          </div>
          <p className="text-2xl font-bold text-blue-900">{rows.length.toLocaleString()}</p>
        </div>
        
        <div className="bg-green-50 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <PieChart className="h-5 w-5 text-green-600 mr-2" />
            <h4 className="font-medium text-green-900">Columns</h4>
          </div>
          <p className="text-2xl font-bold text-green-900">{columns.length}</p>
          <p className="text-sm text-green-700">
            {numericColumns.length} numeric, {categoricalColumns.length} text
          </p>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <TrendingUp className="h-5 w-5 text-purple-600 mr-2" />
            <h4 className="font-medium text-purple-900">Data Points</h4>
          </div>
          <p className="text-2xl font-bold text-purple-900">
            {(rows.length * columns.length).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Numeric Column Stats */}
      {numericStats.length > 0 && (
        <div>
          <h4 className="font-medium mb-3">Numeric Column Statistics</h4>
          <div className="bg-gray-50 rounded-lg overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Column</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Min</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Max</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Average</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Sum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {numericStats.map((stat, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2 text-sm font-medium text-gray-900">{stat.column}</td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600">
                      {stat.min != null ? stat.min.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '0'}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600">
                      {stat.max != null ? stat.max.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '0'}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600">
                      {stat.avg != null ? stat.avg.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '0'}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-gray-600">
                      {stat.sum != null ? stat.sum.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '0'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Categorical Column Distribution */}
      {categoricalStats.length > 0 && (
        <div>
          <h4 className="font-medium mb-3">Categorical Column Distribution</h4>
          <div className="grid grid-cols-1 gap-4">
            {categoricalStats.map((stat, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-4">
                <h5 className="font-medium text-gray-900 mb-2">
                  {stat.column} 
                  <span className="text-sm font-normal text-gray-500 ml-2">
                    ({stat.uniqueValues} unique values)
                  </span>
                </h5>
                <div className="space-y-2">
                  {stat.topValues.map((item, i) => (
                    <div key={i} className="flex items-center">
                      <div className="flex-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-700">{item.value}</span>
                          <span className="text-gray-500">{item.count} ({((item.count / rows.length) * 100).toFixed(1)}%)</span>
                        </div>
                        <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full"
                            style={{ width: `${(item.count / rows.length) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}