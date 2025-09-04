import React from 'react';
import ReactFlow, { ReactFlowProvider } from 'reactflow';
import 'reactflow/dist/style.css';

const Flow = () => {
  const nodes = [
    {
      id: '1',
      type: 'default',
      data: { label: 'Test Node' },
      position: { x: 100, y: 100 },
    },
  ];

  return (
    <div style={{ width: '100%', height: '400px', background: '#f0f0f0' }}>
      <ReactFlow 
        nodes={nodes} 
        fitView
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      />
    </div>
  );
};

const TestReactFlowWithProvider: React.FC = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h1>React Flow with Provider Test</h1>
      <ReactFlowProvider>
        <Flow />
      </ReactFlowProvider>
      <p>Gray box above should contain a node.</p>
    </div>
  );
};

export default TestReactFlowWithProvider;