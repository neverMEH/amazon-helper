import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Plus } from 'lucide-react';

interface Brand {
  brand_tag: string;
  brand_name: string;
  source: string;
}

interface BrandSelectorProps {
  availableBrands: Brand[];
  selectedBrands: string[];
  onAddBrand: (brand: string) => void;
  placeholder?: string;
}

export default function BrandSelector({ 
  availableBrands, 
  selectedBrands, 
  onAddBrand,
  placeholder = "Add a brand..."
}: BrandSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter available brands based on search and exclude already selected
  const filteredBrands = availableBrands.filter(brand => 
    !selectedBrands.includes(brand.brand_tag) &&
    (brand.brand_tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
     brand.brand_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectBrand = (brand: Brand) => {
    onAddBrand(brand.brand_tag);
    setSearchTerm('');
    setIsOpen(false);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setIsOpen(true);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder={placeholder}
          className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        />
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="absolute inset-y-0 right-0 flex items-center px-2 text-gray-400 hover:text-gray-600"
        >
          <ChevronDown className="h-5 w-5" />
        </button>
      </div>

      {isOpen && filteredBrands.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {filteredBrands.map((brand) => (
            <button
              key={brand.brand_tag}
              onClick={() => handleSelectBrand(brand)}
              className="w-full px-3 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">{brand.brand_name}</div>
                  <div className="text-sm text-gray-500">{brand.brand_tag}</div>
                </div>
                <span className="text-xs text-gray-400">{brand.source}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {isOpen && searchTerm && filteredBrands.length === 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg p-3">
          <div className="text-sm text-gray-500">No brands found</div>
          {searchTerm.length >= 2 && (
            <button
              onClick={() => handleSelectBrand({ 
                brand_tag: searchTerm.toLowerCase(), 
                brand_name: searchTerm,
                source: 'custom' 
              })}
              className="mt-2 flex items-center text-sm text-indigo-600 hover:text-indigo-800"
            >
              <Plus className="h-4 w-4 mr-1" />
              Add "{searchTerm}" as new brand
            </button>
          )}
        </div>
      )}
    </div>
  );
}