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

// New Query Builder imports
import QueryLibrary from './pages/QueryLibrary';
import QueryBuilder from './pages/QueryBuilder';
import MyQueries from './pages/MyQueries';

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
              
              {/* Legacy routes - redirect to new ones */}
              <Route path="/workflows" element={<Navigate to="/my-queries" replace />} />
              <Route path="/workflows/:workflowId" element={<WorkflowDetail />} />
              <Route path="/workflows/:workflowId/edit" element={<WorkflowDetail />} />
              <Route path="/query-templates" element={<Navigate to="/query-library" replace />} />
              
              {/* New Query Builder routes */}
              <Route path="/query-library" element={<QueryLibrary />} />
              <Route path="/my-queries" element={<MyQueries />} />
              <Route path="/query-builder/new" element={<QueryBuilder />} />
              <Route path="/query-builder/template/:templateId" element={<QueryBuilder />} />
              <Route path="/query-builder/edit/:workflowId" element={<QueryBuilder />} />
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
  );
}

export default App
