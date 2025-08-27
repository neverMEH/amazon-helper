# Campaigns Page Optimization Specification

## Overview
This specification outlines improvements to the campaigns page to enhance sorting, filtering, and optimize brand dropdown performance.

## Current Issues
1. **Brand Dropdown Performance**: Currently fetches all campaigns to extract unique brands (inefficient with large datasets)
2. **Limited Sorting Options**: Only supports basic field sorting
3. **Filter Persistence**: Filters don't persist across sessions
4. **Loading States**: No skeleton loaders during data fetch

## Proposed Improvements

### 1. Brand Dropdown Optimization

#### Backend Changes

**New Endpoint**: `/api/campaigns/brands-optimized`
```python
@router.get("/brands-optimized")
def list_brands_optimized(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Optimized brand fetching using direct SQL query"""
    try:
        client = SupabaseManager.get_client(use_service_role=True)
        
        # Use RPC function for optimized brand aggregation
        result = client.rpc('get_campaign_brands_with_counts').execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error fetching brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch brands")
```

**Database Function** (to be created):
```sql
CREATE OR REPLACE FUNCTION get_campaign_brands_with_counts()
RETURNS TABLE (
    brand TEXT,
    campaign_count BIGINT,
    enabled_count BIGINT,
    paused_count BIGINT,
    archived_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.brand,
        COUNT(*) as campaign_count,
        COUNT(*) FILTER (WHERE c.state = 'ENABLED') as enabled_count,
        COUNT(*) FILTER (WHERE c.state = 'PAUSED') as paused_count,
        COUNT(*) FILTER (WHERE c.state = 'ARCHIVED') as archived_count
    FROM campaigns c
    WHERE c.brand IS NOT NULL
    GROUP BY c.brand
    ORDER BY c.brand;
END;
$$;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_campaigns_brand_state 
ON campaigns(brand, state) 
WHERE brand IS NOT NULL;
```

#### Frontend Changes

**Optimized Brand Query**:
```typescript
// Use separate query with aggressive caching
const { data: brands, isLoading: brandsLoading } = useQuery<BrandInfo[]>({
  queryKey: ['campaign-brands-optimized'],
  queryFn: async () => {
    const response = await api.get('/campaigns/brands-optimized');
    return response.data;
  },
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 30 * 60 * 1000,   // 30 minutes
  refetchOnWindowFocus: false, // Don't refetch on focus for brands
});
```

### 2. Enhanced Sorting

#### Backend Changes

**Extended Sorting Options**:
```python
@router.get("")
def list_campaigns(
    # ... existing parameters ...
    sort_by: str = Query(
        "name", 
        description="Sort by: name, brand, state, campaign_id, created_at, updated_at, spend, impressions"
    ),
    secondary_sort: Optional[str] = Query(
        None, 
        description="Secondary sort field"
    ),
    # ... rest ...
) -> Dict[str, Any]:
    """Enhanced sorting with secondary sort option"""
    # ... existing code ...
    
    # Apply primary and secondary sorting
    order_columns = {
        'name': 'name',
        'brand': 'brand', 
        'state': 'state',
        'campaign_id': 'campaign_id',
        'created_at': 'created_at',
        'updated_at': 'updated_at',
        'spend': 'total_spend',
        'impressions': 'total_impressions'
    }
    
    primary_column = order_columns.get(sort_by, 'name')
    query = query.order(primary_column, desc=(sort_order == 'desc'))
    
    if secondary_sort and secondary_sort != sort_by:
        secondary_column = order_columns.get(secondary_sort, 'campaign_id')
        query = query.order(secondary_column, desc=False)
```

#### Frontend Changes

**Multi-column Sort UI**:
```tsx
// Add sort indicators and multi-column support
interface SortConfig {
  primary: string;
  primaryOrder: 'asc' | 'desc';
  secondary?: string;
  secondaryOrder?: 'asc' | 'desc';
}

const [sortConfig, setSortConfig] = useState<SortConfig>({
  primary: 'name',
  primaryOrder: 'asc'
});

const handleSort = (column: string, isShiftClick: boolean = false) => {
  if (isShiftClick && column !== sortConfig.primary) {
    // Add as secondary sort
    setSortConfig(prev => ({
      ...prev,
      secondary: column,
      secondaryOrder: 'asc'
    }));
  } else if (column === sortConfig.primary) {
    // Toggle primary sort order
    setSortConfig(prev => ({
      ...prev,
      primaryOrder: prev.primaryOrder === 'asc' ? 'desc' : 'asc'
    }));
  } else {
    // New primary sort
    setSortConfig({
      primary: column,
      primaryOrder: 'asc'
    });
  }
};
```

### 3. Advanced Filters

#### New Filter Options

```typescript
interface FilterState {
  search: string;
  brands: string[];        // Multiple brand selection
  states: string[];        // Multiple state selection
  types: string[];         // Multiple type selection
  dateRange: {
    from: Date | null;
    to: Date | null;
  };
  spendRange: {
    min: number | null;
    max: number | null;
  };
  impressionsRange: {
    min: number | null;
    max: number | null;
  };
  portfolioId?: string;
  biddingStrategy?: string;
}
```

#### Filter Persistence

```typescript
// Use localStorage to persist filters
const FILTER_STORAGE_KEY = 'campaign-filters';

const loadFilters = (): FilterState => {
  const stored = localStorage.getItem(FILTER_STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch {
      // Invalid stored data
    }
  }
  return defaultFilters;
};

const saveFilters = (filters: FilterState) => {
  localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(filters));
};
```

### 4. Performance Optimizations

#### Virtual Scrolling for Large Lists

```tsx
import { FixedSizeList } from 'react-window';

const VirtualCampaignList: React.FC<{ campaigns: Campaign[] }> = ({ campaigns }) => {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const campaign = campaigns[index];
    return (
      <div style={style} className="campaign-row">
        {/* Campaign row content */}
      </div>
    );
  };

  return (
    <FixedSizeList
      height={600}
      itemCount={campaigns.length}
      itemSize={60}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
};
```

#### Skeleton Loaders

```tsx
const CampaignSkeleton: React.FC = () => (
  <div className="animate-pulse">
    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  </div>
);

// Use in table
{isLoading ? (
  <tbody>
    {Array.from({ length: pageSize }).map((_, i) => (
      <tr key={i}>
        <td colSpan={7} className="px-6 py-4">
          <CampaignSkeleton />
        </td>
      </tr>
    ))}
  </tbody>
) : (
  // Actual data
)}
```

### 5. Bulk Operations

#### Selection Management

```typescript
const [selectedCampaigns, setSelectedCampaigns] = useState<Set<string>>(new Set());

const toggleCampaign = (campaignId: string) => {
  setSelectedCampaigns(prev => {
    const next = new Set(prev);
    if (next.has(campaignId)) {
      next.delete(campaignId);
    } else {
      next.add(campaignId);
    }
    return next;
  });
};

const selectAll = () => {
  const allIds = new Set(data?.campaigns.map(c => c.id));
  setSelectedCampaigns(allIds);
};
```

#### Bulk Actions

```tsx
const BulkActions: React.FC<{ selected: Set<string> }> = ({ selected }) => {
  if (selected.size === 0) return null;

  return (
    <div className="bg-blue-50 px-4 py-2 flex items-center justify-between">
      <span>{selected.size} campaigns selected</span>
      <div className="flex gap-2">
        <button onClick={() => bulkUpdateState('PAUSED')}>
          Pause Selected
        </button>
        <button onClick={() => bulkUpdateState('ENABLED')}>
          Enable Selected
        </button>
        <button onClick={() => bulkAssignBrand()}>
          Assign Brand
        </button>
        <button onClick={() => exportSelected()}>
          Export
        </button>
      </div>
    </div>
  );
};
```

### 6. Export Functionality

#### Backend Export Endpoint

```python
@router.post("/export")
async def export_campaigns(
    filters: Dict[str, Any],
    format: str = Query("csv", description="Export format: csv, xlsx, json"),
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> StreamingResponse:
    """Export filtered campaigns"""
    # Apply filters and fetch data
    # Generate file based on format
    # Return streaming response
```

#### Frontend Export

```typescript
const exportCampaigns = async (format: 'csv' | 'xlsx' | 'json' = 'csv') => {
  const response = await api.post('/campaigns/export', {
    filters: currentFilters,
    format
  }, {
    responseType: 'blob'
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `campaigns-${Date.now()}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};
```

## Implementation Priority

1. **Phase 1 - Immediate** (Performance)
   - Brand dropdown optimization with database function
   - Skeleton loaders
   - Basic filter persistence

2. **Phase 2 - Short-term** (Functionality)
   - Multi-column sorting
   - Advanced filters (multi-select)
   - Virtual scrolling for large lists

3. **Phase 3 - Medium-term** (Features)
   - Bulk operations
   - Export functionality
   - Saved filter presets

## Testing Considerations

1. **Performance Testing**
   - Test with 10,000+ campaigns
   - Measure brand dropdown load time
   - Virtual scrolling smoothness

2. **Filter Testing**
   - Complex filter combinations
   - Filter persistence across sessions
   - URL parameter sync

3. **Export Testing**
   - Large dataset exports
   - Different format validations
   - Streaming response handling

## Migration Strategy

1. Create database function and indexes
2. Deploy backend changes with backward compatibility
3. Roll out frontend changes with feature flags
4. Monitor performance metrics
5. Remove old endpoints after migration

## Success Metrics

- Brand dropdown load time < 500ms
- Page load time < 2s with 1000 campaigns
- Filter apply time < 1s
- Export generation < 5s for 10,000 records
- User engagement with filters increased by 30%