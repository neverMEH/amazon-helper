import { memo } from 'react';

interface DataSourceSkeletonProps {
  count?: number;
}

export const DataSourceSkeleton = memo(({ count = 6 }: DataSourceSkeletonProps) => {
  // Only render the compact/list view skeleton
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
});

DataSourceSkeleton.displayName = 'DataSourceSkeleton';