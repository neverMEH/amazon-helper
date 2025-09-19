import { useState, useMemo } from 'react';
import { format, parseISO } from 'date-fns';
import {
  Play,
  Pause,
  PlayCircle,
  Edit,
  Trash2,
  Eye,
  Search,
  ChevronUp,
  ChevronDown,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import type { Report } from '../../types/report';

interface DashboardsTableProps {
  reports: Report[];
  isLoading?: boolean;
  onEdit: (report: Report) => void;
  onDelete: (report: Report) => void;
  onRun: (report: Report) => void;
  onPause: (report: Report) => void;
  onResume: (report: Report) => void;
  onViewResults: (report: Report) => void;
}

type SortField = 'name' | 'status' | 'frequency' | 'last_run' | 'next_run' | 'success_rate';
type SortOrder = 'asc' | 'desc';

const statusIcons = {
  active: CheckCircle,
  paused: Pause,
  failed: XCircle,
  completed: CheckCircle,
};

const statusColors = {
  active: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
  failed: 'bg-red-100 text-red-800',
  completed: 'bg-blue-100 text-blue-800',
};

export default function DashboardsTable({
  reports,
  isLoading = false,
  onEdit,
  onDelete,
  onRun,
  onPause,
  onResume,
  onViewResults,
}: DashboardsTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // Filter and sort reports
  const processedReports = useMemo(() => {
    let filtered = [...reports];

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (report) =>
          report.name.toLowerCase().includes(search) ||
          report.description?.toLowerCase().includes(search)
      );
    }

    // Apply status filter
    if (statusFilter) {
      filtered = filtered.filter((report) => report.status === statusFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (sortField) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'frequency':
          aValue = a.frequency || '';
          bValue = b.frequency || '';
          break;
        case 'last_run':
          aValue = a.last_run_at ? new Date(a.last_run_at).getTime() : 0;
          bValue = b.last_run_at ? new Date(b.last_run_at).getTime() : 0;
          break;
        case 'next_run':
          aValue = a.next_run_at ? new Date(a.next_run_at).getTime() : 0;
          bValue = b.next_run_at ? new Date(b.next_run_at).getTime() : 0;
          break;
        case 'success_rate':
          aValue = a.execution_count ? (a.success_count || 0) / a.execution_count : 0;
          bValue = b.execution_count ? (b.success_count || 0) / b.execution_count : 0;
          break;
        default:
          aValue = a.name;
          bValue = b.name;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [reports, searchTerm, statusFilter, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };


  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-';
    try {
      return format(parseISO(dateString), 'MMM d, yyyy HH:mm');
    } catch {
      return '-';
    }
  };

  const calculateSuccessRate = (report: Report) => {
    if (!report.execution_count || report.execution_count === 0) return '-';
    const rate = ((report.success_count || 0) / report.execution_count) * 100;
    return `${rate.toFixed(1)}%`;
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <div className="w-4 h-4" />;
    }
    return sortOrder === 'asc' ? (
      <ChevronUp className="h-4 w-4" />
    ) : (
      <ChevronDown className="h-4 w-4" />
    );
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="flex items-center justify-center">
          <div className="text-gray-500">Loading reports...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search reports..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm
                         focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label htmlFor="status" className="sr-only">
              Status
            </label>
            <select
              id="status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="failed">Failed</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      {processedReports.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Clock className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No reports found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || statusFilter
              ? 'Try adjusting your filters'
              : 'Create your first report to get started'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    onClick={() => handleSort('name')}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-1">
                      Name
                      <SortIcon field="name" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('status')}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-1">
                      Status
                      <SortIcon field="status" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('frequency')}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-1">
                      Frequency
                      <SortIcon field="frequency" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('last_run')}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-1">
                      Last Run
                      <SortIcon field="last_run" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('next_run')}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-1">
                      Next Run
                      <SortIcon field="next_run" />
                    </div>
                  </th>
                  <th
                    onClick={() => handleSort('success_rate')}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  >
                    <div className="flex items-center gap-1">
                      Success Rate
                      <SortIcon field="success_rate" />
                    </div>
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {processedReports.map((report) => {
                  const StatusIcon = statusIcons[report.status];
                  const statusColor = statusColors[report.status];

                  return (
                    <tr key={report.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{report.name}</div>
                          {report.description && (
                            <div className="text-xs text-gray-500">{report.description}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${statusColor}`}
                        >
                          <StatusIcon className="h-3 w-3" />
                          {report.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {report.frequency || 'once'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDateTime(report.last_run_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {report.status === 'paused' ? '-' : formatDateTime(report.next_run_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {calculateSuccessRate(report)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => onRun(report)}
                            title="Run now"
                            className="p-1 text-indigo-600 hover:text-indigo-900 hover:bg-indigo-50 rounded"
                          >
                            <Play className="h-4 w-4" />
                          </button>
                          {report.status === 'active' ? (
                            <button
                              onClick={() => onPause(report)}
                              title="Pause schedule"
                              className="p-1 text-yellow-600 hover:text-yellow-900 hover:bg-yellow-50 rounded"
                            >
                              <Pause className="h-4 w-4" />
                            </button>
                          ) : report.status === 'paused' ? (
                            <button
                              onClick={() => onResume(report)}
                              title="Resume schedule"
                              className="p-1 text-green-600 hover:text-green-900 hover:bg-green-50 rounded"
                            >
                              <PlayCircle className="h-4 w-4" />
                            </button>
                          ) : null}
                          <button
                            onClick={() => onViewResults(report)}
                            title="View results"
                            className="p-1 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => onEdit(report)}
                            title="Edit report"
                            className="p-1 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => onDelete(report)}
                            title="Delete report"
                            className="p-1 text-red-600 hover:text-red-900 hover:bg-red-50 rounded"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}