import { useState } from 'react';
import { CampaignSelector } from '../parameter-detection/CampaignSelector';

export default function TestCampaignSelector() {
  const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  // Log when component mounts
  console.log('[TestCampaignSelector] Component mounted');
  
  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Test Campaign Selector</h1>
      <p className="mb-4 text-sm text-gray-600">
        Open browser console to see debug output. Testing with instance: amccfnbscqp, brand: FEKKAI
      </p>
      
      <div className="space-y-6">
        {/* Test 1: SP Campaign Names */}
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">Test 1: SP Campaign Names</h2>
          <CampaignSelector
            instanceId="amccfnbscqp"
            brandId="FEKKAI"
            value={selectedCampaigns}
            onChange={(value) => {
              console.log('[Test 1] onChange called with:', value);
              console.log('[Test 1] Value type:', typeof value, 'Is Array:', Array.isArray(value));
              setSelectedCampaigns(value);
            }}
            campaignType="sp"
            valueType="names"
            placeholder="Select SP campaign names..."
          />
          <div className="mt-2 text-sm text-gray-600">
            <strong>Selected Names:</strong> {selectedCampaigns.length > 0 ? (
              <pre className="mt-1 p-2 bg-gray-100 rounded text-xs">
                {JSON.stringify(selectedCampaigns, null, 2)}
              </pre>
            ) : 'None'}
          </div>
        </div>
        
        {/* Test 2: Campaign IDs */}
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">Test 2: SP Campaign IDs</h2>
          <CampaignSelector
            instanceId="amccfnbscqp"
            brandId="FEKKAI"
            value={selectedIds}
            onChange={(value) => {
              console.log('[Test 2] onChange called with:', value);
              console.log('[Test 2] Value type:', typeof value, 'Is Array:', Array.isArray(value));
              setSelectedIds(value);
            }}
            campaignType="sp"
            valueType="ids"
            placeholder="Select SP campaign IDs..."
          />
          <div className="mt-2 text-sm text-gray-600">
            <strong>Selected IDs:</strong> {selectedIds.length > 0 ? (
              <pre className="mt-1 p-2 bg-gray-100 rounded text-xs">
                {JSON.stringify(selectedIds, null, 2)}
              </pre>
            ) : 'None'}
          </div>
        </div>
        
        {/* Test 3: No filtering */}
        <div className="border rounded-lg p-4">
          <h2 className="text-lg font-semibold mb-3">Test 3: All Campaigns</h2>
          <CampaignSelector
            instanceId="amccfnbscqp"
            brandId="FEKKAI"
            value={[]}
            onChange={(value) => {
              console.log('Test 3 - Selected:', value);
            }}
            placeholder="Select any campaigns..."
          />
        </div>
      </div>
    </div>
  );
}