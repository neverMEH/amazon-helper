# JavaScript/TypeScript Style Guide

## Technology Stack

- **TypeScript 5.8.3** (strict mode enabled)
- **React 19.1.0** with functional components and hooks
- **ESLint 9** with TypeScript ESLint
- **Target**: ES2022 with modern JavaScript features

## TypeScript Configuration

### Compiler Options (tsconfig.app.json)
- `strict: true` - Full strict type checking
- `verbatimModuleSyntax: true` - Explicit type-only imports
- `noUnusedLocals: true` - No unused variables
- `noUnusedParameters: true` - No unused function parameters
- `jsx: "react-jsx"` - Modern JSX transform

## Import Organization

### Import Order (top to bottom)
```typescript
// 1. React and hooks
import { useState, useEffect, useMemo } from 'react';

// 2. External libraries (TanStack Query, React Router, etc.)
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';

// 3. Icons
import { Play, Save, X, AlertCircle } from 'lucide-react';

// 4. Utilities
import { toast } from 'react-hot-toast';

// 5. API/Services
import api from '../../services/api';

// 6. Local components
import SQLEditor from '../common/SQLEditor';
import JSONEditor from '../common/JSONEditor';

// 7. Type-only imports (must use 'type' keyword)
import type { User, Workflow } from '../types';
```

### Type-Only Imports (Required)
```typescript
// ALWAYS use 'import type' for types/interfaces
import type { MyType } from './types';  // ✅ Correct

// Value imports
import { myFunction } from './utils';    // ✅ Correct

// Don't mix types and values
import { MyType, myFunction } from './file';  // ❌ Wrong with verbatimModuleSyntax
```

## Naming Conventions

### Variables and Functions
```typescript
// camelCase for variables and functions
const userId = '123';
const isLoading = false;
const handleClick = () => {};

// PascalCase for components and classes
function MyComponent() {}
class ApiService {}

// UPPER_SNAKE_CASE for constants
const API_BASE_URL = 'https://api.example.com';
const MAX_RETRY_ATTEMPTS = 3;
```

### Type Definitions
```typescript
// PascalCase for interfaces and types
interface UserProfile {
  id: string;
  name: string;
  email: string;
}

type ComponentProps = {
  isOpen: boolean;
  onClose: () => void;
};

// Prefer interfaces over types for object shapes
interface User {  // ✅ Preferred
  id: string;
}

type User = {     // ⚠️ Use only when needed (unions, etc.)
  id: string;
};
```

## Function Declarations

### Component Functions
```typescript
// Default export for components (one per file)
export default function MyComponent({ prop1, prop2 }: MyComponentProps) {
  return <div>...</div>;
}
```

### Regular Functions
```typescript
// Named exports for utilities
export const calculateTotal = (items: Item[]): number => {
  return items.reduce((sum, item) => sum + item.price, 0);
};

// Async functions
export const fetchUserData = async (userId: string): Promise<User> => {
  const response = await api.get(`/users/${userId}`);
  return response.data;
};
```

## Type Annotations

### Explicit Return Types (Preferred)
```typescript
// Always specify return types for functions
const getUser = async (id: string): Promise<User> => {
  const response = await api.get(`/users/${id}`);
  return response.data;
};

// Return type for React components (optional but helpful)
const MyComponent = (): JSX.Element => {
  return <div>Hello</div>;
};
```

### Type Assertions
```typescript
// Use 'as' for type assertions (not angle brackets)
const value = someValue as string;  // ✅ Correct

const value = <string>someValue;    // ❌ Wrong (conflicts with JSX)
```

## State Management

### React Hooks
```typescript
// useState with explicit type
const [count, setCount] = useState<number>(0);
const [user, setUser] = useState<User | null>(null);

// useEffect with cleanup
useEffect(() => {
  const subscription = subscribe();

  return () => {
    subscription.unsubscribe();
  };
}, [dependency]);

// useMemo for expensive computations
const filteredItems = useMemo(() => {
  return items.filter(item => item.active);
}, [items]);

// useCallback for memoized callbacks
const handleClick = useCallback(() => {
  doSomething(prop);
}, [prop]);
```

### TanStack Query (React Query)
```typescript
// useQuery pattern
const { data, isLoading, error } = useQuery<Workflow>({
  queryKey: ['workflow', workflowId],
  queryFn: async () => {
    const response = await api.get(`/workflows/${workflowId}`);
    return response.data;
  },
  enabled: !!workflowId,  // Conditional fetching
  staleTime: 5 * 60 * 1000,  // 5 minutes
});

// useMutation pattern
const updateMutation = useMutation({
  mutationFn: async (data: UpdateData) => {
    const response = await api.put(`/workflows/${id}`, data);
    return response.data;
  },
  onSuccess: () => {
    toast.success('Updated successfully');
    queryClient.invalidateQueries({ queryKey: ['workflows'] });
  },
  onError: (error: unknown) => {
    toast.error('Failed to update');
  },
});
```

## Error Handling

### Try-Catch with Typed Errors
```typescript
// Type guard for error objects
const isErrorWithMessage = (error: unknown): error is { message: string } => {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as Record<string, unknown>).message === 'string'
  );
};

// Safe error handling
try {
  await riskyOperation();
} catch (error: unknown) {
  if (isErrorWithMessage(error)) {
    toast.error(error.message);
  } else {
    toast.error('An unknown error occurred');
  }
}
```

### Axios Error Handling
```typescript
import type { AxiosError } from 'axios';

try {
  await api.post('/endpoint', data);
} catch (error) {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>;
    const message = axiosError.response?.data?.detail || 'Request failed';
    toast.error(message);
  }
}
```

## Async/Await

### Always use async/await (not .then)
```typescript
// ✅ Correct - async/await
const fetchData = async () => {
  const response = await api.get('/data');
  return response.data;
};

// ❌ Wrong - .then() chains
const fetchData = () => {
  return api.get('/data').then(response => response.data);
};
```

## Object and Array Destructuring

```typescript
// Object destructuring in function params
function UserCard({ name, email, avatar }: UserProps) {
  return <div>...</div>;
}

// Array destructuring
const [first, second, ...rest] = items;

// Nested destructuring
const { data: { user } } = response;

// Default values
const { count = 0, items = [] } = data;
```

## Spread Operator

```typescript
// Object spread for immutable updates
const updatedUser = { ...user, name: 'New Name' };

// Array spread
const allItems = [...oldItems, ...newItems];

// Rest parameters
const handleClick = (...args: string[]) => {
  console.log(args);
};
```

## Conditional Expressions

```typescript
// Ternary for simple conditions
const message = isSuccess ? 'Success!' : 'Failed';

// Nullish coalescing (??)
const displayName = user.name ?? 'Anonymous';

// Optional chaining (?.)
const email = user?.profile?.email;

// Logical AND for conditional rendering
{isLoading && <LoadingSpinner />}
```

## Array Methods

```typescript
// map for transformations
const names = users.map(user => user.name);

// filter for subset
const activeUsers = users.filter(user => user.active);

// reduce for aggregations
const total = items.reduce((sum, item) => sum + item.price, 0);

// find for single item
const user = users.find(u => u.id === targetId);

// some/every for checks
const hasActive = users.some(user => user.active);
const allActive = users.every(user => user.active);
```

## Constants and Enums

```typescript
// Use const objects instead of enums
export const STATUS = {
  PENDING: 'pending',
  SUCCESS: 'success',
  ERROR: 'error',
} as const;

type Status = typeof STATUS[keyof typeof STATUS];

// Or use literal types
type Status = 'pending' | 'success' | 'error';
```

## Preparing for shadcn/ui

### Utility Function Pattern (shadcn uses this)
```typescript
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// cn utility for merging Tailwind classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage in components
<div className={cn('base-classes', isActive && 'active-classes')} />
```

### Component Variant Pattern
```typescript
// shadcn/ui uses class-variance-authority (cva)
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium',
  {
    variants: {
      variant: {
        default: 'bg-indigo-600 text-white hover:bg-indigo-700',
        outline: 'border border-gray-300 hover:bg-gray-50',
      },
      size: {
        sm: 'h-8 px-3 text-xs',
        md: 'h-10 px-4 text-sm',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);
```

## Anti-Patterns (Don't Do)

❌ **Don't use `any` type**
```typescript
const data: any = fetchData();  // ❌ Bad
const data: unknown = fetchData();  // ✅ Good
```

❌ **Don't use `var`**
```typescript
var count = 0;  // ❌ Bad
const count = 0;  // ✅ Good
let count = 0;  // ✅ Good for reassignment
```

❌ **Don't mutate arrays/objects**
```typescript
// ❌ Bad
items.push(newItem);

// ✅ Good
const newItems = [...items, newItem];
```

❌ **Don't use == (use ===)**
```typescript
if (value == null)  // ❌ Bad
if (value === null || value === undefined)  // ✅ Good
if (value == null)  // ⚠️ OK only for null/undefined check
```

## Best Practices

✅ Use TypeScript strict mode
✅ Prefer `const` over `let`, never use `var`
✅ Use explicit return types for functions
✅ Use type-only imports with `import type`
✅ Use async/await instead of .then()
✅ Use optional chaining and nullish coalescing
✅ Destructure objects and arrays for cleaner code
✅ Use array methods (map, filter, reduce) over loops
✅ Handle errors with proper type guards
✅ Keep functions small and focused
✅ Use meaningful variable names
✅ Comment only when necessary (code should be self-documenting)
