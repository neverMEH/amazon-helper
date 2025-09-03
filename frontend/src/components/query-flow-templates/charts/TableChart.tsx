import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Download, Search } from 'lucide-react';
import type { TemplateChartConfig } from '../../../types/queryFlowTemplate';
import { ChartDataMapper, type TableData } from './ChartDataMapper';

interface TableChartProps {
  chartConfig: TemplateChartConfig;
  data: any[];
  className?: string;
}

const TableChart: React.FC<TableChartProps> = ({
  chartConfig,
  data,
  className = ''
}) => {
  const tableData = ChartDataMapper.mapToChartData(data, chartConfig) as TableData;
  
  const [sortConfig, setSortConfig] = useState<{
    field: string;
    direction: 'asc' | 'desc';
  } | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  
  const pageSize = chartConfig.chart_config.pageSize || 10;
  const isPaginated = chartConfig.chart_config.pagination !== false;
  const isSearchable = chartConfig.chart_config.filterable !== false;
  const isExportable = chartConfig.chart_config.exportable !== false;

  // Filter data based on search term
  const filteredData = useMemo(() => {
    if (!searchTerm) return tableData.rows;
    
    return tableData.rows.filter(row =>
      Object.values(row).some(value => {
        const displayValue = typeof value === 'object' && value?.display 
          ? value.display 
          : String(value);
        return displayValue.toLowerCase().includes(searchTerm.toLowerCase());
      })
    );
  }, [tableData.rows, searchTerm]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aValue = a[sortConfig.field];
      const bValue = b[sortConfig.field];
      
      // Handle formatted values
      const aRaw = typeof aValue === 'object' && aValue?.raw !== undefined ? aValue.raw : aValue;
      const bRaw = typeof bValue === 'object' && bValue?.raw !== undefined ? bValue.raw : bValue;
      
      if (aRaw < bRaw) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aRaw > bRaw) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredData, sortConfig]);

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!isPaginated) return sortedData;
    
    const startIndex = (currentPage - 1) * pageSize;
    return sortedData.slice(startIndex, startIndex + pageSize);
  }, [sortedData, currentPage, pageSize, isPaginated]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleSort = (field: string) => {
    if (!chartConfig.chart_config.sortable) return;

    setSortConfig(current => {
      if (current?.field === field) {
        return {
          field,
          direction: current.direction === 'asc' ? 'desc' : 'asc'
        };
      }
      return { field, direction: 'asc' };
    });
  };

  const handleExport = () => {
    const csv = [
      // Header row
      tableData.columns.map(col => col.header).join(','),
      // Data rows
      ...sortedData.map(row =>
        tableData.columns.map(col => {
          const value = row[col.field];
          const displayValue = typeof value === 'object' && value?.display !== undefined 
            ? value.display 
            : String(value);
          return `"${displayValue.replace(/"/g, '""')}"`;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${chartConfig.chart_name.replace(/\s+/g, '_')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderCellValue = (value: any, format?: string) => {
    if (typeof value === 'object' && value?.display !== undefined) {
      return value.display;
    }
    return String(value);
  };

  return (
    <div className={className}>
      {/* Table Controls */}
      {(isSearchable || isExportable) && (
        <div className="flex items-center justify-between mb-4">
          {isSearchable && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder="Search table..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          )}

          {isExportable && (
            <button
              onClick={handleExport}
              className="flex items-center space-x-2 px-3 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
            >
              <Download className="h-4 w-4" />
              <span>Export CSV</span>
            </button>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {tableData.columns.map((column) => (
                <th
                  key={column.field}
                  onClick={() => handleSort(column.field)}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    chartConfig.chart_config.sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                  }`}
                  style={{ width: column.width }}
                >
                  <div className="flex items-center space-x-1">
                    <span>{column.header}</span>
                    {chartConfig.chart_config.sortable && sortConfig?.field === column.field && (
                      sortConfig.direction === 'asc' ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((row, index) => (
              <tr key={index} className="hover:bg-gray-50">
                {tableData.columns.map((column) => (
                  <td key={column.field} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {renderCellValue(row[column.field], column.format)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {isPaginated && totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <div className="text-sm text-gray-700">
            Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} results
          </div>
          <div className="flex space-x-1">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const page = i + 1;
              return (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-1 border rounded-md text-sm ${
                    currentPage === page
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              );
            })}
            
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TableChart;