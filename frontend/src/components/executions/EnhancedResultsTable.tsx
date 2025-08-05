import { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Download, Search, Filter, Copy } from 'lucide-react';
import toast from 'react-hot-toast';

interface Props {
  data: any[];
  instanceInfo?: {
    instanceId: string;
    instanceName: string;
    region: string;
    accountId: string;
    accountName: string;
  };
  brands?: string[];
}

type SortDirection = 'asc' | 'desc' | null;

export default function EnhancedResultsTable({ data, instanceInfo, brands }: Props) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());
  const [showColumnFilter, setShowColumnFilter] = useState(false);

  // Get column headers from first row
  const columns = useMemo(() => {
    if (!data || !Array.isArray(data) || data.length === 0) return [];
    return Object.keys(data[0]);
  }, [data]);

  // Initialize visible columns
  useMemo(() => {
    if (columns.length > 0 && visibleColumns.size === 0) {
      setVisibleColumns(new Set(columns));
    }
  }, [columns]);

  // Filter data based on search term
  const filteredData = useMemo(() => {
    if (!data || !Array.isArray(data)) return [];
    
    if (!searchTerm) return data;
    
    return data.filter(row => {
      return Object.values(row).some(value =>
        value?.toString().toLowerCase().includes(searchTerm.toLowerCase())
      );
    });
  }, [data, searchTerm]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return filteredData;
    
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      
      // Handle null/undefined values
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;
      
      // Try to sort numerically if possible
      const aNum = Number(aVal);
      const bNum = Number(bVal);
      
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
      }
      
      // Otherwise sort alphabetically
      const aStr = aVal.toString();
      const bStr = bVal.toString();
      
      if (sortDirection === 'asc') {
        return aStr.localeCompare(bStr);
      } else {
        return bStr.localeCompare(aStr);
      }
    });
  }, [filteredData, sortColumn, sortDirection]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  // Handle column sort
  const handleSort = (column: string) => {
    if (sortColumn === column) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortDirection(null);
        setSortColumn(null);
      }
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Toggle column visibility
  const toggleColumnVisibility = (column: string) => {
    const newVisible = new Set(visibleColumns);
    if (newVisible.has(column)) {
      newVisible.delete(column);
    } else {
      newVisible.add(column);
    }
    setVisibleColumns(newVisible);
  };

  // Export functions
  const exportToCSV = () => {
    try {
      const headers = columns.filter(col => visibleColumns.has(col));
      const csvContent = [
        headers.join(','),
        ...sortedData.map(row =>
          headers.map(col => {
            const value = row[col];
            // Escape quotes and wrap in quotes if contains comma
            const str = value?.toString() || '';
            return str.includes(',') || str.includes('"')
              ? `"${str.replace(/"/g, '""')}"`
              : str;
          }).join(',')
        )
      ].join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `execution-results-${new Date().toISOString()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Data exported to CSV');
    } catch (error) {
      toast.error('Failed to export CSV');
    }
  };

  const exportToJSON = () => {
    try {
      const exportData = {
        metadata: {
          exportDate: new Date().toISOString(),
          rowCount: sortedData.length,
          instanceInfo,
          brands
        },
        data: sortedData
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `execution-results-${new Date().toISOString()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Data exported to JSON');
    } catch (error) {
      toast.error('Failed to export JSON');
    }
  };

  const copyToClipboard = () => {
    try {
      const selectedData = selectedRows.size > 0
        ? sortedData.filter((_, idx) => selectedRows.has(idx))
        : sortedData;
      
      const text = selectedData.map(row =>
        columns.filter(col => visibleColumns.has(col))
          .map(col => row[col]?.toString() || '')
          .join('\t')
      ).join('\n');
      
      navigator.clipboard.writeText(text);
      toast.success(`Copied ${selectedData.length} rows to clipboard`);
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  // Toggle row selection
  const toggleRowSelection = (index: number) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedRows(newSelected);
  };

  const toggleAllRows = () => {
    if (selectedRows.size === sortedData.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(sortedData.map((_, idx) => idx)));
    }
  };

  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="text-sm text-gray-500 p-4 bg-gray-50 rounded-md">
        No results available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Instance and Brand Info */}
      {(instanceInfo || brands) && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex flex-wrap gap-4 text-sm">
            {instanceInfo && (
              <div>
                <span className="font-medium text-blue-900">Instance:</span>{' '}
                <span className="text-blue-700">{instanceInfo.instanceName} ({instanceInfo.region})</span>
              </div>
            )}
            {brands && brands.length > 0 && (
              <div>
                <span className="font-medium text-blue-900">Brands:</span>{' '}
                <span className="text-blue-700">{brands.join(', ')}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Controls */}
      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex gap-2 flex-1">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search all columns..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="pl-10 pr-3 py-2 w-full border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Column Filter */}
          <button
            onClick={() => setShowColumnFilter(!showColumnFilter)}
            className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            <Filter className="h-4 w-4" />
            Columns ({visibleColumns.size}/{columns.length})
          </button>
        </div>

        {/* Export buttons */}
        <div className="flex gap-2">
          <button
            onClick={exportToCSV}
            className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            CSV
          </button>
          <button
            onClick={exportToJSON}
            className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            JSON
          </button>
          <button
            onClick={copyToClipboard}
            className="px-3 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            <Copy className="h-4 w-4" />
            Copy
          </button>
        </div>
      </div>

      {/* Column visibility dropdown */}
      {showColumnFilter && (
        <div className="p-3 bg-white border border-gray-200 rounded-md shadow-sm">
          <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
            {columns.map(column => (
              <label key={column} className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={visibleColumns.has(column)}
                  onChange={() => toggleColumnVisibility(column)}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="truncate">{column}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Results summary */}
      <div className="text-sm text-gray-600">
        Showing {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} results
        {searchTerm && ` (filtered from ${data.length} total)`}
        {selectedRows.size > 0 && ` • ${selectedRows.size} selected`}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-300">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-3.5 text-left">
                <input
                  type="checkbox"
                  checked={selectedRows.size === sortedData.length && sortedData.length > 0}
                  onChange={toggleAllRows}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
              </th>
              {columns.filter(col => visibleColumns.has(col)).map((column) => (
                <th
                  key={column}
                  className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort(column)}
                >
                  <div className="flex items-center gap-1">
                    {column}
                    {sortColumn === column && (
                      sortDirection === 'asc' ? <ChevronUp className="h-4 w-4" /> :
                      sortDirection === 'desc' ? <ChevronDown className="h-4 w-4" /> : null
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {paginatedData.map((row, idx) => {
              const globalIndex = (currentPage - 1) * pageSize + idx;
              return (
                <tr key={idx} className={selectedRows.has(globalIndex) ? 'bg-indigo-50' : ''}>
                  <td className="px-3 py-4">
                    <input
                      type="checkbox"
                      checked={selectedRows.has(globalIndex)}
                      onChange={() => toggleRowSelection(globalIndex)}
                      className="rounded text-indigo-600 focus:ring-indigo-500"
                    />
                  </td>
                  {columns.filter(col => visibleColumns.has(col)).map((column) => (
                    <td
                      key={column}
                      className="whitespace-nowrap px-3 py-4 text-sm text-gray-500"
                    >
                      {row[column]?.toString() || '-'}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-700">
              Rows per page:
            </label>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="border border-gray-300 rounded-md px-2 py-1 text-sm"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`px-3 py-1 border rounded-md text-sm ${
                      currentPage === pageNum
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
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
}