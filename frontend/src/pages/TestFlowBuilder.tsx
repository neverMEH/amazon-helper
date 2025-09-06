import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import VisualFlowBuilder from './VisualFlowBuilder';

const TestFlowBuilder: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/query-flow-templates')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Flow Builder Test</h1>
            <p className="text-sm text-gray-600">Testing node configuration and connections</p>
          </div>
        </div>
        <div className="text-xs text-gray-500 bg-yellow-50 border border-yellow-200 px-3 py-1 rounded">
          Debug Mode - Check console for logs
        </div>
      </div>

      {/* Flow Builder */}
      <div className="flex-1">
        <VisualFlowBuilder />
      </div>

      {/* Debug Instructions */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-3">
        <p className="text-sm text-gray-600">
          <strong>Testing Instructions:</strong> 
          1. Drag a template from the left sidebar onto the canvas. 
          2. Click the wheel icon on the node to open configuration. 
          3. Connect nodes by dragging from output to input handles. 
          4. Check browser console for debug logs.
        </p>
      </div>
    </div>
  );
};

export default TestFlowBuilder;