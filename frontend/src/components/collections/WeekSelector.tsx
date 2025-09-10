import React, { useState, useMemo, useCallback } from 'react';
import { CalendarIcon, CheckIcon } from '@heroicons/react/24/outline';
import type { WeekData } from '../../services/reportDashboardService';

interface WeekSelectorProps {
  weeks: WeekData[];
  selectedWeeks: string[];
  onSelectionChange: (weeks: string[]) => void;
  multiSelect?: boolean;
  groupBy?: 'week' | 'month' | 'quarter';
  className?: string;
}

interface WeekGroup {
  label: string;
  weeks: WeekData[];
  allSelected: boolean;
  someSelected: boolean;
}

const WeekSelector: React.FC<WeekSelectorProps> = ({
  weeks,
  selectedWeeks,
  onSelectionChange,
  multiSelect = false,
  groupBy = 'month',
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Group weeks by period
  const groupedWeeks = useMemo(() => {
    const groups: Record<string, WeekData[]> = {};

    weeks.forEach((week) => {
      const date = new Date(week.week_start);
      let groupKey: string;

      switch (groupBy) {
        case 'quarter':
          const quarter = Math.floor(date.getMonth() / 3) + 1;
          groupKey = `Q${quarter} ${date.getFullYear()}`;
          break;
        case 'month':
          groupKey = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
          break;
        case 'week':
        default:
          groupKey = 'All Weeks';
          break;
      }

      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(week);
    });

    // Convert to array and calculate selection state
    return Object.entries(groups).map(([label, groupWeeks]) => {
      const selectedInGroup = groupWeeks.filter((w) =>
        selectedWeeks.includes(w.id)
      );
      return {
        label,
        weeks: groupWeeks,
        allSelected: selectedInGroup.length === groupWeeks.length,
        someSelected: selectedInGroup.length > 0 && selectedInGroup.length < groupWeeks.length,
      };
    });
  }, [weeks, selectedWeeks, groupBy]);

  // Filter weeks based on search
  const filteredGroups = useMemo(() => {
    if (!searchTerm) return groupedWeeks;

    return groupedWeeks
      .map((group) => ({
        ...group,
        weeks: group.weeks.filter((week) => {
          const weekLabel = `Week ${week.week_number}`;
          const dateRange = `${new Date(week.week_start).toLocaleDateString()} - ${new Date(
            week.week_end
          ).toLocaleDateString()}`;
          return (
            weekLabel.toLowerCase().includes(searchTerm.toLowerCase()) ||
            dateRange.toLowerCase().includes(searchTerm.toLowerCase())
          );
        }),
      }))
      .filter((group) => group.weeks.length > 0);
  }, [groupedWeeks, searchTerm]);

  // Handle week selection
  const handleWeekToggle = useCallback(
    (weekId: string) => {
      if (multiSelect) {
        const newSelection = selectedWeeks.includes(weekId)
          ? selectedWeeks.filter((id) => id !== weekId)
          : [...selectedWeeks, weekId];
        onSelectionChange(newSelection);
      } else {
        onSelectionChange([weekId]);
        setIsOpen(false);
      }
    },
    [selectedWeeks, onSelectionChange, multiSelect]
  );

  // Handle group selection
  const handleGroupToggle = useCallback(
    (group: WeekGroup) => {
      if (!multiSelect) return;

      const groupWeekIds = group.weeks.map((w) => w.id);
      let newSelection: string[];

      if (group.allSelected) {
        // Deselect all in group
        newSelection = selectedWeeks.filter((id) => !groupWeekIds.includes(id));
      } else {
        // Select all in group
        const toAdd = groupWeekIds.filter((id) => !selectedWeeks.includes(id));
        newSelection = [...selectedWeeks, ...toAdd];
      }

      onSelectionChange(newSelection);
    },
    [selectedWeeks, onSelectionChange, multiSelect]
  );

  // Handle select all/none
  const handleSelectAll = useCallback(() => {
    onSelectionChange(weeks.map((w) => w.id));
  }, [weeks, onSelectionChange]);

  const handleSelectNone = useCallback(() => {
    onSelectionChange([]);
  }, [onSelectionChange]);

  // Handle preset selections
  const handlePresetSelection = useCallback(
    (preset: 'last4' | 'last12' | 'last26' | 'all') => {
      const sortedWeeks = [...weeks].sort(
        (a, b) => new Date(b.week_start).getTime() - new Date(a.week_start).getTime()
      );

      let selection: WeekData[];
      switch (preset) {
        case 'last4':
          selection = sortedWeeks.slice(0, 4);
          break;
        case 'last12':
          selection = sortedWeeks.slice(0, 12);
          break;
        case 'last26':
          selection = sortedWeeks.slice(0, 26);
          break;
        case 'all':
        default:
          selection = weeks;
          break;
      }

      onSelectionChange(selection.map((w) => w.id));
    },
    [weeks, onSelectionChange]
  );

  // Get display text
  const displayText = useMemo(() => {
    if (selectedWeeks.length === 0) {
      return 'Select weeks';
    }
    if (selectedWeeks.length === 1) {
      const week = weeks.find((w) => w.id === selectedWeeks[0]);
      return week ? `Week ${week.week_number}` : 'Select weeks';
    }
    return `${selectedWeeks.length} weeks selected`;
  }, [selectedWeeks, weeks]);

  return (
    <div className={`relative ${className}`}>
      <label htmlFor="week-selector" className="block text-sm font-medium text-gray-700 mb-1">
        Select Weeks
      </label>
      
      {/* Dropdown trigger */}
      <button
        id="week-selector"
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative w-full bg-white border border-gray-300 rounded-md shadow-sm pl-3 pr-10 py-2 text-left cursor-pointer focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="flex items-center">
          <CalendarIcon className="h-5 w-5 text-gray-400 mr-2" />
          <span className="block truncate">{displayText}</span>
        </span>
        <span className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
          <svg
            className="h-5 w-5 text-gray-400"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 011.414 0L10 14.586l2.293-2.293a1 1 0 011.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </span>
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-96 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
          {/* Search input */}
          <div className="sticky top-0 bg-white px-3 py-2 border-b border-gray-200">
            <input
              type="text"
              className="w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="Search weeks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onClick={(e) => e.stopPropagation()}
            />
          </div>

          {/* Preset selections (only for multiselect) */}
          {multiSelect && (
            <div className="px-3 py-2 border-b border-gray-200">
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => handlePresetSelection('last4')}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Last 4 weeks
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetSelection('last12')}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Last 12 weeks
                </button>
                <button
                  type="button"
                  onClick={() => handlePresetSelection('last26')}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Last 26 weeks
                </button>
                <button
                  type="button"
                  onClick={handleSelectAll}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Select all
                </button>
                <button
                  type="button"
                  onClick={handleSelectNone}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Clear
                </button>
              </div>
            </div>
          )}

          {/* Week list */}
          <ul className="py-1">
            {filteredGroups.map((group) => (
              <li key={group.label}>
                {/* Group header */}
                {groupBy !== 'week' && (
                  <div
                    className="px-3 py-2 bg-gray-50 border-y border-gray-100 flex items-center justify-between cursor-pointer hover:bg-gray-100"
                    onClick={() => multiSelect && handleGroupToggle(group)}
                  >
                    <span className="text-sm font-medium text-gray-700">
                      {group.label}
                    </span>
                    {multiSelect && (
                      <div className="flex items-center">
                        <span className="text-xs text-gray-500 mr-2">
                          {group.weeks.filter((w) => selectedWeeks.includes(w.id)).length}/
                          {group.weeks.length}
                        </span>
                        {group.allSelected && (
                          <CheckIcon className="h-4 w-4 text-indigo-600" />
                        )}
                        {group.someSelected && !group.allSelected && (
                          <div className="h-4 w-4 bg-indigo-200 rounded" />
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Weeks in group */}
                {group.weeks.map((week) => {
                  const isSelected = selectedWeeks.includes(week.id);
                  const statusColor =
                    week.status === 'completed'
                      ? 'text-green-600'
                      : week.status === 'failed'
                      ? 'text-red-600'
                      : week.status === 'running'
                      ? 'text-blue-600'
                      : 'text-gray-400';

                  return (
                    <div
                      key={week.id}
                      className={`px-3 py-2 cursor-pointer hover:bg-gray-50 ${
                        isSelected ? 'bg-indigo-50' : ''
                      }`}
                      onClick={() => handleWeekToggle(week.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          {multiSelect && (
                            <input
                              type="checkbox"
                              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mr-3"
                              checked={isSelected}
                              onChange={() => {}}
                              onClick={(e) => e.stopPropagation()}
                            />
                          )}
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              Week {week.week_number}
                            </p>
                            <p className="text-xs text-gray-500">
                              {new Date(week.week_start).toLocaleDateString()} -{' '}
                              {new Date(week.week_end).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <span className={`text-xs font-medium ${statusColor}`}>
                          {week.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </li>
            ))}
          </ul>

          {filteredGroups.length === 0 && (
            <div className="px-3 py-4 text-center text-sm text-gray-500">
              No weeks found
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WeekSelector;