import { X } from 'lucide-react';

export interface FilterBadge {
  key: string;
  label: string;
  value: string;
  onRemove: () => void;
}

interface ActiveFilterBadgesProps {
  badges: FilterBadge[];
  onClearAll: () => void;
  resultCount?: number;
  totalCount?: number;
}

export default function ActiveFilterBadges({ 
  badges, 
  onClearAll, 
  resultCount, 
  totalCount 
}: ActiveFilterBadgesProps) {
  if (badges.length === 0) return null;

  return (
    <div className="mb-4 p-3 bg-blue-50 rounded-lg">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center flex-wrap gap-2">
          <span className="text-sm font-medium text-gray-700">Active Filters:</span>
          {badges.map((badge) => (
            <span
              key={badge.key}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200"
            >
              <span className="mr-1">{badge.label}:</span>
              <span className="font-normal">{badge.value}</span>
              <button
                onClick={badge.onRemove}
                className="ml-1.5 inline-flex items-center justify-center text-blue-600 hover:text-blue-800 focus:outline-none"
                aria-label={`Remove ${badge.label} filter`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
          <button
            onClick={onClearAll}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear All
          </button>
        </div>
        {resultCount !== undefined && totalCount !== undefined && (
          <span className="text-sm text-gray-600">
            Showing {resultCount} of {totalCount} workflows
          </span>
        )}
      </div>
    </div>
  );
}