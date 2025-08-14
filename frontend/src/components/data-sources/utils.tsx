/**
 * Utility functions for data source components
 */

import type { ReactElement } from 'react';

/**
 * Highlights matching text in a string
 */
export function highlightMatch(text: string, query: string): ReactElement {
  if (!query || query.length < 2) return <>{text}</>;
  
  try {
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const parts = text.split(new RegExp(`(${escapedQuery})`, 'gi'));
    
    return (
      <>
        {parts.map((part, i) => 
          part.toLowerCase() === query.toLowerCase() ? (
            <mark key={i} className="bg-yellow-100 text-gray-900 px-0.5 rounded">{part}</mark>
          ) : (
            <span key={i}>{part}</span>
          )
        )}
      </>
    );
  } catch {
    return <>{text}</>;
  }
}

/**
 * Gets complexity level based on field count
 */
export function getComplexityLevel(fieldCount: number): { 
  label: string; 
  color: string; 
  bgColor: string;
} {
  if (fieldCount < 20) {
    return { 
      label: 'Simple', 
      color: 'text-green-700', 
      bgColor: 'bg-green-50' 
    };
  }
  if (fieldCount < 50) {
    return { 
      label: 'Medium', 
      color: 'text-yellow-700', 
      bgColor: 'bg-yellow-50' 
    };
  }
  return { 
    label: 'Complex', 
    color: 'text-red-700', 
    bgColor: 'bg-red-50' 
  };
}

/**
 * Truncates text to a maximum length with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}