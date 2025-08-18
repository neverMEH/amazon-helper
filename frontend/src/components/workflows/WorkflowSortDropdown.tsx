import { ChevronDown, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';

export type SortField = 'name' | 'lastExecuted' | 'createdAt' | 'updatedAt' | 'executionCount' | 'status';
export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  direction: SortDirection;
}

interface SortOption {
  value: string;
  label: string;
  field: SortField;
  direction: SortDirection;
}

interface WorkflowSortDropdownProps {
  value: SortConfig;
  onChange: (config: SortConfig) => void;
}

const sortOptions: SortOption[] = [
  { value: 'name-asc', label: 'Name (A → Z)', field: 'name', direction: 'asc' },
  { value: 'name-desc', label: 'Name (Z → A)', field: 'name', direction: 'desc' },
  { value: 'lastExecuted-desc', label: 'Last Run (Newest First)', field: 'lastExecuted', direction: 'desc' },
  { value: 'lastExecuted-asc', label: 'Last Run (Oldest First)', field: 'lastExecuted', direction: 'asc' },
  { value: 'created-desc', label: 'Created (Newest First)', field: 'createdAt', direction: 'desc' },
  { value: 'created-asc', label: 'Created (Oldest First)', field: 'createdAt', direction: 'asc' },
  { value: 'updated-desc', label: 'Updated (Recently Modified)', field: 'updatedAt', direction: 'desc' },
  { value: 'updated-asc', label: 'Updated (Least Recently)', field: 'updatedAt', direction: 'asc' },
  { value: 'execCount-desc', label: 'Most Executed', field: 'executionCount', direction: 'desc' },
  { value: 'execCount-asc', label: 'Least Executed', field: 'executionCount', direction: 'asc' },
  { value: 'status-asc', label: 'Status (A → Z)', field: 'status', direction: 'asc' },
  { value: 'status-desc', label: 'Status (Z → A)', field: 'status', direction: 'desc' },
];

export default function WorkflowSortDropdown({ value, onChange }: WorkflowSortDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentOption = sortOptions.find(
    opt => opt.field === value.field && opt.direction === value.direction
  ) || sortOptions[6]; // Default to "Updated (Recently Modified)"

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (option: SortOption) => {
    onChange({ field: option.field, direction: option.direction });
    setIsOpen(false);
  };

  const getIcon = (field: SortField, direction: SortDirection) => {
    if (field === value.field && direction === value.direction) {
      return direction === 'asc' 
        ? <ArrowUp className="h-3 w-3" />
        : <ArrowDown className="h-3 w-3" />;
    }
    return null;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <ArrowUpDown className="h-4 w-4 mr-2 text-gray-400" />
        <span>Sort: {currentOption.label}</span>
        <ChevronDown className="h-4 w-4 ml-2 text-gray-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 z-10 mt-2 w-64 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <div className="py-1" role="listbox">
            {sortOptions.map((option) => {
              const isSelected = option.field === value.field && option.direction === value.direction;
              return (
                <button
                  key={option.value}
                  onClick={() => handleSelect(option)}
                  className={`${
                    isSelected
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  } group flex items-center justify-between w-full px-4 py-2 text-sm`}
                  role="option"
                  aria-selected={isSelected}
                >
                  <span className="flex items-center">
                    {option.label}
                  </span>
                  {getIcon(option.field, option.direction)}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}