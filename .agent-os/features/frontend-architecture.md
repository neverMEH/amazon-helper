# Frontend Architecture

## Overview

The RecomAMP frontend is built with React 19.1.0, TypeScript 5.8, and modern development practices. It follows a component-based architecture with centralized state management, type safety, and performance optimization patterns.

## Recent Updates (2025-09-25)

### TypeScript Build Fixes (2025-09-25)
- **Fixed Docker Build Failures**: Resolved critical TypeScript compilation errors preventing production deployments
  - **Issues Fixed**:
    - Unused `result` variable in QueryLibrary.tsx causing compilation warnings treated as errors in strict mode
    - Various TypeScript strict mode violations across template components
    - Boolean type conversion issues in conditional expressions
    - Unused imports causing build failures
  - **Solutions Applied**:
    - Removed unused variables, imports, and function declarations
    - Fixed type declarations and explicit boolean conversions using `!!` operator
    - Corrected JSX syntax issues
    - Updated component interfaces to remove unused props
  - **Impact**: Production builds and Docker deployments now complete successfully
  - **Files**: `/frontend/src/pages/QueryLibrary.tsx`, template components throughout query-library directory

### Query Library Redesign Components Implementation (2025-09-12)
- **New Components**: Added advanced Query Library components with enhanced parameter handling
  - `/frontend/src/components/query-library/CampaignSelector.tsx` - Enhanced campaign selection with wildcard patterns
  - `/frontend/src/components/query-library/DateRangePicker.tsx` - Advanced date picker with presets and dynamic expressions
- **Features**: Wildcard pattern support (`Brand_*`, `*_2025`), bulk selection, AMC 14-day lookback support
- **Testing**: Comprehensive test suites with 95+ test scenarios for user interactions and accessibility
- **TypeScript**: Fixed compilation errors with boolean type conversion and unused import cleanup
- **Performance**: React-window virtualization for large datasets, debounced search, optimistic updates

### Campaign Page Routing Fix (2025-09-11)
- **Issue**: The CampaignsOptimized component was using incorrect API endpoint `/campaigns` instead of `/campaigns/`
- **Fix**: Updated API service calls to include proper trailing slash for backend compatibility
- **File**: `frontend/src/pages/CampaignsOptimized.tsx`
- **Impact**: Resolved 404 errors when loading the campaigns page
- **Technical**: Fixed routing mismatch between frontend and backend API expectations

## Technology Stack

### Core Technologies
- **React 19.1.0** - Component framework with latest features
- **TypeScript 5.8** - Type safety and developer experience
- **Vite** - Fast build tool and development server
- **React Router v7** - Client-side routing
- **TanStack Query v5** - Server state management and caching

### UI and Styling
- **Tailwind CSS** - Utility-first CSS framework
- **Tailwind Forms Plugin** - Form styling
- **Tailwind Typography Plugin** - Rich text styling
- **Monaco Editor** - SQL code editor
- **Chart.js with react-chartjs-2** - Data visualization

## Project Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── common/          # Generic components (Button, Modal, etc.)
│   │   ├── forms/           # Form-specific components
│   │   ├── layout/          # Layout components (Header, Sidebar)
│   │   ├── charts/          # Chart and visualization components
│   │   └── domain/          # Domain-specific components
│   ├── pages/               # Route-level page components
│   │   ├── auth/           # Authentication pages
│   │   ├── workflows/      # Workflow management pages
│   │   ├── dashboards/     # Dashboard pages
│   │   └── settings/       # Settings and configuration
│   ├── services/           # API service layer
│   │   ├── api.ts          # Base API client
│   │   ├── auth.service.ts # Authentication service
│   │   ├── workflow.service.ts # Workflow operations
│   │   └── [domain].service.ts # Domain services
│   ├── hooks/              # Custom React hooks
│   │   ├── useAuth.ts      # Authentication hook
│   │   ├── useApi.ts       # API integration hooks
│   │   └── use[Feature].ts # Feature-specific hooks
│   ├── contexts/           # React contexts
│   │   ├── AuthContext.tsx # Authentication context
│   │   └── ThemeContext.tsx # Theme management
│   ├── types/              # TypeScript type definitions
│   │   ├── api.types.ts    # API response types
│   │   ├── domain.types.ts # Domain entity types
│   │   └── common.types.ts # Shared types
│   ├── utils/              # Utility functions
│   │   ├── formatters.ts   # Data formatting
│   │   ├── validators.ts   # Input validation
│   │   └── helpers.ts      # Generic helpers
│   ├── constants/          # Application constants
│   ├── assets/            # Static assets
│   └── styles/            # Global styles
├── public/                 # Static files
├── dist/                  # Production build output
├── tests/                 # Test files
│   ├── components/        # Component tests
│   ├── pages/            # Page tests
│   ├── services/         # Service tests
│   └── e2e/              # End-to-end tests
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── playwright.config.ts
```

## Core Architecture Patterns

### Component Architecture
```typescript
// Component structure following React best practices
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface ComponentProps {
  // Always define proper TypeScript interfaces
  id: string;
  title: string;
  onUpdate?: (data: any) => void;
  className?: string;
}

export const ExampleComponent: React.FC<ComponentProps> = ({
  id,
  title,
  onUpdate,
  className = ''
}) => {
  // Hooks at the top
  const [localState, setLocalState] = useState<string>('');
  const queryClient = useQueryClient();
  
  // API queries
  const { data, isLoading, error } = useQuery({
    queryKey: ['example', id],
    queryFn: () => exampleService.getById(id),
    enabled: !!id
  });
  
  // Mutations
  const updateMutation = useMutation({
    mutationFn: exampleService.update,
    onSuccess: (data) => {
      queryClient.invalidateQueries(['example']);
      onUpdate?.(data);
    }
  });
  
  // Effects
  useEffect(() => {
    // Side effects here
  }, [id]);
  
  // Event handlers
  const handleUpdate = (newData: any) => {
    updateMutation.mutate({ id, ...newData });
  };
  
  // Early returns for loading/error states
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return <EmptyState />;
  
  // Main render
  return (
    <div className={`component-wrapper ${className}`}>
      <h2>{title}</h2>
      {/* Component content */}
    </div>
  );
};
```

### State Management Architecture
```typescript
// TanStack Query configuration
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,        // 5 minutes
      gcTime: 10 * 60 * 1000,          // 10 minutes (replaces cacheTime)
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      retry: (failureCount, error) => {
        // Custom retry logic
        if (error.status === 404) return false;
        return failureCount < 3;
      }
    },
    mutations: {
      retry: 1
    }
  }
});

// Query key factory pattern
export const queryKeys = {
  workflows: ['workflows'] as const,
  workflow: (id: string) => ['workflows', id] as const,
  workflowExecutions: (workflowId: string) => ['workflow-executions', workflowId] as const,
  
  instances: ['instances'] as const,
  instance: (id: string) => ['instances', id] as const,
  
  campaigns: (instanceId?: string) => 
    instanceId ? ['campaigns', instanceId] : ['campaigns'] as const,
    
  // Infinite query keys
  workflowsList: (filters: WorkflowFilters) => ['workflows', 'list', filters] as const,
};

// Custom hooks for common patterns
export const useWorkflow = (workflowId: string) => {
  return useQuery({
    queryKey: queryKeys.workflow(workflowId),
    queryFn: () => workflowService.getById(workflowId),
    enabled: !!workflowId
  });
};

export const useWorkflows = (filters: WorkflowFilters = {}) => {
  return useQuery({
    queryKey: queryKeys.workflowsList(filters),
    queryFn: () => workflowService.list(filters)
  });
};
```

### Service Layer Pattern
```typescript
// api.ts - Base API client
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

class APIClient {
  private client: AxiosInstance;
  
  constructor(baseURL: string = '/api') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors() {
    // Request interceptor for auth
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token expiry
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        
        // Transform error for consistent handling
        const apiError = new APIError(
          error.response?.data?.message || error.message,
          error.response?.status || 500,
          error.response?.data
        );
        
        return Promise.reject(apiError);
      }
    );
  }
  
  // Generic CRUD methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get(url, config);
    return response.data;
  }
  
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post(url, data, config);
    return response.data;
  }
  
  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put(url, data, config);
    return response.data;
  }
  
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete(url, config);
    return response.data;
  }
}

export const apiClient = new APIClient();
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}
```

### Domain Service Pattern
```typescript
// workflow.service.ts - Domain-specific service
import { apiClient } from './api';
import type { 
  Workflow, 
  WorkflowExecution, 
  CreateWorkflowRequest, 
  ExecuteWorkflowRequest,
  WorkflowFilters 
} from '../types/workflow.types';

class WorkflowService {
  private readonly basePath = '/workflows';
  
  async list(filters?: WorkflowFilters): Promise<Workflow[]> {
    const params = new URLSearchParams();
    
    if (filters?.instance_id) {
      params.append('instance_id', filters.instance_id);
    }
    if (filters?.search) {
      params.append('search', filters.search);
    }
    if (filters?.tags?.length) {
      params.append('tags', filters.tags.join(','));
    }
    
    const queryString = params.toString();
    const url = queryString ? `${this.basePath}?${queryString}` : this.basePath;
    
    return apiClient.get<Workflow[]>(url);
  }
  
  async getById(id: string): Promise<Workflow> {
    return apiClient.get<Workflow>(`${this.basePath}/${id}`);
  }
  
  async create(data: CreateWorkflowRequest): Promise<Workflow> {
    return apiClient.post<Workflow>(`${this.basePath}/`, data); // Note trailing slash
  }
  
  async update(id: string, data: Partial<CreateWorkflowRequest>): Promise<Workflow> {
    return apiClient.put<Workflow>(`${this.basePath}/${id}`, data);
  }
  
  async delete(id: string): Promise<void> {
    return apiClient.delete(`${this.basePath}/${id}`);
  }
  
  async execute(id: string, data: ExecuteWorkflowRequest): Promise<WorkflowExecution> {
    return apiClient.post<WorkflowExecution>(`${this.basePath}/${id}/execute`, data);
  }
  
  async getExecutions(workflowId: string): Promise<WorkflowExecution[]> {
    return apiClient.get<WorkflowExecution[]>(`${this.basePath}/${workflowId}/executions`);
  }
  
  async getExecutionResults(executionId: string): Promise<any> {
    return apiClient.get(`/executions/${executionId}/results`);
  }
  
  // Preview query with parameters
  async previewQuery(id: string, parameters: Record<string, any>): Promise<{ sql: string }> {
    return apiClient.post<{ sql: string }>(`${this.basePath}/${id}/preview`, { parameters });
  }
}

export const workflowService = new WorkflowService();
```

## Component Library

### Common Components
```typescript
// Button component with variants
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    ghost: 'text-gray-700 hover:bg-gray-100 focus:ring-gray-500'
  };
  
  const sizeClasses = {
    sm: 'px-2.5 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  const isDisabled = disabled || loading;
  
  return (
    <button
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
        ${className}
      `}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      
      {icon && !loading && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
};
```

### Form Components
```typescript
// FormField wrapper component
interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  help?: string;
  children: React.ReactNode;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  required,
  help,
  children
}) => {
  return (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      
      {children}
      
      {help && (
        <p className="text-sm text-gray-500">{help}</p>
      )}
      
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
};

// Input component with validation
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input: React.FC<InputProps> = ({
  error,
  className = '',
  ...props
}) => {
  return (
    <input
      className={`
        block w-full px-3 py-2 border rounded-md shadow-sm
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
        ${error 
          ? 'border-red-300 text-red-900 placeholder-red-300' 
          : 'border-gray-300'
        }
        ${className}
      `}
      {...props}
    />
  );
};
```

### Modal System
```typescript
// Modal with portal rendering
import { createPortal } from 'react-dom';
import { useEffect, useState } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  size = 'md',
  children
}) => {
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);
  
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);
  
  if (!mounted || !isOpen) return null;
  
  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-7xl'
  };
  
  const modalContent = (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />
        
        {/* Modal */}
        <div className={`
          relative w-full ${sizeClasses[size]} bg-white rounded-lg shadow-xl
          transform transition-all
        `}>
          {title && (
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">{title}</h3>
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          
          <div className="px-6 py-4">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
  
  return createPortal(modalContent, document.body);
};
```

## Custom Hooks

### API Integration Hooks
```typescript
// useAPI hook for common patterns
export const useWorkflowExecution = (workflowId: string, parameters?: Record<string, any>) => {
  return useMutation({
    mutationFn: () => workflowService.execute(workflowId, { parameters }),
    onSuccess: (execution) => {
      // Invalidate related queries
      queryClient.invalidateQueries(queryKeys.workflowExecutions(workflowId));
      
      // Start polling for execution status
      queryClient.invalidateQueries(['execution-status', execution.id]);
    }
  });
};

// Polling hook for execution status
export const useExecutionStatus = (executionId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['execution-status', executionId],
    queryFn: () => executionService.getStatus(executionId),
    enabled: enabled && !!executionId,
    refetchInterval: (data) => {
      // Stop polling when execution is complete
      if (data?.status && ['SUCCESS', 'FAILED', 'CANCELLED'].includes(data.status)) {
        return false;
      }
      return 5000; // Poll every 5 seconds
    },
    refetchIntervalInBackground: true
  });
};

// Form state management hook
export const useFormState = <T>(initialState: T) => {
  const [state, setState] = useState<T>(initialState);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  
  const updateField = (field: keyof T, value: any) => {
    setState(prev => ({ ...prev, [field]: value }));
    
    // Clear error when field is updated
    if (errors[field as string]) {
      setErrors(prev => ({ ...prev, [field as string]: '' }));
    }
  };
  
  const touchField = (field: keyof T) => {
    setTouched(prev => ({ ...prev, [field as string]: true }));
  };
  
  const validate = (validationRules: Record<string, (value: any) => string | null>) => {
    const newErrors: Record<string, string> = {};
    
    Object.entries(validationRules).forEach(([field, validator]) => {
      const error = validator(state[field as keyof T]);
      if (error) {
        newErrors[field] = error;
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const reset = () => {
    setState(initialState);
    setErrors({});
    setTouched({});
  };
  
  return {
    state,
    errors,
    touched,
    updateField,
    touchField,
    validate,
    reset,
    isValid: Object.keys(errors).length === 0
  };
};
```

### Local Storage Hook
```typescript
// useLocalStorage hook with TypeScript support
export const useLocalStorage = <T>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });
  
  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  };
  
  const removeValue = () => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  };
  
  return [storedValue, setValue, removeValue] as const;
};
```

## TypeScript Configuration

### Type Definitions
```typescript
// api.types.ts - API response types
export interface APIResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> extends APIResponse<T[]> {
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}

export interface APIError {
  message: string;
  status: number;
  errors?: Record<string, string[]>;
}

// workflow.types.ts - Domain types
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  sql_query: string;
  user_id: string;
  instance_id: string;
  template_id?: string;
  parameters: Record<string, any>;
  tags: string[];
  is_public: boolean;
  created_at: string;
  updated_at: string;
  last_executed_at?: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  user_id: string;
  amc_execution_id?: string;
  status: ExecutionStatus;
  parameters: Record<string, any>;
  result_data?: any;
  result_rows?: number;
  execution_duration?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export type ExecutionStatus = 
  | 'PENDING' 
  | 'RUNNING' 
  | 'SUCCESS' 
  | 'FAILED' 
  | 'CANCELLED' 
  | 'TIMEOUT';

export interface CreateWorkflowRequest {
  name: string;
  description?: string;
  sql_query: string;
  instance_id: string;
  template_id?: string;
  parameters?: Record<string, any>;
  tags?: string[];
  is_public?: boolean;
}
```

## Performance Optimization

### Code Splitting
```typescript
// Lazy loading for route components
import { lazy, Suspense } from 'react';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

// Lazy load heavy components
const WorkflowDetail = lazy(() => import('../pages/WorkflowDetail'));
const DashboardBuilder = lazy(() => import('../pages/DashboardBuilder'));
const QueryTemplates = lazy(() => import('../pages/QueryTemplates'));

// Route configuration with lazy loading
export const routes = [
  {
    path: '/workflows/:id',
    element: (
      <Suspense fallback={<LoadingSpinner />}>
        <WorkflowDetail />
      </Suspense>
    )
  }
];

// Component-level code splitting
const MonacoEditor = lazy(() => import('@monaco-editor/react'));

export const SQLEditor = (props) => (
  <Suspense fallback={<div>Loading editor...</div>}>
    <MonacoEditor {...props} />
  </Suspense>
);
```

### Memoization Patterns
```typescript
// React.memo for component memoization
export const WorkflowCard = React.memo<WorkflowCardProps>(({ workflow, onUpdate }) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison function
  return prevProps.workflow.id === nextProps.workflow.id &&
         prevProps.workflow.updated_at === nextProps.workflow.updated_at;
});

// useMemo for expensive calculations
const processedData = useMemo(() => {
  return data?.map(item => ({
    ...item,
    formatted_date: formatDate(item.date),
    calculated_metric: expensiveCalculation(item.values)
  }));
}, [data]);

// useCallback for stable function references
const handleWorkflowUpdate = useCallback((workflowId: string, updates: any) => {
  updateMutation.mutate({ id: workflowId, ...updates });
}, [updateMutation]);
```

## Testing Strategy

### Component Testing with Vitest
```typescript
// WorkflowCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WorkflowCard } from './WorkflowCard';
import { vi } from 'vitest';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
});

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

describe('WorkflowCard', () => {
  const mockWorkflow = {
    id: '123',
    name: 'Test Workflow',
    description: 'Test description',
    status: 'active',
    last_executed_at: '2023-01-01T00:00:00Z'
  };
  
  it('renders workflow information correctly', () => {
    renderWithProviders(
      <WorkflowCard workflow={mockWorkflow} onUpdate={vi.fn()} />
    );
    
    expect(screen.getByText('Test Workflow')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
  });
  
  it('calls onUpdate when edit button is clicked', async () => {
    const mockOnUpdate = vi.fn();
    
    renderWithProviders(
      <WorkflowCard workflow={mockWorkflow} onUpdate={mockOnUpdate} />
    );
    
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    
    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalledWith(mockWorkflow);
    });
  });
});
```

### E2E Testing with Playwright
```typescript
// workflow-management.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Workflow Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'test@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    
    // Wait for dashboard
    await page.waitForURL('/dashboard');
  });
  
  test('can create a new workflow', async ({ page }) => {
    await page.goto('/workflows');
    await page.click('button:has-text("New Workflow")');
    
    // Fill form
    await page.fill('[name="name"]', 'Test E2E Workflow');
    await page.fill('[name="description"]', 'Created via E2E test');
    
    // SQL editor interaction
    await page.click('.monaco-editor');
    await page.keyboard.type('SELECT * FROM campaigns LIMIT 10');
    
    // Save workflow
    await page.click('button:has-text("Save")');
    
    // Verify creation
    await expect(page).toHaveURL(/\/workflows\/\w+/);
    await expect(page.locator('h1')).toContainText('Test E2E Workflow');
  });
  
  test('can execute a workflow', async ({ page }) => {
    await page.goto('/workflows/test-workflow-id');
    
    // Execute workflow
    await page.click('button:has-text("Execute")');
    
    // Wait for execution to start
    await expect(page.locator('[data-testid="execution-status"]')).toContainText('Running');
    
    // Wait for completion (with timeout)
    await expect(page.locator('[data-testid="execution-status"]')).toContainText('Success', { timeout: 30000 });
    
    // Verify results are displayed
    await expect(page.locator('[data-testid="results-table"]')).toBeVisible();
  });
});
```

This frontend architecture provides a scalable, maintainable, and type-safe foundation for RecomAMP's user interface, following React and TypeScript best practices while ensuring excellent developer experience and application performance.