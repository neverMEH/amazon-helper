import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, Link2 } from 'lucide-react';
import type { Node, Edge } from 'reactflow';
import type { QueryFlowTemplate, ParameterFormValues } from '../../types/queryFlowTemplate';
import type { FlowTemplateNodeData } from './FlowTemplateNode';
import TemplateParameterForm from '../query-flow-templates/TemplateParameterForm';
import SQLPreview from '../query-flow-templates/SQLPreview';

interface NodeConfigurationModalProps {
  node: Node<FlowTemplateNodeData>;
  nodes: Node[];
  edges: Edge[];
  template?: QueryFlowTemplate;
  isOpen: boolean;
  onClose: () => void;
  onSave: (nodeId: string, config: Record<string, any>, parameterMappings?: ParameterMapping[]) => void;
}

export interface ParameterMapping {
  source_param: string;
  target_param: string;
  transformation?: 'direct' | 'first' | 'last' | 'join' | 'count';
}

const NodeConfigurationModal: React.FC<NodeConfigurationModalProps> = ({
  node,
  nodes,
  edges,
  template,
  isOpen,
  onClose,
  onSave,
}) => {
  const [activeTab, setActiveTab] = useState<'parameters' | 'mappings' | 'preview'>('parameters');
  const [parameterValues, setParameterValues] = useState<ParameterFormValues>(node.data.config || {});
  const [parameterErrors, setParameterErrors] = useState<Record<string, string>>({});
  const [isParameterFormValid, setIsParameterFormValid] = useState(false);
  const [parameterMappings, setParameterMappings] = useState<ParameterMapping[]>([]);

  // Get upstream nodes (nodes that connect to this node)
  const upstreamNodes = edges
    .filter(edge => edge.target === node.id)
    .map(edge => nodes.find(n => n.id === edge.source))
    .filter(Boolean) as Node<FlowTemplateNodeData>[];

  // Get available output parameters from upstream nodes
  const availableSourceParameters = upstreamNodes.flatMap(upstreamNode => {
    // In a real implementation, this would fetch the actual output schema
    // For now, we'll use a simple pattern
    return [
      { nodeId: upstreamNode.id, nodeName: upstreamNode.data.name, param: 'result_rows', type: 'array' },
      { nodeId: upstreamNode.id, nodeName: upstreamNode.data.name, param: 'row_count', type: 'number' },
      { nodeId: upstreamNode.id, nodeName: upstreamNode.data.name, param: 'execution_id', type: 'string' },
    ];
  });

  // Initialize mappings from node data
  useEffect(() => {
    if (node.data.config?.parameter_mappings) {
      setParameterMappings(node.data.config.parameter_mappings);
    }
  }, [node.data.config]);

  const handleParameterValidationChange = (isValid: boolean, errors: Record<string, string>) => {
    setIsParameterFormValid(isValid);
    setParameterErrors(errors);
  };

  const handleAddMapping = () => {
    setParameterMappings([
      ...parameterMappings,
      { source_param: '', target_param: '', transformation: 'direct' }
    ]);
  };

  const handleUpdateMapping = (index: number, field: keyof ParameterMapping, value: string) => {
    const updated = [...parameterMappings];
    updated[index] = { ...updated[index], [field]: value };
    setParameterMappings(updated);
  };

  const handleRemoveMapping = (index: number) => {
    setParameterMappings(parameterMappings.filter((_, i) => i !== index));
  };

  const handleSave = () => {
    const config = {
      ...parameterValues,
      parameter_mappings: parameterMappings.filter(m => m.source_param && m.target_param)
    };
    onSave(node.id, config, parameterMappings);
    onClose();
  };

  if (!isOpen || !template) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-60 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Configure Node: {node.data.name}</h2>
            <p className="text-sm text-gray-600 mt-1">{node.data.description}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('parameters')}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'parameters'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Parameters
          </button>
          {upstreamNodes.length > 0 && (
            <button
              onClick={() => setActiveTab('mappings')}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === 'mappings'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Input Mappings
              {parameterMappings.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
                  {parameterMappings.length}
                </span>
              )}
            </button>
          )}
          <button
            onClick={() => setActiveTab('preview')}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === 'preview'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            SQL Preview
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'parameters' && (
            <div>
              <TemplateParameterForm
                template={template}
                values={parameterValues}
                onChange={setParameterValues}
                onValidationChange={handleParameterValidationChange}
              />
              
              {Object.keys(parameterErrors).length > 0 && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-start">
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
                    <div>
                      <h4 className="font-medium text-red-800">Validation Errors</h4>
                      <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
                        {Object.entries(parameterErrors).map(([param, error]) => (
                          <li key={param}>
                            <strong>{param}:</strong> {error}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'mappings' && (
            <div>
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Parameter Mappings</h3>
                <p className="text-sm text-gray-600">
                  Map outputs from upstream nodes to this node's parameters. This allows data to flow between nodes.
                </p>
              </div>

              {upstreamNodes.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Link2 className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p>No upstream nodes connected</p>
                  <p className="text-sm mt-1">Connect a node to this one to enable parameter mapping</p>
                </div>
              ) : (
                <>
                  <div className="space-y-4">
                    {parameterMappings.map((mapping, index) => (
                      <div key={index} className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg">
                        <select
                          value={mapping.source_param}
                          onChange={(e) => handleUpdateMapping(index, 'source_param', e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        >
                          <option value="">Select source parameter...</option>
                          {availableSourceParameters.map((param, idx) => (
                            <option key={idx} value={`${param.nodeId}.${param.param}`}>
                              {param.nodeName} → {param.param} ({param.type})
                            </option>
                          ))}
                        </select>

                        <span className="text-gray-400">→</span>

                        <select
                          value={mapping.target_param}
                          onChange={(e) => handleUpdateMapping(index, 'target_param', e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm"
                        >
                          <option value="">Select target parameter...</option>
                          {template.parameters?.map(param => (
                            <option key={param.parameter_name} value={param.parameter_name}>
                              {param.display_name || param.parameter_name} ({param.parameter_type})
                            </option>
                          ))}
                        </select>

                        <select
                          value={mapping.transformation}
                          onChange={(e) => handleUpdateMapping(index, 'transformation', e.target.value)}
                          className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                        >
                          <option value="direct">Direct</option>
                          <option value="first">First Value</option>
                          <option value="last">Last Value</option>
                          <option value="join">Join Array</option>
                          <option value="count">Count</option>
                        </select>

                        <button
                          onClick={() => handleRemoveMapping(index)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={handleAddMapping}
                    className="mt-4 px-4 py-2 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-md text-sm font-medium"
                  >
                    + Add Mapping
                  </button>
                </>
              )}
            </div>
          )}

          {activeTab === 'preview' && template && (
            <div>
              <SQLPreview
                templateId={template.template_id}
                parameters={parameterValues}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            {upstreamNodes.length > 0 && (
              <span>
                Connected to {upstreamNodes.length} upstream node{upstreamNodes.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!isParameterFormValid && activeTab === 'parameters'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NodeConfigurationModal;