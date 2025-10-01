# CSS Style Guide

## Technology Stack

- **Tailwind CSS v3.4.1** - Utility-first CSS framework
- **Plugins**: `@tailwindcss/forms`, `@tailwindcss/typography`
- **No custom CSS files** - All styling via Tailwind utilities
- **Index CSS**: Only imports Tailwind directives (`@tailwind base/components/utilities`)

## Class Organization

### Single-Line Classes (Preferred)
For most components, use single-line class strings with template literals for dynamic values:

```tsx
<button className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700">
  Click Me
</button>
```

### Dynamic Classes with Conditionals
Use template literals for conditional styling:

```tsx
<span className={`inline-flex items-center px-3 py-1 text-sm font-medium rounded-full ${
  isEditable ? 'bg-indigo-100 text-indigo-800 hover:bg-indigo-200' : 'bg-indigo-100 text-indigo-800'
}`}>
```

### Size Variants
Define size variants as objects for consistency:

```tsx
const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-1.5 text-base'
};

<div className={`${baseClasses} ${sizeClasses[size]} ${colorClasses}`}>
```

## Layout Patterns

### Common Class Combinations

**Flex Container (Common)**
```tsx
<div className="flex items-center space-x-2">
<div className="flex items-center justify-between">
<div className="inline-flex items-center">
```

**Cards/Panels**
```tsx
<div className="bg-white border-b border-gray-200 px-6 py-3">
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
```

**Buttons**
```tsx
// Primary
className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"

// Secondary
className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
```

**Text Styling**
```tsx
// Headings
className="text-lg font-medium text-gray-900"
className="text-sm font-medium text-gray-700"

// Body
className="text-sm text-gray-500 hover:text-gray-700"
```

## Custom Animations

Defined in [tailwind.config.js](../../frontend/tailwind.config.js):

```tsx
// Available animations
className="animate-fade-in"
className="animate-slide-up"
className="animate-slide-down"
className="animate-scale-in"
className="animate-spin" // Built-in
```

## Color Palette

**Primary Colors**: Indigo (`indigo-50` through `indigo-900`)
**Status Colors**:
- Success: `green-50/600/700`
- Error: `red-50/600/700`
- Warning: `yellow-50/600/700`
- Info: `blue-50/600/700`

**Neutrals**: Gray scale (`gray-50` through `gray-900`)

## Component-Specific Patterns

### Loading States
```tsx
<div className="animate-spin rounded-full border-b-2 border-blue-600 h-8 w-8">
```

### Transitions
```tsx
className="transition-colors" // For hover effects
className="transition-all" // For complex state changes
```

### Focus States
Always include focus states for accessibility:
```tsx
className="focus:outline-none focus:ring-2 focus:ring-indigo-500"
```

## Anti-Patterns (Don't Do)

❌ **Don't use multi-line class strings**
```tsx
// Bad
<div className="bg-gray-50
               hover:bg-gray-100
               sm:p-8">
```

❌ **Don't create custom CSS classes**
```css
/* Bad - Avoid custom CSS */
.custom-button { ... }
```

❌ **Don't use inline styles**
```tsx
// Bad
<div style={{ padding: '16px' }}>
```

## Best Practices

✅ Keep classes on a single line for readability
✅ Use object-based variants for size/state variations
✅ Extract repeated patterns into reusable components
✅ Use Tailwind's built-in utilities before creating custom solutions
✅ Include accessibility classes (focus, aria-label, etc.)
✅ Maintain consistent spacing (prefer `space-x-*` over individual margins)
