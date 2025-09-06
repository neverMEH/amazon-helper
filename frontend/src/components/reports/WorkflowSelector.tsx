import { useState, useMemo, useRef, useEffect } from 'react';
import { Search, ChevronDown, FileText } from 'lucide-react';

interface Workflow {
  id: string;
  workflow_id: string;
  name: string;
  description?: string;
  instance_name?: string;
  last_executed?: string;
}

interface WorkflowSelectorProps {
  workflows: Workflow[];
  value: string;
  onChange: (workflowId: string) => void;
  placeholder?: string;
}

export default function WorkflowSelector({
  workflows,
  value,
  onChange,
  placeholder = "Search and select a workflow..."
}: WorkflowSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter workflows based on search query
  const filteredWorkflows = useMemo(() => {
    if (!searchQuery) return workflows;
    
    const query = searchQuery.toLowerCase();
    return workflows.filter(workflow => {
      // Search by workflow name
      if (workflow.name?.toLowerCase().includes(query)) return true;
      
      // Search by workflow ID
      if (workflow.workflow_id?.toLowerCase().includes(query)) return true;
      
      // Search by description
      if (workflow.description?.toLowerCase().includes(query)) return true;
      
      // Search by instance name
      if (workflow.instance_name?.toLowerCase().includes(query)) return true;
      
      return false;
    });
  }, [workflows, searchQuery]);

  // Get selected workflow
  const selectedWorkflow = workflows.find(w => w.id === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSelect = (workflowId: string) => {
    onChange(workflowId);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div ref={dropdownRef} className="relative">
      {/* Selected Value Display */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full px-3 py-2 text-left border rounded-md 
          ${isOpen ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-300'}
          bg-white hover:bg-gray-50 transition-colors
          flex items-center justify-between
        `}
      >
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
          {selectedWorkflow ? (
            <div className="min-w-0">
              <div className="font-medium text-gray-900 truncate">
                {selectedWorkflow.name}
              </div>
              <div className="text-xs text-gray-500 truncate">
                {selectedWorkflow.workflow_id}
              </div>
            </div>
          ) : (
            <span className="text-gray-500">{placeholder}</span>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 w-4 h-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search workflows..."
                className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Workflow List */}
          <div className="max-h-60 overflow-y-auto">
            {filteredWorkflows.length > 0 ? (
              filteredWorkflows.map(workflow => (
                <button
                  key={workflow.id}
                  onClick={() => handleSelect(workflow.id)}
                  className={`
                    w-full px-3 py-2 text-left hover:bg-gray-50
                    ${workflow.id === value ? 'bg-blue-50' : ''}
                    border-b border-gray-100 last:border-b-0
                  `}
                >
                  <div className="flex items-start gap-2">
                    <FileText className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900">
                        {workflow.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        ID: {workflow.workflow_id}
                      </div>
                      {workflow.description && (
                        <div className="text-xs text-gray-600 mt-1 line-clamp-2">
                          {workflow.description}
                        </div>
                      )}
                      {workflow.last_executed && (
                        <div className="text-xs text-gray-400 mt-1">
                          Last run: {new Date(workflow.last_executed).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))
            ) : (
              <div className="px-3 py-4 text-sm text-gray-500 text-center">
                No workflows found
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}