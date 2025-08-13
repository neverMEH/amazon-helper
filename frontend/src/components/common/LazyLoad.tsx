import { Suspense, lazy } from 'react';
import type { ComponentType } from 'react';
import { Loader } from 'lucide-react';

interface LazyLoadProps {
  loader: () => Promise<{ default: ComponentType<any> }>;
  fallback?: React.ReactNode;
  props?: any;
}

export function LazyLoad({ loader, fallback, props = {} }: LazyLoadProps) {
  const Component = lazy(loader);
  
  const defaultFallback = (
    <div className="flex items-center justify-center p-8">
      <Loader className="h-8 w-8 animate-spin text-gray-400" />
    </div>
  );

  return (
    <Suspense fallback={fallback || defaultFallback}>
      <Component {...props} />
    </Suspense>
  );
}

// Pre-configured lazy components
export const LazyDataVisualization = lazy(() => import('../executions/DataVisualization'));
export const LazyEnhancedResultsTable = lazy(() => import('../executions/EnhancedResultsTable'));
export const LazyExecutionDetailModal = lazy(() => import('../workflows/ExecutionDetailModal'));