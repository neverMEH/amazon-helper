import React, { useState, useCallback, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { 
  Package, 
  Upload, 
  Search, 
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ColumnFiltersState
} from '@tanstack/react-table';
import { toast } from 'react-hot-toast';
import asinService, { type ASIN, type ASINListResponse } from '../services/asinService';
import ASINImportModal from '../components/asins/ASINImportModal';
import ASINDetailModal from '../components/asins/ASINDetailModal';
import LoadingSpinner from '../components/LoadingSpinner';

const ASINManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBrand, setSelectedBrand] = useState<string>('');
  const [showImportModal, setShowImportModal] = useState(false);
  const [selectedASIN, setSelectedASIN] = useState<ASIN | null>(null);
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);

  // Fetch ASINs
  const { data: asinData, isLoading, error, refetch } = useQuery<ASINListResponse>({
    queryKey: ['asins', page, pageSize, selectedBrand, searchQuery],
    queryFn: () => asinService.listASINs({
      page,
      page_size: pageSize,
      brand: selectedBrand || undefined,
      search: searchQuery || undefined,
      active: true
    }),
    staleTime: 5 * 60 * 1000 // 5 minutes
  });

  // Fetch brands for filter dropdown
  const { data: brandsData } = useQuery({
    queryKey: ['asin-brands'],
    queryFn: () => asinService.getBrands(),
    staleTime: 10 * 60 * 1000 // 10 minutes
  });

  // Column definitions
  const columns = useMemo<ColumnDef<ASIN>[]>(() => [
    {
      accessorKey: 'asin',
      header: 'ASIN',
      cell: ({ row }) => (
        <button
          className="text-blue-600 hover:text-blue-800 font-mono text-sm"
          onClick={() => setSelectedASIN(row.original)}
        >
          {row.original.asin}
        </button>
      )
    },
    {
      accessorKey: 'title',
      header: 'Product Title',
      cell: ({ getValue }: any) => {
        const title = getValue() as string | undefined;
        return (
          <div className="max-w-xs truncate" title={title}>
            {title || '-'}
          </div>
        );
      }
    },
    {
      accessorKey: 'brand',
      header: 'Brand',
      cell: ({ getValue }) => getValue() || '-'
    },
    {
      accessorKey: 'last_known_price',
      header: 'Price',
      cell: ({ getValue }: any) => {
        const price = getValue() as number | undefined;
        return price ? `$${price.toFixed(2)}` : '-';
      }
    },
    {
      accessorKey: 'monthly_estimated_units',
      header: 'Est. Units/Month',
      cell: ({ getValue }: any) => {
        const units = getValue() as number | undefined;
        return units ? units.toLocaleString() : '-';
      }
    },
    {
      accessorKey: 'marketplace',
      header: 'Marketplace',
      cell: ({ getValue }) => getValue() || 'US'
    },
    {
      accessorKey: 'updated_at',
      header: 'Last Updated',
      cell: ({ getValue }: any) => {
        const date = getValue() as string;
        return new Date(date).toLocaleDateString();
      }
    }
  ], []);

  // Table instance
  const table = useReactTable({
    data: asinData?.items || [],
    columns,
    state: {
      sorting,
      columnFilters
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualPagination: true,
    pageCount: asinData?.pages || 0
  });

  // Handle search
  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    refetch();
  }, [refetch]);

  // Handle brand filter change
  const handleBrandChange = useCallback((brand: string) => {
    setSelectedBrand(brand);
    setPage(1);
  }, []);

  // Handle import success
  const handleImportSuccess = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['asins'] });
    queryClient.invalidateQueries({ queryKey: ['asin-brands'] });
    setShowImportModal(false);
    toast.success('Import completed successfully');
  }, [queryClient]);

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-center mb-2">Error Loading ASINs</h2>
          <p className="text-gray-600 text-center">{(error as Error).message}</p>
          <button
            onClick={() => refetch()}
            className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Package className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">ASIN Management</h1>
                <p className="text-gray-600">
                  Manage product ASINs for AMC query parameters
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowImportModal(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Upload className="w-5 h-5 mr-2" />
              Import CSV
            </button>
          </div>

          {/* Stats */}
          {asinData && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-600 text-sm">Total ASINs</p>
                <p className="text-2xl font-bold">{asinData.total.toLocaleString()}</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-600 text-sm">Unique Brands</p>
                <p className="text-2xl font-bold">{brandsData?.total || 0}</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-600 text-sm">Current Page</p>
                <p className="text-2xl font-bold">{page} / {asinData.pages}</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-gray-600 text-sm">Page Size</p>
                <p className="text-2xl font-bold">{pageSize}</p>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white p-4 rounded-lg shadow mb-6">
            <div className="flex items-center gap-4">
              {/* Search */}
              <form onSubmit={handleSearch} className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by ASIN or title..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </form>

              {/* Brand Filter */}
              <div className="w-64">
                <select
                  value={selectedBrand}
                  onChange={(e) => handleBrandChange(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Brands</option>
                  {brandsData?.brands.map(brand => (
                    <option key={brand} value={brand}>{brand}</option>
                  ))}
                </select>
              </div>

              {/* Refresh */}
              <button
                onClick={() => refetch()}
                className="p-2 text-gray-600 hover:text-gray-800"
                title="Refresh"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <LoadingSpinner />
              <p className="mt-4 text-gray-600">Loading ASINs...</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b">
                    {table.getHeaderGroups().map(headerGroup => (
                      <tr key={headerGroup.id}>
                        {headerGroup.headers.map(header => (
                          <th
                            key={header.id}
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </th>
                        ))}
                      </tr>
                    ))}
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {table.getRowModel().rows.map(row => (
                      <tr key={row.id} className="hover:bg-gray-50">
                        {row.getVisibleCells().map(cell => (
                          <td key={cell.id} className="px-6 py-4 whitespace-nowrap text-sm">
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="px-6 py-3 bg-gray-50 border-t flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(1)}
                    disabled={page === 1}
                    className="px-3 py-1 border rounded disabled:opacity-50"
                  >
                    First
                  </button>
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border rounded disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <span className="px-3">
                    Page {page} of {asinData?.pages || 1}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(asinData?.pages || 1, p + 1))}
                    disabled={page === (asinData?.pages || 1)}
                    className="px-3 py-1 border rounded disabled:opacity-50"
                  >
                    Next
                  </button>
                  <button
                    onClick={() => setPage(asinData?.pages || 1)}
                    disabled={page === (asinData?.pages || 1)}
                    className="px-3 py-1 border rounded disabled:opacity-50"
                  >
                    Last
                  </button>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Items per page:</span>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value));
                      setPage(1);
                    }}
                    className="border rounded px-2 py-1"
                  >
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                    <option value={250}>250</option>
                    <option value={500}>500</option>
                  </select>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Modals */}
      {showImportModal && (
        <ASINImportModal
          isOpen={showImportModal}
          onClose={() => setShowImportModal(false)}
          onSuccess={handleImportSuccess}
        />
      )}

      {selectedASIN && (
        <ASINDetailModal
          asin={selectedASIN}
          isOpen={!!selectedASIN}
          onClose={() => setSelectedASIN(null)}
        />
      )}
    </div>
  );
};

export default ASINManagement;