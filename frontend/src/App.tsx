import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { lazy, Suspense } from 'react';
import Layout from './components/Layout';
import Login from './components/auth/Login';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthCallback } from './pages/AuthCallback';
import ErrorBoundary from './components/ErrorBoundary';

// Loading skeleton for lazy-loaded pages
const PageSkeleton = () => (
  <div className="animate-pulse p-6">
    <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
    <div className="space-y-4">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-32 bg-gray-200 rounded"></div>
    </div>
  </div>
);

// Eager load: Dashboard and core navigation (frequently accessed)
import Dashboard from './components/Dashboard';
import Instances from './components/instances/Instances';
import InstanceDetail from './components/instances/InstanceDetail';

// Lazy load: Less frequently accessed pages
const Campaigns = lazy(() => import('./components/campaigns/Campaigns'));
const Profile = lazy(() => import('./pages/Profile'));
const QueryLibrary = lazy(() => import('./pages/QueryLibrary'));
const QueryBuilder = lazy(() => import('./pages/QueryBuilder'));
const MyQueries = lazy(() => import('./pages/MyQueries'));
const Executions = lazy(() => import('./pages/Executions'));
const DataSources = lazy(() => import('./pages/DataSources'));
const DataSourceDetail = lazy(() => import('./pages/DataSourceDetail'));
const ScheduleManager = lazy(() => import('./pages/ScheduleManager'));
const BuildGuides = lazy(() => import('./pages/BuildGuides'));
const BuildGuideDetail = lazy(() => import('./pages/BuildGuideDetail'));
const ASINManagement = lazy(() => import('./pages/ASINManagement'));
const DataCollections = lazy(() => import('./components/reports/DataCollections'));
const ReportBuilder = lazy(() => import('./components/report-builder/ReportBuilder'));

// Test components (lazy loaded, rarely used)
const TestCampaignSelector = lazy(() => import('./components/test/TestCampaignSelector'));
const TestAllCampaignSelector = lazy(() => import('./components/test/TestAllCampaignSelector'));


const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false, // Disabled: reduces unnecessary refetches on tab switch
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
              {/* Eager loaded routes - core navigation */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/instances" element={<Instances />} />
              <Route path="/instances/:instanceId" element={<InstanceDetail />} />

              {/* Lazy loaded routes - wrapped in Suspense */}
              <Route path="/campaigns" element={<Suspense fallback={<PageSkeleton />}><Campaigns /></Suspense>} />
              <Route path="/test-campaign-selector" element={<Suspense fallback={<PageSkeleton />}><TestCampaignSelector /></Suspense>} />
              <Route path="/test-all-campaigns" element={<Suspense fallback={<PageSkeleton />}><TestAllCampaignSelector /></Suspense>} />
              <Route path="/executions" element={<Suspense fallback={<PageSkeleton />}><Executions /></Suspense>} />

              {/* Legacy routes - redirect to new ones */}
              <Route path="/query-templates" element={<Navigate to="/query-library" replace />} />

              {/* Query Builder routes */}
              <Route path="/query-library" element={<Suspense fallback={<PageSkeleton />}><QueryLibrary /></Suspense>} />
              <Route path="/my-queries" element={<Suspense fallback={<PageSkeleton />}><MyQueries /></Suspense>} />
              <Route path="/schedules" element={<Suspense fallback={<PageSkeleton />}><ScheduleManager /></Suspense>} />
              <Route path="/query-builder/new" element={<Suspense fallback={<PageSkeleton />}><QueryBuilder /></Suspense>} />
              <Route path="/query-builder/template/:templateId" element={<Suspense fallback={<PageSkeleton />}><QueryBuilder /></Suspense>} />
              <Route path="/query-builder/edit/:workflowId" element={<Suspense fallback={<PageSkeleton />}><QueryBuilder /></Suspense>} />
              <Route path="/query-builder/copy/:workflowId" element={<Suspense fallback={<PageSkeleton />}><QueryBuilder /></Suspense>} />

              {/* Data Sources routes */}
              <Route path="/data-sources" element={<Suspense fallback={<PageSkeleton />}><DataSources /></Suspense>} />
              <Route path="/data-sources/:schemaId" element={<Suspense fallback={<PageSkeleton />}><DataSourceDetail /></Suspense>} />

              {/* Build Guides routes */}
              <Route path="/build-guides" element={<Suspense fallback={<PageSkeleton />}><BuildGuides /></Suspense>} />
              <Route path="/build-guides/:guideId" element={<Suspense fallback={<PageSkeleton />}><BuildGuideDetail /></Suspense>} />

              {/* ASIN Management route */}
              <Route path="/asins" element={<Suspense fallback={<PageSkeleton />}><ASINManagement /></Suspense>} />

              {/* Reports & Analytics routes */}
              <Route path="/data-collections" element={<Suspense fallback={<PageSkeleton />}><DataCollections /></Suspense>} />
              <Route path="/report-builder" element={<Suspense fallback={<PageSkeleton />}><ReportBuilder /></Suspense>} />

              {/* Profile route */}
              <Route path="/profile" element={<Suspense fallback={<PageSkeleton />}><Profile /></Suspense>} />
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
