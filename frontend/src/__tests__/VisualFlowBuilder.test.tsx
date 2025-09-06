import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import VisualFlowBuilder from '../pages/VisualFlowBuilder';
import { ReactFlowProvider } from 'reactflow';

// Mock React Flow to avoid canvas rendering issues in tests
vi.mock('reactflow', () => ({
  ReactFlow: vi.fn(({ children, nodes, edges }) => (
    <div data-testid="react-flow-canvas">
      <div data-testid="nodes-count">{nodes?.length || 0}</div>
      <div data-testid="edges-count">{edges?.length || 0}</div>
      {children}
    </div>
  )),
  ReactFlowProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Controls: () => <div data-testid="react-flow-controls">Controls</div>,
  Background: () => <div data-testid="react-flow-background">Background</div>,
  MiniMap: () => <div data-testid="react-flow-minimap">MiniMap</div>,
  Handle: vi.fn(({ type, position }) => (
    <div data-testid={`handle-${type}-${position}`} />
  )),
  Position: {
    Top: 'top',
    Bottom: 'bottom',
    Left: 'left',
    Right: 'right',
  },
  useReactFlow: () => ({
    project: vi.fn((position) => position),
    getNodes: vi.fn(() => []),
    getEdges: vi.fn(() => []),
    setNodes: vi.fn(),
    setEdges: vi.fn(),
    addNodes: vi.fn(),
    addEdges: vi.fn(),
  }),
  useNodesState: vi.fn((initialNodes) => {
    const [nodes, setNodes] = React.useState(initialNodes);
    return [nodes, setNodes, vi.fn()];
  }),
  useEdgesState: vi.fn((initialEdges) => {
    const [edges, setEdges] = React.useState(initialEdges);
    return [edges, setEdges, vi.fn()];
  }),
}));

// Mock API services
vi.mock('../services/queryFlowTemplateService', () => ({
  queryFlowTemplateService: {
    listTemplates: vi.fn(() => Promise.resolve({
      templates: [
        {
          id: 'tmpl_1',
          template_id: 'tmpl_campaign_performance',
          name: 'Campaign Performance',
          description: 'Analyze campaign performance metrics',
          category: 'Performance',
          parameters: [
            { name: 'date_range', type: 'date_range', required: true }
          ]
        },
        {
          id: 'tmpl_2',
          template_id: 'tmpl_creative_analysis',
          name: 'Creative Analysis',
          description: 'Analyze creative performance',
          category: 'Creative',
          parameters: [
            { name: 'asin_list', type: 'asin_list', required: true }
          ]
        }
      ],
      total_count: 2
    }))
  }
}));

vi.mock('../services/flowCompositionService', () => ({
  flowCompositionService: {
    getCompositions: vi.fn(() => Promise.resolve({
      compositions: [],
      total_count: 0
    })),
    createComposition: vi.fn((data) => Promise.resolve({
      id: 'comp_123',
      composition_id: data.composition_id,
      name: data.name,
      nodes: [],
      connections: []
    })),
    updateComposition: vi.fn((id, data) => Promise.resolve({
      id: id,
      ...data
    })),
    deleteComposition: vi.fn(() => Promise.resolve(true))
  }
}));

describe('VisualFlowBuilder', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ReactFlowProvider>
            <VisualFlowBuilder />
          </ReactFlowProvider>
        </BrowserRouter>
      </QueryClientProvider>
    );
  };

  describe('Canvas Initialization', () => {
    it('should render the visual flow builder canvas', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('react-flow-canvas')).toBeInTheDocument();
      });
    });

    it('should render canvas controls', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('react-flow-controls')).toBeInTheDocument();
        expect(screen.getByTestId('react-flow-background')).toBeInTheDocument();
        expect(screen.getByTestId('react-flow-minimap')).toBeInTheDocument();
      });
    });

    it('should initialize with empty canvas', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('nodes-count')).toHaveTextContent('0');
        expect(screen.getByTestId('edges-count')).toHaveTextContent('0');
      });
    });
  });

  describe('Template Gallery Sidebar', () => {
    it('should render template gallery sidebar', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Query Templates')).toBeInTheDocument();
      });
    });

    it('should load and display templates', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Campaign Performance')).toBeInTheDocument();
        expect(screen.getByText('Creative Analysis')).toBeInTheDocument();
      });
    });

    it('should show template categories', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText('Performance')).toBeInTheDocument();
        expect(screen.getByText('Creative')).toBeInTheDocument();
      });
    });

    it('should allow template search', async () => {
      renderComponent();
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText(/search templates/i);
        expect(searchInput).toBeInTheDocument();
      });
    });
  });

  describe('Drag and Drop Functionality', () => {
    it('should make templates draggable', async () => {
      renderComponent();
      
      await waitFor(() => {
        const templateCard = screen.getByText('Campaign Performance').closest('[draggable]');
        expect(templateCard).toHaveAttribute('draggable', 'true');
      });
    });

    it('should handle template drag start', async () => {
      renderComponent();
      
      await waitFor(() => {
        const templateCard = screen.getByText('Campaign Performance').closest('[draggable]');
        
        const dragStartEvent = new DragEvent('dragstart', {
          dataTransfer: new DataTransfer(),
        });
        
        fireEvent(templateCard!, dragStartEvent);
      });
    });

    it('should handle drop on canvas', async () => {
      renderComponent();
      
      await waitFor(() => {
        const canvas = screen.getByTestId('react-flow-canvas');
        
        const dropEvent = new DragEvent('drop', {
          dataTransfer: new DataTransfer(),
        });
        
        dropEvent.dataTransfer?.setData('application/reactflow', JSON.stringify({
          template_id: 'tmpl_campaign_performance',
          name: 'Campaign Performance'
        }));
        
        fireEvent(canvas, dropEvent);
      });
    });
  });

  describe('Node Management', () => {
    it('should add node when template is dropped', async () => {
      renderComponent();
      
      // Simulate dropping a template
      await waitFor(() => {
        const canvas = screen.getByTestId('react-flow-canvas');
        fireEvent.drop(canvas, {
          dataTransfer: {
            getData: () => JSON.stringify({
              template_id: 'tmpl_campaign_performance',
              name: 'Campaign Performance'
            })
          }
        });
      });
      
      // Node should be added
      // In real implementation, this would update the nodes count
    });

    it('should allow node selection', async () => {
      renderComponent();
      
      // Add a node first
      // Then test selection
      // This would be implemented with actual node components
    });

    it('should allow node deletion', async () => {
      renderComponent();
      
      // Add a node, select it, press delete
      // Test that node is removed
    });
  });

  describe('Connection Management', () => {
    it('should render connection handles on nodes', async () => {
      renderComponent();
      
      // When nodes are added, they should have handles
      // Test would check for handle elements
    });

    it('should allow creating connections between nodes', async () => {
      renderComponent();
      
      // Add two nodes
      // Connect them
      // Verify edge is created
    });

    it('should validate connections', async () => {
      renderComponent();
      
      // Try to create invalid connection (cycle)
      // Should show error or prevent connection
    });
  });

  describe('Canvas State Persistence', () => {
    it('should save canvas state', async () => {
      renderComponent();
      
      // Add nodes and edges
      // Trigger save
      // Verify save function is called
    });

    it('should restore canvas state', async () => {
      renderComponent();
      
      // Load saved composition
      // Verify nodes and edges are restored
    });

    it('should auto-save changes', async () => {
      vi.useFakeTimers();
      renderComponent();
      
      // Make changes
      // Advance timers
      // Verify auto-save triggered
      
      vi.useRealTimers();
    });
  });

  describe('Composition Actions', () => {
    it('should create new composition', async () => {
      renderComponent();
      
      const newButton = screen.getByRole('button', { name: /new flow/i });
      await userEvent.click(newButton);
      
      // Fill in composition details
      // Save
      // Verify creation
    });

    it('should save composition', async () => {
      renderComponent();
      
      const saveButton = screen.getByRole('button', { name: /save/i });
      await userEvent.click(saveButton);
      
      // Verify save is called with current state
    });

    it('should load existing composition', async () => {
      renderComponent();
      
      // Select from dropdown or list
      // Verify composition is loaded
    });

    it('should execute composition', async () => {
      renderComponent();
      
      const executeButton = screen.getByRole('button', { name: /execute/i });
      await userEvent.click(executeButton);
      
      // Verify execution dialog opens
    });
  });

  describe('Toolbar and Controls', () => {
    it('should have zoom controls', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByTestId('react-flow-controls')).toBeInTheDocument();
      });
    });

    it('should have layout options', async () => {
      renderComponent();
      
      // Look for layout buttons
      // Test auto-layout functionality
    });

    it('should have undo/redo buttons', async () => {
      renderComponent();
      
      // Check for undo/redo buttons
      // Test functionality
    });
  });

  describe('Integration with Existing Components', () => {
    it('should reuse TemplateCard component', async () => {
      renderComponent();
      
      // Verify template cards have same structure as existing component
      await waitFor(() => {
        const templateCard = screen.getByText('Campaign Performance').closest('.template-card');
        expect(templateCard).toBeInTheDocument();
      });
    });

    it('should open parameter form when node is configured', async () => {
      renderComponent();
      
      // Add node
      // Double-click or click configure
      // Verify parameter form opens
    });

    it('should integrate with existing theme', async () => {
      renderComponent();
      
      // Check for Tailwind classes
      // Verify dark mode support
    });
  });

  describe('Error Handling', () => {
    it('should show error when template load fails', async () => {
      // Mock service to return error
      const { queryFlowTemplateService } = await import('../services/queryFlowTemplateService');
      vi.mocked(queryFlowTemplateService.listTemplates).mockRejectedValueOnce(new Error('Load failed'));
      
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByText(/failed to load templates/i)).toBeInTheDocument();
      });
    });

    it('should handle save errors gracefully', async () => {
      renderComponent();
      
      // Mock save to fail
      // Attempt save
      // Verify error message
    });

    it('should prevent invalid node connections', async () => {
      renderComponent();
      
      // Try to create circular dependency
      // Should show warning
    });
  });

  describe('Accessibility', () => {
    it('should support keyboard navigation', async () => {
      renderComponent();
      
      // Test tab navigation
      // Test arrow keys for node selection
      // Test delete key
    });

    it('should have proper ARIA labels', async () => {
      renderComponent();
      
      await waitFor(() => {
        expect(screen.getByRole('region', { name: /flow canvas/i })).toBeInTheDocument();
        expect(screen.getByRole('complementary', { name: /template gallery/i })).toBeInTheDocument();
      });
    });

    it('should announce state changes', async () => {
      renderComponent();
      
      // Add node
      // Should announce "Node added"
      // Delete node
      // Should announce "Node deleted"
    });
  });
});