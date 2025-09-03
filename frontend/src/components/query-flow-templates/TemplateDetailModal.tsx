import React, { useState, useEffect } from 'react';
import { X, Star, Heart, Play, Clock, TrendingUp, Users, Settings, BarChart3, AlertCircle } from 'lucide-react';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { queryFlowTemplateService } from '../../services/queryFlowTemplateService';
import { instanceService, type AMCInstance } from '../../services/instanceService';
import type { QueryFlowTemplate, ParameterFormValues } from '../../types/queryFlowTemplate';
import TemplateParameterForm from './TemplateParameterForm';
import SQLPreview from './SQLPreview';
import toast from 'react-hot-toast';

interface TemplateDetailModalProps {
  template: QueryFlowTemplate;
  isOpen: boolean;
  onClose: () => void;
}

const TemplateDetailModal: React.FC<TemplateDetailModalProps> = ({
  template,
  isOpen,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'parameters' | 'sql' | 'charts'>('overview');
  const [parameterValues, setParameterValues] = useState<ParameterFormValues>({});
  const [parameterErrors, setParameterErrors] = useState<Record<string, string>>({});
  const [isParameterFormValid, setIsParameterFormValid] = useState(false);
  const [selectedInstance, setSelectedInstance] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState(false);

  const queryClient = useQueryClient();

  // Fetch user's instances
  const { data: instances } = useQuery<AMCInstance[]>({
    queryKey: ['instances'],
    queryFn: instanceService.list,
    staleTime: 5 * 60 * 1000
  });

  // Toggle favorite mutation
  const favoriteMutation = useMutation({
    mutationFn: () => queryFlowTemplateService.toggleFavorite(template.template_id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['queryFlowTemplates'] });
      toast.success(data.message);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update favorite status');
    }
  });

  // Execute template mutation
  const executeMutation = useMutation({
    mutationFn: (data: { instanceId: string; parameters: ParameterFormValues }) =>
      queryFlowTemplateService.executeTemplate(template.template_id, {
        instance_id: data.instanceId,
        parameters: data.parameters
      }),
    onSuccess: (data) => {
      toast.success('Template execution started successfully');
      // Navigate to execution details
      window.location.href = `/executions/${data.execution_id}`;
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to execute template');
    }
  });

  // Set default instance on load
  useEffect(() => {
    if (instances && instances.length > 0 && !selectedInstance) {
      setSelectedInstance(instances[0].id);
    }
  }, [instances, selectedInstance]);

  // Reset form when template changes
  useEffect(() => {
    setParameterValues({});
    setParameterErrors({});
    setActiveTab('overview');
  }, [template.id]);

  const handleExecuteTemplate = async () => {
    if (!selectedInstance) {
      toast.error('Please select an AMC instance');
      return;
    }

    if (!isParameterFormValid) {
      toast.error('Please fix parameter validation errors');
      setActiveTab('parameters');
      return;
    }

    setIsExecuting(true);
    try {
      await executeMutation.mutateAsync({
        instanceId: selectedInstance,
        parameters: parameterValues
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleToggleFavorite = () => {
    favoriteMutation.mutate();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-gray-200">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h2 className="text-xl font-bold text-gray-900">{template.name}</h2>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs font-medium">
                {template.category}
              </span>
              <button
                onClick={handleToggleFavorite}
                disabled={favoriteMutation.isPending}
                className={`p-1 rounded-full transition-colors ${
                  template.is_favorite
                    ? 'text-red-500 hover:text-red-600'
                    : 'text-gray-400 hover:text-red-500'
                }`}
              >
                <Heart className={`h-5 w-5 ${template.is_favorite ? 'fill-current' : ''}`} />
              </button>
            </div>
            
            <p className="text-gray-600 mb-3">{template.description}</p>
            
            <div className="flex items-center space-x-6 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <TrendingUp className="h-4 w-4" />
                <span>{template.execution_count} executions</span>
              </div>
              
              {template.rating_info && template.rating_info.rating_count > 0 && (
                <div className="flex items-center space-x-1">
                  <Star className="h-4 w-4 text-yellow-400 fill-current" />
                  <span>{template.rating_info.avg_rating.toFixed(1)} ({template.rating_info.rating_count} reviews)</span>
                </div>
              )}
              
              <div className="flex items-center space-x-1">
                <BarChart3 className="h-4 w-4" />
                <span>{template.chart_configs?.length || 0} visualizations</span>
              </div>
              
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4" />
                <span>Updated {formatDate(template.updated_at)}</span>
              </div>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { key: 'overview', label: 'Overview', icon: Users },
              { key: 'parameters', label: 'Parameters', icon: Settings },
              { key: 'sql', label: 'SQL Preview', icon: BarChart3 },
              { key: 'charts', label: 'Visualizations', icon: BarChart3 }
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === key
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
                {key === 'parameters' && Object.keys(parameterErrors).length > 0 && (
                  <AlertCircle className="h-3 w-3 text-red-500" />
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Template Details */}
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Template Information</h3>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Version:</dt>
                      <dd className="text-gray-900">v{template.version}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Parameters:</dt>
                      <dd className="text-gray-900">{template.parameters?.length || 0}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Charts:</dt>
                      <dd className="text-gray-900">{template.chart_configs?.length || 0}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Created:</dt>
                      <dd className="text-gray-900">{formatDate(template.created_at)}</dd>
                    </div>
                  </dl>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Usage Statistics</h3>
                  <dl className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-gray-500">Total Runs:</dt>
                      <dd className="text-gray-900">{template.execution_count.toLocaleString()}</dd>
                    </div>
                    {template.avg_execution_time_ms && (
                      <div className="flex justify-between">
                        <dt className="text-gray-500">Avg Runtime:</dt>
                        <dd className="text-gray-900">{Math.round(template.avg_execution_time_ms / 1000)}s</dd>
                      </div>
                    )}
                    {template.rating_info && (
                      <>
                        <div className="flex justify-between">
                          <dt className="text-gray-500">Rating:</dt>
                          <dd className="text-gray-900">{template.rating_info.avg_rating.toFixed(1)}/5</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-500">Reviews:</dt>
                          <dd className="text-gray-900">{template.rating_info.rating_count}</dd>
                        </div>
                      </>
                    )}
                  </dl>
                </div>
              </div>

              {/* Tags */}
              {template.tags && template.tags.length > 0 && (
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {template.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'parameters' && (
            <TemplateParameterForm
              template={template}
              values={parameterValues}
              onChange={setParameterValues}
              onValidationChange={setIsParameterFormValid}
              disabled={isExecuting}
            />
          )}

          {activeTab === 'sql' && (
            <SQLPreview
              templateId={template.template_id}
              parameters={parameterValues}
            />
          )}

          {activeTab === 'charts' && (
            <div className="space-y-6">
              <div className="text-center py-8 text-gray-500">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Chart Visualizations</h3>
                <p className="text-gray-600">
                  This template includes {template.chart_configs?.length || 0} pre-configured visualizations.
                  Charts will be available after executing the template with your parameters.
                </p>
              </div>
              
              {template.chart_configs && template.chart_configs.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {template.chart_configs.map((chart, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 mb-2">{chart.chart_name}</h4>
                      <p className="text-sm text-gray-600 mb-2">Type: {chart.chart_type}</p>
                      <p className="text-xs text-gray-500">
                        {chart.is_default ? 'Default visualization' : 'Additional chart'}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-4">
            <div>
              <label htmlFor="instance-select" className="block text-sm font-medium text-gray-700 mb-1">
                AMC Instance
              </label>
              <select
                id="instance-select"
                value={selectedInstance}
                onChange={(e) => setSelectedInstance(e.target.value)}
                className="block w-48 px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                disabled={isExecuting}
              >
                {instances?.map((instance) => (
                  <option key={instance.id} value={instance.id}>
                    {instance.instanceName}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
              disabled={isExecuting}
            >
              Cancel
            </button>
            <button
              onClick={handleExecuteTemplate}
              disabled={!selectedInstance || !isParameterFormValid || isExecuting}
              className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isExecuting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Executing...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  <span>Execute Template</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateDetailModal;