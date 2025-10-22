import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';

// Only eagerly load critical components needed for initial render
import ProtectedRoute from './components/auth/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load all route components to reduce initial bundle size
const Layout = lazy(() => import('./components/Layout'));
const Login = lazy(() => import('./components/auth/Login'));
const Dashboard = lazy(() => import('./components/Dashboard'));
const Instances = lazy(() => import('./components/instances/Instances'));
const InstanceDetail = lazy(() => import('./components/instances/InstanceDetail'));
const Campaigns = lazy(() => import('./components/campaigns/Campaigns'));
const AuthCallback = lazy(() => import('./pages/AuthCallback').then(module => ({ default: module.AuthCallback })));
const Profile = lazy(() => import('./pages/Profile'));

// Query Builder pages
const QueryLibrary = lazy(() => import('./pages/QueryLibrary'));
const QueryBuilder = lazy(() => import('./pages/QueryBuilder'));
const MyQueries = lazy(() => import('./pages/MyQueries'));
const Executions = lazy(() => import('./pages/Executions'));

// Data Sources pages
const DataSources = lazy(() => import('./pages/DataSources'));
const DataSourceDetail = lazy(() => import('./pages/DataSourceDetail'));

// Schedule pages
const ScheduleManager = lazy(() => import('./pages/ScheduleManager'));

// Build Guides pages
const BuildGuides = lazy(() => import('./pages/BuildGuides'));
const BuildGuideDetail = lazy(() => import('./pages/BuildGuideDetail'));

// Test pages
const TestCampaignSelector = lazy(() => import('./components/test/TestCampaignSelector'));
const TestAllCampaignSelector = lazy(() => import('./components/test/TestAllCampaignSelector'));

// ASIN Management
const ASINManagement = lazy(() => import('./pages/ASINManagement'));

// Reports & Analytics
const DataCollections = lazy(() => import('./components/reports/DataCollections'));
const ReportBuilder = lazy(() => import('./components/report-builder/ReportBuilder'));


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

// Loading fallback component for code splitting
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Suspense fallback={<LoadingFallback />}>
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
              <Route path="/query-templates" element={<Navigate to="/query-library" replace />} />
              
              {/* New Query Builder routes */}
              <Route path="/query-library" element={<QueryLibrary />} />
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
              <Route path="/report-builder" element={<ReportBuilder />} />
              
              
              {/* Profile route */}
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Route>
        </Routes>
          </Suspense>
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
