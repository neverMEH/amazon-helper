import { memo } from 'react';

interface DataSourceSkeletonProps {
  viewMode?: 'card' | 'compact';
  count?: number;
}

export const DataSourceSkeleton = memo(({ viewMode = 'card', count = 6 }: DataSourceSkeletonProps) => {
  if (viewMode === 'compact') {
    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left">
                <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
              </th>
              <th className="px-4 py-3 text-left">
                <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
              </th>
              <th className="px-4 py-3 text-left">
                <div className="h-4 w-12 bg-gray-200 rounded animate-pulse" />
              </th>
              <th className="px-4 py-3 text-left">
                <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
              </th>
              <th className="px-4 py-3 text-left">
                <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {Array.from({ length: count }).map((_, i) => (
              <tr key={i} className="animate-pulse">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 bg-gray-200 rounded" />
                    <div className="h-4 w-32 bg-gray-200 rounded" />
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 w-24 bg-gray-200 rounded" />
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <div className="h-4 w-8 bg-gray-200 rounded" />
                    <div className="h-4 w-8 bg-gray-200 rounded" />
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="h-4 w-16 bg-gray-200 rounded" />
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    <div className="h-4 w-12 bg-gray-200 rounded" />
                    <div className="h-4 w-12 bg-gray-200 rounded" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="grid gap-4 grid-cols-1 xl:grid-cols-2">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white rounded-lg border border-gray-200 p-5 animate-pulse"
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <div className="h-6 w-40 bg-gray-200 rounded" />
                <div className="h-4 w-16 bg-gray-200 rounded" />
              </div>
              <div className="h-3 w-32 bg-gray-200 rounded mt-2" />
            </div>
            <div className="h-5 w-5 bg-gray-200 rounded" />
          </div>

          {/* Description */}
          <div className="space-y-2 mb-3">
            <div className="h-3 w-full bg-gray-200 rounded" />
            <div className="h-3 w-3/4 bg-gray-200 rounded" />
          </div>

          {/* Stats Bar */}
          <div className="flex items-center gap-4 mb-3 pb-3 border-b border-gray-100">
            <div className="flex items-center gap-1.5">
              <div className="h-4 w-4 bg-gray-200 rounded" />
              <div className="h-4 w-12 bg-gray-200 rounded" />
            </div>
            <div className="flex items-center gap-1.5">
              <div className="h-4 w-4 bg-gray-200 rounded" />
              <div className="h-4 w-12 bg-gray-200 rounded" />
            </div>
            <div className="flex items-center gap-1.5 ml-auto">
              <div className="h-4 w-4 bg-gray-200 rounded" />
              <div className="h-4 w-16 bg-gray-200 rounded" />
            </div>
          </div>

          {/* Tags */}
          <div className="flex gap-1.5">
            <div className="h-5 w-16 bg-gray-200 rounded" />
            <div className="h-5 w-20 bg-gray-200 rounded" />
            <div className="h-5 w-14 bg-gray-200 rounded" />
          </div>

          {/* Category */}
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="h-5 w-24 bg-gray-200 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
});

DataSourceSkeleton.displayName = 'DataSourceSkeleton';