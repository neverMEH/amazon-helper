import { X } from 'lucide-react';

interface BrandTagProps {
  brand: string;
  isEditable?: boolean;
  onRemove?: (brand: string) => void;
  size?: 'sm' | 'md' | 'lg';
}

export default function BrandTag({ brand, isEditable = false, onRemove, size = 'md' }: BrandTagProps) {
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base'
  };

  const baseClasses = 'inline-flex items-center font-medium rounded-full';
  const colorClasses = isEditable 
    ? 'bg-indigo-100 text-indigo-800 hover:bg-indigo-200' 
    : 'bg-indigo-100 text-indigo-800';

  return (
    <span className={`${baseClasses} ${sizeClasses[size]} ${colorClasses}`}>
      {brand}
      {isEditable && onRemove && (
        <button
          onClick={() => onRemove(brand)}
          className="ml-1.5 -mr-1 hover:text-indigo-900 focus:outline-none"
          aria-label={`Remove ${brand}`}
        >
          <X className={size === 'sm' ? 'h-3 w-3' : 'h-4 w-4'} />
        </button>
      )}
    </span>
  );
}