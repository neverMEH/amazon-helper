import React from 'react';
import ReactFlow from 'reactflow';
import 'reactflow/dist/style.css';

const TestReactFlowSimple: React.FC = () => {
  console.log('TestReactFlowSimple component rendering');
  
  const nodes = [
    {
      id: '1',
      type: 'default',
      data: { label: 'Node 1' },
      position: { x: 250, y: 5 },
    },
  ];

  return (
    <div>
      <h1>React Flow Simple Test</h1>
      <div style={{ width: '100%', height: '500px', border: '2px solid red' }}>
        <ReactFlow nodes={nodes} />
      </div>
      <p>You should see a red bordered box above with a node inside.</p>
    </div>
  );
};

export default TestReactFlowSimple;