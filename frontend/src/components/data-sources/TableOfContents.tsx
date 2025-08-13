import { useEffect, useState } from 'react';
import { ChevronRight, Hash, BookOpen } from 'lucide-react';

interface TOCItem {
  id: string;
  title: string;
  level: number;
  active?: boolean;
}

interface TableOfContentsProps {
  sections: TOCItem[];
  activeSection: string;
  onSectionClick: (id: string) => void;
}

export function TableOfContents({ sections, activeSection, onSectionClick }: TableOfContentsProps) {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPosition = window.scrollY;
      const progress = (scrollPosition / scrollHeight) * 100;
      setScrollProgress(progress);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav className="sticky top-24 max-h-[calc(100vh-120px)] overflow-y-auto">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Table of Contents
          </h3>
          {/* Progress bar */}
          <div className="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-blue-500 transition-all duration-150 ease-out"
              style={{ width: `${scrollProgress}%` }}
            />
          </div>
        </div>

        {/* Sections */}
        <div className="py-2">
          {sections.map((section) => {
            const isActive = section.id === activeSection;
            const paddingLeft = `${(section.level - 1) * 12 + 16}px`;
            
            return (
              <button
                key={section.id}
                onClick={() => onSectionClick(section.id)}
                className={`
                  w-full text-left px-4 py-2 text-sm transition-all duration-200
                  hover:bg-gray-50 relative group
                  ${isActive 
                    ? 'bg-blue-50 text-blue-700 font-medium border-l-2 border-blue-500' 
                    : 'text-gray-600 hover:text-gray-900'
                  }
                `}
                style={{ paddingLeft }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {section.level === 1 ? (
                      <Hash className="h-3 w-3 opacity-50" />
                    ) : (
                      <ChevronRight className={`h-3 w-3 opacity-50 transition-transform ${
                        isActive ? 'rotate-90' : ''
                      }`} />
                    )}
                    <span className="truncate">{section.title}</span>
                  </div>
                  {isActive && (
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full animate-pulse" />
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-4 bg-white rounded-lg border border-gray-200 shadow-sm p-4">
        <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Quick Actions
        </h4>
        <div className="space-y-2">
          <button className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md transition-colors">
            Copy Schema ID
          </button>
          <button className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md transition-colors">
            Export Documentation
          </button>
          <button className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-md transition-colors">
            View in Query Builder
          </button>
        </div>
      </div>
    </nav>
  );
}