import { memo, useMemo, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';
import { ArrowUp, ArrowDown } from 'lucide-react';

interface VirtualizedTableProps {
  data: any[];
  columns: string[];
  height?: number;
  rowHeight?: number;
  onSort?: (column: string, direction: 'asc' | 'desc') => void;
  sortColumn?: string;
  sortDirection?: 'asc' | 'desc';
}

const Row = memo(({ index, style, data: { items, columns, columnWidths } }: any) => {
  const item = items[index];
  
  return (
    <div style={style} className="flex border-b border-gray-200 hover:bg-gray-50">
      {columns.map((col: any, idx: any) => (
        <div 
          key={col}
          className="px-4 py-2 text-sm text-gray-900 truncate"
          style={{ width: columnWidths[idx] }}
          title={String(item[col] || '')}
        >
          {item[col] !== null && item[col] !== undefined ? String(item[col]) : '-'}
        </div>
      ))}
    </div>
  );
});

Row.displayName = 'Row';

export default function VirtualizedTable({
  data,
  columns,
  height = 600,
  rowHeight = 40,
  onSort,
  sortColumn,
  sortDirection
}: VirtualizedTableProps) {
  // Calculate column widths based on content
  const columnWidths = useMemo(() => {
    const widths = columns.map(col => {
      // Calculate max width needed for column
      const headerWidth = col.length * 10 + 40; // Approximate width for header
      const maxDataWidth = Math.min(
        300, // Max width cap
        Math.max(
          100, // Min width
          ...data.slice(0, 100).map(row => {
            const value = String(row[col] || '');
            return Math.min(300, value.length * 8 + 20);
          })
        )
      );
      return Math.max(headerWidth, maxDataWidth);
    });
    
    return widths;
  }, [data, columns]);

  const totalWidth = useMemo(() => 
    columnWidths.reduce((sum, width) => sum + width, 0),
    [columnWidths]
  );

  const handleSort = useCallback((column: string) => {
    if (onSort) {
      const newDirection = sortColumn === column && sortDirection === 'asc' ? 'desc' : 'asc';
      onSort(column, newDirection);
    }
  }, [onSort, sortColumn, sortDirection]);

  const itemData = useMemo(() => ({
    items: data,
    columns,
    columnWidths
  }), [data, columns, columnWidths]);

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No data to display
      </div>
    );
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div 
        className="flex bg-gray-50 border-b border-gray-200 sticky top-0 z-10"
        style={{ width: totalWidth }}
      >
        {columns.map((col, idx) => (
          <div
            key={col}
            className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
            style={{ width: columnWidths[idx] }}
            onClick={() => handleSort(col)}
          >
            <div className="flex items-center justify-between">
              <span className="truncate">{col}</span>
              {sortColumn === col && (
                <span className="ml-1">
                  {sortDirection === 'asc' ? (
                    <ArrowUp className="h-3 w-3" />
                  ) : (
                    <ArrowDown className="h-3 w-3" />
                  )}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Virtualized rows */}
      <List
        height={height}
        itemCount={data.length}
        itemSize={rowHeight}
        width="100%"
        itemData={itemData}
        overscanCount={5}
      >
        {Row}
      </List>
    </div>
  );
}

// Memoized version for performance
export const MemoizedVirtualizedTable = memo(VirtualizedTable);