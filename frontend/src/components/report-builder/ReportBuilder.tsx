import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Plus, FileText, LayoutDashboard, Sparkles, ChevronRight, ChevronLeft, Lightbulb, TrendingUp, Target, Zap } from 'lucide-react';
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
  const [showAIAssistant, setShowAIAssistant] = useState(true);

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

      {/* Content Area with AI Assistant */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main Content */}
        <div className={`flex-1 overflow-auto bg-gray-50 transition-all duration-300 ${showAIAssistant ? 'mr-80' : 'mr-0'}`}>
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

        {/* AI Assistant Side Panel */}
        <div className={`fixed right-0 top-0 bottom-0 w-80 bg-white border-l border-gray-200 shadow-lg transform transition-transform duration-300 ${
          showAIAssistant ? 'translate-x-0' : 'translate-x-full'
        } z-30`}>
          {/* Toggle Button */}
          <button
            onClick={() => setShowAIAssistant(!showAIAssistant)}
            className="absolute -left-10 top-1/2 transform -translate-y-1/2 bg-indigo-600 text-white p-2 rounded-l-lg hover:bg-indigo-700 shadow-lg"
          >
            {showAIAssistant ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </button>

          {/* AI Assistant Content */}
          <div className="h-full flex flex-col">
            {/* Header */}
            <div className="px-4 py-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
              <div className="flex items-center space-x-2">
                <Sparkles className="h-5 w-5 text-indigo-600" />
                <h3 className="text-lg font-semibold text-gray-900">AI Assistant</h3>
              </div>
              <p className="mt-1 text-xs text-gray-600">Get intelligent suggestions for your reports</p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Quick Tips */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <Lightbulb className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-blue-900">Quick Tips</h4>
                    <ul className="mt-2 text-xs text-blue-700 space-y-1.5">
                      <li className="flex items-start">
                        <span className="mr-1">•</span>
                        <span>Use date parameters for flexible time-range reports</span>
                      </li>
                      <li className="flex items-start">
                        <span className="mr-1">•</span>
                        <span>Schedule reports to run automatically on a cadence</span>
                      </li>
                      <li className="flex items-start">
                        <span className="mr-1">•</span>
                        <span>Export results to Snowflake for long-term storage</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Smart Suggestions */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                  <TrendingUp className="h-4 w-4 mr-1.5 text-indigo-600" />
                  Smart Suggestions
                </h4>
                <div className="space-y-2">
                  <div className="bg-white border border-gray-200 rounded-lg p-3 hover:border-indigo-300 transition-colors cursor-pointer">
                    <div className="flex items-start space-x-2">
                      <Target className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Performance Optimization</p>
                        <p className="text-xs text-gray-600 mt-1">Add LIMIT clauses to improve query speed</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-3 hover:border-indigo-300 transition-colors cursor-pointer">
                    <div className="flex items-start space-x-2">
                      <Zap className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Data Freshness</p>
                        <p className="text-xs text-gray-600 mt-1">AMC data has a 14-day lag - adjust date ranges accordingly</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-3 hover:border-indigo-300 transition-colors cursor-pointer">
                    <div className="flex items-start space-x-2">
                      <Sparkles className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Best Practice</p>
                        <p className="text-xs text-gray-600 mt-1">Use incremental backfills for historical analysis</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Common Report Templates */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                  <FileText className="h-4 w-4 mr-1.5 text-indigo-600" />
                  Popular Templates
                </h4>
                <div className="space-y-2">
                  <button className="w-full text-left bg-white border border-gray-200 rounded-lg p-3 hover:border-indigo-300 hover:bg-indigo-50 transition-colors">
                    <p className="text-sm font-medium text-gray-900">Campaign Performance</p>
                    <p className="text-xs text-gray-600 mt-1">Track ROAS, impressions, and conversions</p>
                  </button>

                  <button className="w-full text-left bg-white border border-gray-200 rounded-lg p-3 hover:border-indigo-300 hover:bg-indigo-50 transition-colors">
                    <p className="text-sm font-medium text-gray-900">Attribution Analysis</p>
                    <p className="text-xs text-gray-600 mt-1">Understand customer journey touchpoints</p>
                  </button>

                  <button className="w-full text-left bg-white border border-gray-200 rounded-lg p-3 hover:border-indigo-300 hover:bg-indigo-50 transition-colors">
                    <p className="text-sm font-medium text-gray-900">Audience Insights</p>
                    <p className="text-xs text-gray-600 mt-1">Analyze demographic and behavioral patterns</p>
                  </button>
                </div>
              </div>
            </div>

            {/* Footer CTA */}
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <button
                onClick={handleCreateReport}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create New Report
              </button>
            </div>
          </div>
        </div>
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
          isOpen={!!selectedExecution}
          instanceId={selectedExecution.instanceId}
          executionId={selectedExecution.executionId}
          onClose={handleExecutionClose}
          onRerunSuccess={handleExecutionRerun}
        />
      )}
    </div>
  );
}