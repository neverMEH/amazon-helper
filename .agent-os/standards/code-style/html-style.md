# HTML/JSX Style Guide

## Technology Stack

- **React 19.1.0** with TypeScript 5.8
- **JSX/TSX** for component markup
- **React Router v7** for navigation
- **Preparing for shadcn/ui** transition (component library coming soon)

## Component Structure

### File Organization
```tsx
// 1. Imports (grouped by category)
import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { Play, Save, X } from 'lucide-react';
import { toast } from 'react-hot-toast';

// 2. Import from local services
import api from '../../services/api';

// 3. Import local components
import SQLEditor from '../common/SQLEditor';
import JSONEditor from '../common/JSONEditor';

// 4. Types/Interfaces
interface MyComponentProps {
  id: string;
  isOpen: boolean;
  onClose: () => void;
}

// 5. Component definition
export default function MyComponent({ id, isOpen, onClose }: MyComponentProps) {
  // Component logic
  return (
    // JSX
  );
}
```

### JSX Formatting

**Single-line for simple elements:**
```tsx
<button className="px-4 py-2 bg-indigo-600 text-white rounded-md">
  Click Me
</button>
```

**Multi-line for complex elements:**
```tsx
<button
  onClick={handleClick}
  disabled={isLoading}
  className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
>
  {isLoading ? 'Loading...' : 'Submit'}
</button>
```

**Conditional rendering patterns:**
```tsx
// Ternary for two states
{isLoading ? <LoadingSpinner /> : <Content />}

// && for single conditional
{error && <ErrorMessage message={error} />}

// Early return for complex conditions
if (!data) return <LoadingSpinner />;
```

## Component Patterns

### Modal Structure
```tsx
{isOpen && (
  <div className="fixed inset-0 z-50 overflow-y-auto">
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="fixed inset-0 bg-black bg-opacity-25" onClick={onClose} />
      <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full">
        {/* Modal content */}
      </div>
    </div>
  </div>
)}
```

### Form Elements
```tsx
<div className="space-y-4">
  <div>
    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
      Name
    </label>
    <input
      id="name"
      type="text"
      value={name}
      onChange={(e) => setName(e.target.value)}
      className="mt-1 block w-full rounded-md border-gray-300"
    />
  </div>
</div>
```

### Lists and Mapping
```tsx
<ul className="space-y-2">
  {items.map((item) => (
    <li key={item.id} className="flex items-center space-x-2">
      <span>{item.name}</span>
    </li>
  ))}
</ul>
```

## Accessibility

### Always include:
```tsx
// Labels with htmlFor
<label htmlFor="email">Email</label>
<input id="email" type="email" />

// Alt text for images
<img src={url} alt="Descriptive text" />

// aria-label for icon buttons
<button aria-label="Close modal">
  <X className="h-5 w-5" />
</button>

// aria-label for navigation
<nav className="flex" aria-label="Breadcrumb">
```

## Icon Usage (Lucide React)

```tsx
import { Play, Save, X, AlertCircle, CheckCircle } from 'lucide-react';

// Standard sizes
<Play className="h-5 w-5" />  // Default
<Play className="h-4 w-4" />  // Small
<Play className="h-6 w-6" />  // Large

// With color
<CheckCircle className="h-5 w-5 text-green-600" />
```

## Preparing for shadcn/ui

### Current Component Patterns
The project currently uses custom components. When transitioning to shadcn/ui:

**Button Component (Current):**
```tsx
<button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
  Click Me
</button>
```

**Button Component (Future with shadcn/ui):**
```tsx
import { Button } from "@/components/ui/button"

<Button variant="default" size="default">
  Click Me
</Button>
```

**Dialog/Modal (Current):**
```tsx
{isOpen && (
  <div className="fixed inset-0 z-50">
    {/* Custom modal implementation */}
  </div>
)}
```

**Dialog/Modal (Future with shadcn/ui):**
```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
      <DialogDescription>Description</DialogDescription>
    </DialogHeader>
    {/* Content */}
  </DialogContent>
</Dialog>
```

### shadcn/ui Setup Notes
When transitioning:
1. Install: `npx shadcn@latest init`
2. Add path alias `@/` to tsconfig
3. Install components as needed: `npx shadcn@latest add button`
4. Components will be in `src/components/ui/`
5. Fully customizable with Tailwind

## TypeScript Props

### Always use interfaces for props:
```tsx
interface MyComponentProps {
  id: string;
  isOpen: boolean;
  onClose: () => void;
  data?: MyData;  // Optional with ?
  children?: React.ReactNode;  // For children
}

export default function MyComponent({
  id,
  isOpen,
  onClose,
  data,
  children
}: MyComponentProps) {
  // Component logic
}
```

### Type-only imports:
```tsx
// TypeScript 5.8+ with verbatimModuleSyntax
import type { User } from '../types';  // Type-only import
import { fetchUser } from '../api';     // Value import
```

## Event Handlers

```tsx
// Inline for simple handlers
<button onClick={() => setCount(count + 1)}>

// Named functions for complex logic
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  // Complex logic
};

<form onSubmit={handleSubmit}>
```

## Anti-Patterns (Don't Do)

❌ **Don't use class components**
```tsx
// Bad - Use functional components
class MyComponent extends React.Component { }
```

❌ **Don't use default exports for non-components**
```tsx
// Bad
export default { apiMethod1, apiMethod2 };

// Good
export const api = { apiMethod1, apiMethod2 };
```

❌ **Don't put multiple attributes on one line**
```tsx
// Bad
<button onClick={handleClick} disabled={isLoading} className="..." aria-label="Submit">

// Good
<button
  onClick={handleClick}
  disabled={isLoading}
  className="..."
  aria-label="Submit"
>
```

## Best Practices

✅ Use semantic HTML elements (`<nav>`, `<header>`, `<main>`, `<article>`)
✅ Always provide `key` prop when mapping arrays
✅ Use `htmlFor` on labels, not `for`
✅ Extract complex JSX into separate components
✅ Use fragments (`<>`) to avoid unnecessary divs
✅ Keep components focused and single-purpose
✅ Prefer controlled components for forms
✅ Use React hooks (useState, useEffect, useMemo, useCallback)
✅ Implement proper TypeScript types for all props
