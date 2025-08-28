import { useState } from 'react';
import { CampaignSelector } from '../parameter-detection/CampaignSelector';

export default function TestAllCampaignSelector() {
  const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Test Campaign Selector - Show All Campaigns</h1>
      <p className="mb-4 text-sm text-gray-600">
        This test page demonstrates the campaign selector showing ALL campaigns without filtering by instance or brand.
      </p>
      
      <div className="space-y-6">
        {/* Test 1: All SP Campaign Names */}
        <div className="border rounded-lg p-4 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Test 1: All SP Campaign Names (No Filtering)</h2>
          <p className="text-sm text-gray-500 mb-3">
            Shows all SP campaigns from the entire database with brand information displayed
          </p>
          <CampaignSelector
            value={selectedCampaigns}
            onChange={(value) => {
              console.log('[Test 1] Selected campaigns:', value);
              setSelectedCampaigns(value);
            }}
            campaignType="sp"
            valueType="names"
            showAll={true}
            placeholder="Select any SP campaign names..."
          />
          <div className="mt-3 p-3 bg-gray-50 rounded">
            <strong className="text-sm">Selected Names ({selectedCampaigns.length}):</strong>
            {selectedCampaigns.length > 0 ? (
              <ul className="mt-2 text-sm space-y-1">
                {selectedCampaigns.map((name) => (
                  <li key={name} className="text-gray-700">• {name}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500 mt-1">None selected</p>
            )}
          </div>
        </div>
        
        {/* Test 2: All Campaign IDs */}
        <div className="border rounded-lg p-4 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Test 2: All Campaign IDs (No Filtering)</h2>
          <p className="text-sm text-gray-500 mb-3">
            Shows all campaigns from the entire database with brand information displayed
          </p>
          <CampaignSelector
            value={selectedIds}
            onChange={(value) => {
              console.log('[Test 2] Selected campaign IDs:', value);
              setSelectedIds(value);
            }}
            valueType="ids"
            showAll={true}
            placeholder="Select any campaign IDs..."
          />
          <div className="mt-3 p-3 bg-gray-50 rounded">
            <strong className="text-sm">Selected IDs ({selectedIds.length}):</strong>
            {selectedIds.length > 0 ? (
              <ul className="mt-2 text-sm space-y-1">
                {selectedIds.map((id) => (
                  <li key={id} className="text-gray-700 font-mono">• {id}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500 mt-1">None selected</p>
            )}
          </div>
        </div>
        
        {/* Test 3: Compare with filtered version */}
        <div className="border rounded-lg p-4 bg-white shadow-sm">
          <h2 className="text-lg font-semibold mb-3">Test 3: Filtered by Instance/Brand (Old Way)</h2>
          <p className="text-sm text-gray-500 mb-3">
            For comparison: Shows only FEKKAI campaigns when instance/brand are specified
          </p>
          <CampaignSelector
            instanceId="amccfnbscqp"
            brandId="FEKKAI"
            value={[]}
            onChange={(value) => {
              console.log('[Test 3] Selected (filtered):', value);
            }}
            campaignType="sp"
            valueType="names"
            showAll={false}
            placeholder="Select FEKKAI SP campaigns only..."
          />
        </div>
      </div>
      
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">Implementation Notes:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• When <code className="bg-blue-100 px-1 rounded">showAll=true</code>, the selector fetches from the main campaigns endpoint</li>
          <li>• Brand information is displayed inline with each campaign when showing all</li>
          <li>• The selector can return either campaign names or IDs based on <code className="bg-blue-100 px-1 rounded">valueType</code></li>
          <li>• Instance and brand IDs are now optional props</li>
        </ul>
      </div>
    </div>
  );
}