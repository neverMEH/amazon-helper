import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, FileText, LayoutDashboard } from 'lucide-react';
import ExecutionsGrid from './ExecutionsGrid';
import DashboardsTable from './DashboardsTable';
import RunReportModal from './RunReportModal';
import AMCExecutionDetail from '../executions/AMCExecutionDetail';
import { reportService } from '../../services/reportService';
import type { Report } from '../../types/report';
import toast from 'react-hot-toast';

export default function ReportBuilder() {
  const [activeTab, setActiveTab] = useState<'reports' | 'dashboards'>('reports');
  const [showRunModal, setShowRunModal] = useState(false);
  const [showCreateCustom, setShowCreateCustom] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState<{ instanceId: string; executionId: string } | null>(null);

  // Fetch reports
  const { data: reportsData, isLoading: loadingReports, refetch: refetchReports } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportService.listReports(),
  });

  const reports = reportsData?.data || [];

  const handleCreateReport = () => {
    // Open modal without a template for custom report creation
    setShowCreateCustom(true);
    setShowRunModal(true);
    setActiveTab('reports');
  };

  const handleRunReport = async (reportConfig: any) => {
    console.log('Creating report with config:', reportConfig);
    try {
      const result = await reportService.createReport(reportConfig);
      console.log('Report created successfully:', result);
      toast.success('Report created successfully');
      setShowRunModal(false);
      setShowCreateCustom(false);
      refetchReports();
      setActiveTab('dashboards');
    } catch (error: any) {
      console.error('Failed to create report:', error);
      toast.error(error.response?.data?.detail || error.message || 'Failed to create report');
    }
  };

  const handleEditReport = () => {
    toast('Edit functionality coming soon', { icon: 'ℹ️' });
  };

  const handleDeleteReport = async (report: Report) => {
    if (!confirm('Are you sure you want to delete this report?')) return;

    try {
      await reportService.deleteReport(report.id);
      toast.success('Report deleted successfully');
      refetchReports();
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete report');
    }
  };

  const handleRunNow = async (report: Report) => {
    try {
      await reportService.runReport(report.id);
      toast.success('Report execution started');
      refetchReports();
    } catch (error: any) {
      toast.error(error.message || 'Failed to run report');
    }
  };

  const handlePauseReport = async (report: Report) => {
    try {
      await reportService.pauseReport(report.id);
      toast.success('Report paused');
      refetchReports();
    } catch (error: any) {
      toast.error(error.message || 'Failed to pause report');
    }
  };

  const handleResumeReport = async (report: Report) => {
    try {
      await reportService.resumeReport(report.id);
      toast.success('Report resumed');
      refetchReports();
    } catch (error: any) {
      toast.error(error.message || 'Failed to resume report');
    }
  };

  const handleViewResults = (report: Report) => {
    // Navigate to results view
    window.location.href = `/reports/${report.id}/results`;
  };

  const handleExecutionSelect = (execution: any) => {
    // Extract the instance ID and execution ID from the execution data
    const instanceId = execution.instanceInfo?.id || execution.instance_id;
    const executionId = execution.workflowExecutionId || execution.execution_id;

    if (instanceId && executionId) {
      setSelectedExecution({ instanceId, executionId });
    } else {
      toast.error('Unable to open execution details - missing instance or execution ID');
    }
  };

  const handleExecutionClose = () => {
    setSelectedExecution(null);
  };

  const handleExecutionRerun = (newExecutionId: string) => {
    // Update the selected execution to the new one after rerun
    if (selectedExecution) {
      setSelectedExecution({ ...selectedExecution, executionId: newExecutionId });
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Report Builder</h1>
            <p className="mt-1 text-sm text-gray-500">
              Create and manage automated reports from AMC query templates
            </p>
          </div>
          <button
            onClick={handleCreateReport}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600
                     hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Report
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 bg-white px-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('reports')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'reports'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center">
              <FileText className="h-4 w-4 mr-2" />
              Reports
            </div>
          </button>
          <button
            onClick={() => setActiveTab('dashboards')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'dashboards'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center">
              <LayoutDashboard className="h-4 w-4 mr-2" />
              Dashboards
            </div>
          </button>
        </nav>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto bg-gray-50">
        {activeTab === 'reports' ? (
          <div className="p-6">
            <ExecutionsGrid onSelect={handleExecutionSelect} />
          </div>
        ) : (
          <div className="p-6">
            <DashboardsTable
              reports={reports}
              isLoading={loadingReports}
              onEdit={handleEditReport}
              onDelete={handleDeleteReport}
              onRun={handleRunNow}
              onPause={handlePauseReport}
              onResume={handleResumeReport}
              onViewResults={handleViewResults}
            />
          </div>
        )}
      </div>

      {/* Run Report Modal */}
      {showRunModal && (
        <RunReportModal
          isOpen={showRunModal}
          onClose={() => {
            setShowRunModal(false);
            setShowCreateCustom(false);
          }}
          template={null}
          onSubmit={handleRunReport}
          includeTemplateStep={showCreateCustom}
        />
      )}

      {/* Execution Detail Modal */}
      {selectedExecution && (
        <AMCExecutionDetail
          instanceId={selectedExecution.instanceId}
          executionId={selectedExecution.executionId}
          onClose={handleExecutionClose}
          onRerunSuccess={handleExecutionRerun}
        />
      )}
    </div>
  );
}