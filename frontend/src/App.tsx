import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import Login from './components/auth/Login';
import Dashboard from './components/Dashboard';
import Instances from './components/instances/Instances';
import InstanceDetail from './components/instances/InstanceDetail';
import Campaigns from './components/campaigns/Campaigns';
import WorkflowDetail from './components/workflows/WorkflowDetail';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthCallback } from './pages/AuthCallback';
import Profile from './pages/Profile';
import ErrorBoundary from './components/ErrorBoundary';

// New Query Builder imports
import QueryLibrary from './pages/QueryLibrary';
import QueryFlowTemplates from './pages/QueryFlowTemplates';
import TemplateEditorWireframe from './components/query-flow-templates/editor/TemplateEditorWireframe';
import TemplateEditor from './components/query-flow-templates/editor/TemplateEditor';
import QueryBuilder from './pages/QueryBuilder';
import MyQueries from './pages/MyQueries';
import Executions from './pages/Executions';

// Data Sources imports
import DataSources from './pages/DataSources';
import DataSourceDetail from './pages/DataSourceDetail';

// Schedule imports
import ScheduleManager from './pages/ScheduleManager';

// Build Guides imports
import BuildGuides from './pages/BuildGuides';

// Test imports
import TestCampaignSelector from './components/test/TestCampaignSelector';
import TestAllCampaignSelector from './components/test/TestAllCampaignSelector';
import BuildGuideDetail from './pages/BuildGuideDetail';

// ASIN Management import
import ASINManagement from './pages/ASINManagement';

// Reports & Analytics imports
import DataCollections from './components/reports/DataCollections';

// Visual Flow Builder import
import VisualFlowBuilder from './pages/VisualFlowBuilder';
import TestFlowBuilder from './pages/TestFlowBuilder';
import TestReactFlow from './pages/TestReactFlow';
import TestReactFlowSimple from './pages/TestReactFlowSimple';
import TestReactFlowWithProvider from './pages/TestReactFlowWithProvider';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/auth/success" element={<AuthCallback />} />
          <Route path="/auth/error" element={<AuthCallback />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/instances" element={<Instances />} />
              <Route path="/instances/:instanceId" element={<InstanceDetail />} />
              <Route path="/campaigns" element={<Campaigns />} />
              <Route path="/test-campaign-selector" element={<TestCampaignSelector />} />
              <Route path="/test-all-campaigns" element={<TestAllCampaignSelector />} />
              <Route path="/executions" element={<Executions />} />
              
              {/* Legacy routes - redirect to new ones */}
              <Route path="/workflows" element={<Navigate to="/my-queries" replace />} />
              <Route path="/workflows/:workflowId" element={<WorkflowDetail />} />
              <Route path="/workflows/:workflowId/edit" element={<WorkflowDetail />} />
              <Route path="/query-templates" element={<Navigate to="/query-library" replace />} />
              
              {/* New Query Builder routes */}
              <Route path="/query-library" element={<QueryLibrary />} />
              <Route path="/query-flow-templates" element={<QueryFlowTemplates />} />
              <Route path="/query-flow-templates/editor-wireframe" element={<TemplateEditorWireframe />} />
              <Route path="/query-flow-templates/new" element={<TemplateEditor />} />
              <Route path="/query-flow-templates/edit/:id" element={<TemplateEditor />} />
              <Route path="/my-queries" element={<MyQueries />} />
              <Route path="/schedules" element={<ScheduleManager />} />
              <Route path="/query-builder/new" element={<QueryBuilder />} />
              <Route path="/query-builder/template/:templateId" element={<QueryBuilder />} />
              <Route path="/query-builder/edit/:workflowId" element={<QueryBuilder />} />
              <Route path="/query-builder/copy/:workflowId" element={<QueryBuilder />} />
              
              {/* Data Sources routes */}
              <Route path="/data-sources" element={<DataSources />} />
              <Route path="/data-sources/:schemaId" element={<DataSourceDetail />} />
              
              {/* Build Guides routes */}
              <Route path="/build-guides" element={<BuildGuides />} />
              <Route path="/build-guides/:guideId" element={<BuildGuideDetail />} />
              
              {/* ASIN Management route */}
              <Route path="/asins" element={<ASINManagement />} />
              
              {/* Reports & Analytics routes */}
              <Route path="/data-collections" element={<DataCollections />} />
              
              {/* Visual Flow Builder route */}
              <Route path="/flow-builder" element={<VisualFlowBuilder />} />
              <Route path="/test-flow-builder" element={<TestFlowBuilder />} />
              <Route path="/test-flow" element={<TestReactFlow />} />
              <Route path="/test-flow-simple" element={<TestReactFlowSimple />} />
              <Route path="/test-flow-provider" element={<TestReactFlowWithProvider />} />
              
              {/* Profile route */}
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Route>
        </Routes>
      </Router>
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            style: {
              background: '#059669',
            },
          },
          error: {
            style: {
              background: '#DC2626',
            },
          },
        }}
      />
    </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App
