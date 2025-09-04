import React, { useState, useCallback, useRef } from 'react';
import type { DragEvent } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  MarkerType,
  useReactFlow,
} from 'reactflow';
import type { Connection, Edge, Node } from 'reactflow';
import 'reactflow/dist/style.css';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { 
  Search, 
  Save, 
  Play, 
  Plus,
  Layout,
  Eye,
  EyeOff
} from 'lucide-react';
import { queryFlowTemplateService } from '../services/queryFlowTemplateService';
import { flowCompositionService } from '../services/flowCompositionService';
import type { QueryTemplate } from '../types/queryTemplate';
import type { FlowNode, FlowConnection } from '../types/flowComposition';
import FlowTemplateNode from '../components/flow-builder/FlowTemplateNode';

// Define custom node types
const nodeTypes = {
  templateNode: FlowTemplateNode,
};

// Template Gallery Sidebar Component
const TemplateGallery: React.FC<{
  onTemplateDragStart: (template: QueryTemplate, event: DragEvent) => void;
}> = ({ onTemplateDragStart }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const { data: templatesData, isLoading } = useQuery({
    queryKey: ['queryTemplates'],
    queryFn: () => queryFlowTemplateService.listTemplates({ limit: 100 }),
  });

  const templates = templatesData?.templates || [];
  
  // Get unique categories
  const categories = ['all', ...new Set(templates.map((t: any) => t.category).filter(Boolean))];
  
  // Filter templates
  const filteredTemplates = templates.filter((template: any) => {
    const matchesSearch = searchTerm === '' || 
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Query Templates</h2>
        
        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Category Filter */}
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          {categories.map((category: string) => (
            <option key={category} value={category}>
              {category === 'all' ? 'All Categories' : category}
            </option>
          ))}
        </select>
      </div>

      {/* Templates List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading templates...</div>
        ) : filteredTemplates.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No templates found</div>
        ) : (
          filteredTemplates.map((template: any) => (
            <div
              key={template.id}
              draggable
              onDragStart={(e: DragEvent) => onTemplateDragStart(template, e)}
              className="template-card p-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 cursor-move transition-colors"
            >
              <div className="flex items-start justify-between mb-1">
                <h3 className="font-medium text-gray-900 text-sm">{template.name}</h3>
                {template.category && (
                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                    {template.category}
                  </span>
                )}
              </div>
              {template.description && (
                <p className="text-xs text-gray-600 line-clamp-2">{template.description}</p>
              )}
              {template.parameters && template.parameters.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {template.parameters.slice(0, 3).map((param: any, idx: number) => (
                    <span key={idx} className="text-xs px-1.5 py-0.5 bg-gray-200 text-gray-700 rounded">
                      {param.name}
                    </span>
                  ))}
                  {template.parameters.length > 3 && (
                    <span className="text-xs text-gray-500">+{template.parameters.length - 3}</span>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Main Visual Flow Builder Component
const VisualFlowBuilderContent: React.FC = () => {
  const queryClient = useQueryClient();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { project } = useReactFlow();
  
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedComposition, setSelectedComposition] = useState<string | null>(null);
  const [showMinimap, setShowMinimap] = useState(true);
  const [isAutoLayout, setIsAutoLayout] = useState(false);

  // Load existing compositions
  const { data: compositionsData } = useQuery({
    queryKey: ['flowCompositions'],
    queryFn: () => flowCompositionService.getCompositions({ limit: 50 }),
  });

  // Save composition mutation
  const saveCompositionMutation = useMutation({
    mutationFn: async (data: { name: string; description?: string }) => {
      const compositionData = {
        name: data.name,
        description: data.description,
        nodes: nodes.map(node => ({
          node_id: node.id,
          template_id: node.data.template_id,
          position: node.position,
          config: node.data.config || {},
        })),
        connections: edges.map(edge => ({
          source_node_id: edge.source,
          target_node_id: edge.target,
          parameter_mappings: edge.data?.parameter_mappings || [],
        })),
      };

      if (selectedComposition) {
        return flowCompositionService.updateComposition(selectedComposition, compositionData);
      } else {
        return flowCompositionService.createComposition(compositionData);
      }
    },
    onSuccess: () => {
      toast.success('Flow composition saved successfully');
      queryClient.invalidateQueries({ queryKey: ['flowCompositions'] });
    },
    onError: (error) => {
      toast.error(`Failed to save composition: ${(error as Error).message}`);
    },
  });

  // Handle template drop
  const onDrop = useCallback(
    (event: DragEvent) => {
      event.preventDefault();

      if (!reactFlowWrapper.current) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const templateData = event.dataTransfer?.getData('application/reactflow');

      if (templateData) {
        const template = JSON.parse(templateData);
        const position = project({
          x: event.clientX - reactFlowBounds.left,
          y: event.clientY - reactFlowBounds.top,
        });

        const newNode: Node = {
          id: `node_${Date.now()}`,
          type: 'templateNode',
          position,
          data: {
            template_id: template.template_id || template.id,
            name: template.name,
            description: template.description,
            parameters: template.parameters || [],
            config: {},
          },
        };

        setNodes((nds) => nds.concat(newNode));
      }
    },
    [project, setNodes]
  );

  const onDragOver = useCallback((event: DragEvent) => {
    event.preventDefault();
    event.dataTransfer!.dropEffect = 'move';
  }, []);

  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge: Edge = {
        ...params,
        id: `edge_${Date.now()}`,
        type: 'smoothstep',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
        data: {
          parameter_mappings: [],
        },
      } as Edge;
      
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  const handleTemplateDragStart = (template: QueryTemplate, event: DragEvent) => {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('application/reactflow', JSON.stringify(template));
  };

  // Auto-layout function
  const handleAutoLayout = () => {
    if (nodes.length === 0) return;

    const nodeWidth = 250;
    const nodeHeight = 150;
    const horizontalSpacing = 100;
    const verticalSpacing = 100;

    // Simple left-to-right layout
    const layoutedNodes = nodes.map((node, index) => ({
      ...node,
      position: {
        x: (nodeWidth + horizontalSpacing) * (index % 3),
        y: Math.floor(index / 3) * (nodeHeight + verticalSpacing),
      },
    }));

    setNodes(layoutedNodes);
    setIsAutoLayout(true);
    setTimeout(() => setIsAutoLayout(false), 300);
  };

  // Load composition
  const handleLoadComposition = async (compositionId: string) => {
    try {
      const composition = await flowCompositionService.getComposition(compositionId);
      
      // Convert composition nodes to React Flow nodes
      const flowNodes = composition.nodes.map((node: FlowNode) => ({
        id: node.node_id,
        type: 'templateNode',
        position: node.position,
        data: {
          template_id: node.template_id,
          name: node.template?.name || 'Unknown Template',
          description: node.template?.description,
          parameters: node.template?.parameters || [],
          config: node.config,
        },
      }));

      // Convert composition connections to React Flow edges
      const flowEdges = composition.connections.map((conn: FlowConnection, index: number) => ({
        id: `edge_${index}`,
        source: conn.source_node_id,
        target: conn.target_node_id,
        type: 'smoothstep',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
        },
        data: {
          parameter_mappings: conn.parameter_mappings,
        },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
      setSelectedComposition(compositionId);
      toast.success('Composition loaded successfully');
    } catch (error) {
      toast.error(`Failed to load composition: ${(error as Error).message}`);
    }
  };

  // Execute composition
  const handleExecuteComposition = () => {
    if (nodes.length === 0) {
      toast.error('Add at least one node to execute the flow');
      return;
    }

    // Navigate to execution dialog or trigger execution
    toast.success('Flow execution started');
  };

  // Clear canvas
  const handleClearCanvas = () => {
    setNodes([]);
    setEdges([]);
    setSelectedComposition(null);
  };

  return (
    <div className="h-screen flex">
      {/* Template Gallery Sidebar */}
      <TemplateGallery onTemplateDragStart={handleTemplateDragStart} />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                const name = prompt('Enter flow name:');
                if (name) {
                  saveCompositionMutation.mutate({ name });
                }
              }}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Save className="h-4 w-4 mr-1" />
              Save
            </button>

            <button
              onClick={handleExecuteComposition}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Play className="h-4 w-4 mr-1" />
              Execute
            </button>

            <div className="h-6 w-px bg-gray-300" />

            <select
              value={selectedComposition || ''}
              onChange={(e) => e.target.value && handleLoadComposition(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-2 py-1.5"
            >
              <option value="">Load Composition...</option>
              {compositionsData?.compositions.map((comp: any) => (
                <option key={comp.id} value={comp.id}>
                  {comp.name}
                </option>
              ))}
            </select>

            <button
              onClick={handleClearCanvas}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <Plus className="h-4 w-4 mr-1" />
              New Flow
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleAutoLayout}
              className={`inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md ${
                isAutoLayout ? 'text-blue-700 bg-blue-50' : 'text-gray-700 bg-white hover:bg-gray-50'
              }`}
            >
              <Layout className="h-4 w-4 mr-1" />
              Auto Layout
            </button>

            <button
              onClick={() => setShowMinimap(!showMinimap)}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              {showMinimap ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* React Flow Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
            className="bg-gray-50"
          >
            <Controls />
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
            {showMinimap && (
              <MiniMap 
                nodeStrokeColor={() => '#6366f1'}
                nodeColor={() => '#e0e7ff'}
                nodeStrokeWidth={3}
              />
            )}
          </ReactFlow>
        </div>

        {/* Status Bar */}
        <div className="bg-white border-t border-gray-200 px-4 py-2 text-sm text-gray-600">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span>Nodes: {nodes.length}</span>
              <span>Connections: {edges.length}</span>
              {selectedComposition && (
                <span className="text-blue-600">Editing saved composition</span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-500">
                Drop templates onto canvas to build flow
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Wrapper with ReactFlowProvider
const VisualFlowBuilder: React.FC = () => {
  return (
    <ReactFlowProvider>
      <VisualFlowBuilderContent />
    </ReactFlowProvider>
  );
};

export default VisualFlowBuilder;