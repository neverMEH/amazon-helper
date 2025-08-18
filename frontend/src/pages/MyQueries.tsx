import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Plus, 
  Search, 
  Eye, 
  Edit2, 
  Trash2, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Calendar,
  Cloud,
  CloudOff,
  Copy,
  Filter,
  ArrowUpDown
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import api from '../services/api';
import { formatDistanceToNow, isAfter, isBefore, parseISO } from 'date-fns';
import WorkflowSortDropdown, { type SortConfig } from '../components/workflows/WorkflowSortDropdown';
import WorkflowFilters, { type WorkflowFiltersConfig } from '../components/workflows/WorkflowFilters';
import ActiveFilterBadges, { type FilterBadge } from '../components/workflows/ActiveFilterBadges';

interface Workflow {
  id: string;
  workflowId: string;
  name: string;
  description?: string;
  sqlQuery: string;
  status: string;
  instance?: {
    id: string;
    instanceId: string;
    instanceName: string;
  };
  parameters?: any;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
  lastExecutedAt?: string;
  executionCount?: number;
  amcWorkflowId?: string;
  isSyncedToAmc?: boolean;
  amcSyncStatus?: string;
}

// Default filter configuration
const defaultFilters: WorkflowFiltersConfig = {
  status: [],
  instanceIds: [],
  syncStatus: 'all',
  tags: [],
  dateRange: {
    field: 'createdAt',
    from: null,
    to: null
  },
  executionCountRange: {
    min: null,
    max: null
  }
};

// Default sort configuration
const defaultSort: SortConfig = {
  field: 'updatedAt',
  direction: 'desc'
};

export default function MyQueries() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<WorkflowFiltersConfig>(defaultFilters);
  const [sortConfig, setSortConfig] = useState<SortConfig>(defaultSort);
  const [showFilterSidebar, setShowFilterSidebar] = useState(false);
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Load saved preferences from localStorage
  useEffect(() => {
    const savedFilters = localStorage.getItem('workflowFilters');
    const savedSort = localStorage.getItem('workflowSort');
    
    if (savedFilters) {
      try {
        setFilters(JSON.parse(savedFilters));
      } catch (e) {
        console.error('Failed to parse saved filters:', e);
      }
    }
    
    if (savedSort) {
      try {
        setSortConfig(JSON.parse(savedSort));
      } catch (e) {
        console.error('Failed to parse saved sort:', e);
      }
    }
  }, []);

  // Save preferences to localStorage
  useEffect(() => {
    localStorage.setItem('workflowFilters', JSON.stringify(filters));
  }, [filters]);

  useEffect(() => {
    localStorage.setItem('workflowSort', JSON.stringify(sortConfig));
  }, [sortConfig]);

  // Fetch workflows
  const { data: workflows = [], isLoading } = useQuery<Workflow[]>({
    queryKey: ['workflows'],
    queryFn: async () => {
      const response = await api.get('/workflows');
      return response.data;
    }
  });

  // Delete workflow mutation
  const deleteMutation = useMutation({
    mutationFn: async (workflowId: string) => {
      await api.delete(`/workflows/${workflowId}`);
    },
    onSuccess: () => {
      toast.success('Workflow deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: () => {
      toast.error('Failed to delete workflow');
    }
  });


  // Extract unique instances and tags for filter options
  const availableInstances = useMemo(() => {
    const instanceMap = new Map();
    workflows.forEach(w => {
      if (w.instance) {
        instanceMap.set(w.instance.instanceId, {
          id: w.instance.id,
          instanceId: w.instance.instanceId,
          name: w.instance.instanceName || w.instance.name || 'Unknown'
        });
      }
    });
    return Array.from(instanceMap.values());
  }, [workflows]);

  const availableTags = useMemo(() => {
    const tagSet = new Set<string>();
    workflows.forEach(w => {
      if (w.tags) {
        w.tags.forEach(tag => tagSet.add(tag));
      }
    });
    return Array.from(tagSet).sort();
  }, [workflows]);

  // Apply filters
  const applyFilters = useCallback((workflows: Workflow[], filters: WorkflowFiltersConfig, search: string) => {
    return workflows.filter(workflow => {
      // Search filter
      if (search && 
          !workflow.name.toLowerCase().includes(search.toLowerCase()) &&
          !workflow.description?.toLowerCase().includes(search.toLowerCase())) {
        return false;
      }

      // Status filter
      if (filters.status.length > 0 && !filters.status.includes(workflow.status)) {
        return false;
      }

      // Instance filter
      if (filters.instanceIds.length > 0 && 
          (!workflow.instance || !filters.instanceIds.includes(workflow.instance.instanceId))) {
        return false;
      }

      // Sync status filter
      if (filters.syncStatus !== 'all') {
        const isSynced = workflow.isSyncedToAmc;
        if (filters.syncStatus === 'synced' && !isSynced) return false;
        if (filters.syncStatus === 'not_synced' && isSynced) return false;
      }

      // Tags filter
      if (filters.tags.length > 0) {
        if (!workflow.tags || !filters.tags.some(tag => workflow.tags?.includes(tag))) {
          return false;
        }
      }

      // Date range filter
      if (filters.dateRange.from || filters.dateRange.to) {
        const dateField = filters.dateRange.field;
        const workflowDate = workflow[dateField];
        
        if (workflowDate) {
          const date = parseISO(workflowDate);
          
          if (filters.dateRange.from && isBefore(date, parseISO(filters.dateRange.from))) {
            return false;
          }
          
          if (filters.dateRange.to) {
            const endOfDay = new Date(filters.dateRange.to);
            endOfDay.setHours(23, 59, 59, 999);
            if (isAfter(date, endOfDay)) {
              return false;
            }
          }
        } else if (filters.dateRange.from) {
          // If date field is empty but filter requires a date, exclude
          return false;
        }
      }

      // Execution count filter
      if (filters.executionCountRange.min !== null || filters.executionCountRange.max !== null) {
        const count = workflow.executionCount || 0;
        
        if (filters.executionCountRange.min !== null && count < filters.executionCountRange.min) {
          return false;
        }
        
        if (filters.executionCountRange.max !== null && count > filters.executionCountRange.max) {
          return false;
        }
      }

      return true;
    });
  }, []);

  // Apply sorting
  const sortWorkflows = useCallback((workflows: Workflow[], sortConfig: SortConfig) => {
    const sorted = [...workflows].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortConfig.field) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'lastExecuted':
          aValue = a.lastExecutedAt ? new Date(a.lastExecutedAt).getTime() : 0;
          bValue = b.lastExecutedAt ? new Date(b.lastExecutedAt).getTime() : 0;
          break;
        case 'createdAt':
          aValue = new Date(a.createdAt).getTime();
          bValue = new Date(b.createdAt).getTime();
          break;
        case 'updatedAt':
          aValue = new Date(a.updatedAt).getTime();
          bValue = new Date(b.updatedAt).getTime();
          break;
        case 'executionCount':
          aValue = a.executionCount || 0;
          bValue = b.executionCount || 0;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, []);

  // Process workflows with filters and sorting
  const processedWorkflows = useMemo(() => {
    let result = workflows;
    result = applyFilters(result, filters, debouncedSearch);
    result = sortWorkflows(result, sortConfig);
    return result;
  }, [workflows, filters, debouncedSearch, sortConfig, applyFilters, sortWorkflows]);

  // Generate filter badges
  const filterBadges = useMemo((): FilterBadge[] => {
    const badges: FilterBadge[] = [];

    // Status badges
    filters.status.forEach(status => {
      badges.push({
        key: `status-${status}`,
        label: 'Status',
        value: status.charAt(0).toUpperCase() + status.slice(1),
        onRemove: () => setFilters(prev => ({
          ...prev,
          status: prev.status.filter(s => s !== status)
        }))
      });
    });

    // Instance badges
    filters.instanceIds.forEach(instanceId => {
      const instance = availableInstances.find(i => i.instanceId === instanceId);
      if (instance) {
        badges.push({
          key: `instance-${instanceId}`,
          label: 'Instance',
          value: instance.name,
          onRemove: () => setFilters(prev => ({
            ...prev,
            instanceIds: prev.instanceIds.filter(id => id !== instanceId)
          }))
        });
      }
    });

    // Sync status badge
    if (filters.syncStatus !== 'all') {
      badges.push({
        key: 'sync-status',
        label: 'Sync',
        value: filters.syncStatus === 'synced' ? 'Synced' : 'Not Synced',
        onRemove: () => setFilters(prev => ({ ...prev, syncStatus: 'all' }))
      });
    }

    // Tag badges
    filters.tags.forEach(tag => {
      badges.push({
        key: `tag-${tag}`,
        label: 'Tag',
        value: tag,
        onRemove: () => setFilters(prev => ({
          ...prev,
          tags: prev.tags.filter(t => t !== tag)
        }))
      });
    });

    // Date range badge
    if (filters.dateRange.from || filters.dateRange.to) {
      const label = filters.dateRange.field === 'createdAt' ? 'Created' : 
                    filters.dateRange.field === 'updatedAt' ? 'Updated' : 'Last Run';
      const value = `${filters.dateRange.from || '...'} to ${filters.dateRange.to || '...'}`;
      badges.push({
        key: 'date-range',
        label,
        value,
        onRemove: () => setFilters(prev => ({
          ...prev,
          dateRange: { ...prev.dateRange, from: null, to: null }
        }))
      });
    }

    // Execution count badge
    if (filters.executionCountRange.min !== null || filters.executionCountRange.max !== null) {
      const value = `${filters.executionCountRange.min || 0} - ${filters.executionCountRange.max || '∞'} executions`;
      badges.push({
        key: 'exec-count',
        label: 'Executions',
        value,
        onRemove: () => setFilters(prev => ({
          ...prev,
          executionCountRange: { min: null, max: null }
        }))
      });
    }

    return badges;
  }, [filters, availableInstances]);

  const clearAllFilters = () => {
    setFilters(defaultFilters);
    setSearchQuery('');
  };

  const handleEdit = (workflowId: string) => {
    navigate(`/query-builder/edit/${workflowId}`);
  };

  const handleView = (workflowId: string) => {
    navigate(`/workflows/${workflowId}`);
  };

  const handleDelete = async (workflowId: string) => {
    if (confirm('Are you sure you want to delete this workflow?')) {
      await deleteMutation.mutateAsync(workflowId);
    }
  };

  const handleSchedule = () => {
    // TODO: Open schedule modal
    toast('Schedule feature coming soon', {
      icon: 'ℹ️'
    });
  };

  const handleCopy = (workflowId: string) => {
    // Navigate to query builder with copy mode
    navigate(`/query-builder/copy/${workflowId}`);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'draft':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'archived':
        return <XCircle className="h-4 w-4 text-gray-400" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getSyncIcon = (workflow: Workflow) => {
    if (workflow.isSyncedToAmc) {
      return (
        <span title="Synced to AMC">
          <Cloud className="h-4 w-4 text-blue-500" />
        </span>
      );
    }
    return (
      <span title="Not synced to AMC">
        <CloudOff className="h-4 w-4 text-gray-400" />
      </span>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Workflows</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage and execute your saved AMC workflows
            </p>
          </div>
          <button
            onClick={() => navigate('/query-builder/new')}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Workflow
          </button>
        </div>
      </div>

      {/* Search, Sort and Filter Bar */}
      <div className="mb-6">
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search workflows by name or description..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <WorkflowSortDropdown 
              value={sortConfig}
              onChange={setSortConfig}
            />
            <button
              onClick={() => setShowFilterSidebar(!showFilterSidebar)}
              className={`inline-flex items-center px-3 py-2 border ${
                filterBadges.length > 0 
                  ? 'border-blue-500 text-blue-700 bg-blue-50' 
                  : 'border-gray-300 text-gray-700 bg-white'
              } text-sm font-medium rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filters
              {filterBadges.length > 0 && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-600 text-white">
                  {filterBadges.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Active Filter Badges */}
      <ActiveFilterBadges
        badges={filterBadges}
        onClearAll={clearAllFilters}
        resultCount={processedWorkflows.length}
        totalCount={workflows.length}
      />

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading queries...</div>
        </div>
      )}

      {/* Queries Table */}
      {!isLoading && processedWorkflows.length > 0 && (
        <div className="bg-white shadow overflow-hidden rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Query Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Instance
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Run
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sync
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {processedWorkflows.map((workflow) => (
                <tr 
                  key={workflow.id} 
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={(e) => {
                    // Don't navigate if clicking on action buttons
                    const target = e.target as HTMLElement;
                    if (!target.closest('button') && !target.closest('.actions-cell')) {
                      handleView(workflow.workflowId);
                    }
                  }}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {workflow.name}
                      </div>
                      {workflow.description && (
                        <div className="text-xs text-gray-500 truncate max-w-xs">
                          {workflow.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">
                      {workflow.instance?.instanceName || '-'}
                    </div>
                    <div className="text-xs text-gray-500">
                      {workflow.instance?.instanceId}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(workflow.status)}
                      <span className="ml-2 text-sm text-gray-900 capitalize">
                        {workflow.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {workflow.lastExecutedAt ? (
                      <div className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatDistanceToNow(new Date(workflow.lastExecutedAt), { addSuffix: true })}
                      </div>
                    ) : (
                      'Never'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getSyncIcon(workflow)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium actions-cell">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => handleView(workflow.workflowId)}
                        className="text-blue-600 hover:text-blue-900"
                        title="View"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEdit(workflow.workflowId)}
                        className="text-gray-600 hover:text-gray-900"
                        title="Edit"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleCopy(workflow.workflowId)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Copy"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleSchedule()}
                        className="text-gray-600 hover:text-gray-900"
                        title="Schedule"
                      >
                        <Calendar className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(workflow.workflowId)}
                        disabled={deleteMutation.isPending}
                        className="text-red-600 hover:text-red-900"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && processedWorkflows.length === 0 && (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No workflows found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery || filterBadges.length > 0
              ? 'Try adjusting your search or filter criteria'
              : 'Get started by creating your first workflow'}
          </p>
          <div className="mt-6">
            <button
              onClick={() => navigate('/query-builder/new')}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create New Workflow
            </button>
          </div>
        </div>
      )}

      {/* Filter Sidebar */}
      <WorkflowFilters
        filters={filters}
        onChange={setFilters}
        availableInstances={availableInstances}
        availableTags={availableTags}
        isOpen={showFilterSidebar}
        onClose={() => setShowFilterSidebar(false)}
      />
    </div>
  );
}