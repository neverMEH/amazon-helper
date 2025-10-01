# Campaign Management System

## Overview

The campaign management system provides functionality to import, filter, and manage Amazon advertising campaigns within RecomAMP. It enables users to work with campaign data for parameter substitution in AMC queries and maintains campaign metadata for analysis.

## Recent Changes (2025-09-25)

### Campaign API Parameter Limits Fix (2025-09-25)
- **Fixed Campaign Selector 422 Validation Errors**: Corrected page_size parameter in campaign API requests to comply with API limits
  - **Issue**: CampaignSelector components were requesting 200 campaigns per page, exceeding the API's maximum limit of 100
  - **Impact**: Users experienced 422 Unprocessable Entity errors when trying to load campaign lists in template parameter configuration
  - **Solution**: Updated all CampaignSelector components to use page_size=100 instead of 200
  - **Files Modified**: Campaign selector components throughout the frontend
  - **Result**: Campaign selection in query templates and workflow parameters now works without validation errors

## Recent Changes (2025-09-11)

### Critical Bug Fix: Campaign Page Loading Issue

#### Root Cause Analysis
- **Primary Issue**: API routing mismatch causing 404 errors when accessing campaign endpoints
- **Secondary Issue**: Database schema misalignment - attempted user filtering on non-existent `user_id` column
- **Impact**: Complete inability to load campaigns page, blocking user access to campaign management functionality

#### Fix Implementation

**Phase 1: Initial Fix Attempt (Commit 2246746)**
- **Approach**: Attempted to add user-level security filtering to campaign endpoints
- **Changes Made**:
  - Added trailing slash to frontend API calls (`/campaigns/` instead of `/campaigns`)
  - Implemented `get_campaigns_for_user()` method in `CampaignService`
  - Added user filtering to all campaign endpoints (`/api/campaigns/`, `/api/campaigns/brands`, `/api/campaigns/stats`)
- **Result**: Fixed 404 routing issue but introduced 500 errors due to missing database column

**Phase 2: Rollback and Actual Fix (Commit 7febedb)**
- **Root Issue Identified**: `campaigns` table lacks `user_id` column for user-level filtering
- **Solution**: Removed all user_id filtering references while preserving routing fixes
- **Final State**: 
  - **✓ Fixed**: Trailing slash routing issue resolved
  - **✓ Fixed**: 500 errors from missing column eliminated  
  - **✓ Maintained**: Authentication still required at API level
  - **⚠ Note**: User-level data filtering not implemented (requires database migration)

#### Files Modified
- **Backend**: `/amc_manager/api/supabase/campaigns.py` - Removed user filtering, kept routing
- **Frontend**: `/frontend/src/components/campaigns/CampaignsOptimized.tsx` - Added trailing slash
- **Service Layer**: `/amc_manager/services/campaign_service.py` - Added framework for future user filtering
- **Tests**: `/tests/test_campaign_user_filtering.py` - Comprehensive test suite for future implementation

#### Current Status
- **✅ Working**: Campaigns page loads successfully
- **✅ Secure**: Authentication required for all campaign endpoints  
- **⚠ Future Work**: User-level data isolation requires database schema update to add `user_id` column to campaigns table

#### Technical Lessons Learned
- **API Route Consistency**: Trailing slashes must match between frontend calls and backend route definitions
- **Schema-First Approach**: Database constraints must exist before implementing filtering logic
- **Error Propagation**: Missing columns cause 500 errors that mask underlying routing issues
- **Test-Driven Development**: Comprehensive test suite created for future user filtering implementation

## Key Components

### Backend Services
- `amc_manager/services/campaign_service.py` - Campaign CRUD operations
- `amc_manager/services/amazon_api_client.py` - Amazon Advertising API integration
- `amc_manager/api/supabase/campaigns.py` - Campaign API endpoints

### Frontend Components
- `frontend/src/pages/CampaignList.tsx` - Campaign management interface
- `frontend/src/components/CampaignImporter.tsx` - Campaign import functionality
- `frontend/src/components/CampaignSelector.tsx` - Campaign selection for queries
- `frontend/src/services/campaign.service.ts` - Campaign API client

### Database Tables
- `campaigns` - Campaign metadata and performance data
- `amc_instances` - Instance associations for campaign filtering
- `workflows` - Campaign parameter usage in queries

## Campaign Data Model

### Campaign Entity Structure
```python
# campaigns table schema
class Campaign:
    id: UUID                    # Internal ID
    campaign_id: str           # Amazon campaign ID
    name: str                  # Campaign name
    campaign_type: str         # SP, SB, SD, DSP
    state: str                # ENABLED, PAUSED, ARCHIVED
    instance_id: UUID          # FK to amc_instances
    user_id: UUID             # FK to users
    
    # Performance metrics (updated periodically)
    impressions: int
    clicks: int
    spend: Decimal
    sales: Decimal
    acos: Decimal
    roas: Decimal
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    last_sync_at: datetime
    
    # Amazon metadata
    start_date: date
    end_date: date
    budget: Decimal
    budget_type: str
    targeting_type: str
    portfolio_id: str
```

## Campaign Import System

### Amazon Advertising API Integration
```python
# campaign_service.py - Campaign import functionality
class CampaignService(DatabaseService):
    def __init__(self):
        super().__init__()
        self.amazon_api = AmazonAdvertisingAPIClient()
    
    async def import_campaigns_for_instance(self, instance_id: str, user_id: str, 
                                          campaign_types: List[str] = None) -> dict:
        """Import campaigns from Amazon Advertising API"""
        
        # Get instance configuration
        instance = await self.get_instance_with_credentials(instance_id)
        
        # Default to all campaign types if not specified
        if not campaign_types:
            campaign_types = ['sponsoredProducts', 'sponsoredBrands', 'sponsoredDisplay']
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        try:
            for campaign_type in campaign_types:
                campaigns_data = await self.fetch_campaigns_by_type(
                    instance, campaign_type
                )
                
                for campaign_data in campaigns_data:
                    try:
                        result = await self.import_single_campaign(
                            campaign_data, instance_id, user_id, campaign_type
                        )
                        
                        if result['created']:
                            imported_count += 1
                        else:
                            updated_count += 1
                            
                    except Exception as e:
                        errors.append({
                            'campaign_id': campaign_data.get('campaignId'),
                            'error': str(e)
                        })
                        logger.error(f"Failed to import campaign {campaign_data.get('campaignId')}: {e}")
            
            # Update last sync time
            self.db.table('amc_instances')\
                .update({'campaigns_last_sync': datetime.utcnow().isoformat()})\
                .eq('id', instance_id)\
                .execute()
            
            return {
                'success': True,
                'imported': imported_count,
                'updated': updated_count,
                'errors': errors,
                'total_processed': imported_count + updated_count
            }
            
        except Exception as e:
            logger.error(f"Campaign import failed for instance {instance_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'imported': imported_count,
                'updated': updated_count,
                'errors': errors
            }
    
    async def fetch_campaigns_by_type(self, instance: dict, campaign_type: str) -> List[dict]:
        """Fetch campaigns from Amazon API by type"""
        try:
            # Get user tokens for API authentication
            user = self.get_user_with_tokens(instance['user_id'])
            
            campaigns = await self.amazon_api.get_campaigns(
                access_token=self.decrypt_token(user['encrypted_access_token']),
                profile_id=instance['amc_accounts']['profile_id'],
                campaign_type=campaign_type,
                state_filter='enabled,paused'  # Exclude archived by default
            )
            
            return campaigns
            
        except Exception as e:
            logger.error(f"Failed to fetch {campaign_type} campaigns: {e}")
            raise
    
    async def import_single_campaign(self, campaign_data: dict, instance_id: str, 
                                   user_id: str, campaign_type: str) -> dict:
        """Import or update single campaign"""
        campaign_id = campaign_data['campaignId']
        
        # Check if campaign already exists
        existing = self.db.table('campaigns')\
            .select('id')\
            .eq('campaign_id', campaign_id)\
            .eq('instance_id', instance_id)\
            .execute()
        
        campaign_record = {
            'campaign_id': campaign_id,
            'name': campaign_data['name'],
            'campaign_type': campaign_type,
            'state': campaign_data.get('state', 'UNKNOWN'),
            'instance_id': instance_id,
            'user_id': user_id,
            'start_date': campaign_data.get('startDate'),
            'end_date': campaign_data.get('endDate'),
            'budget': campaign_data.get('budget', {}).get('budget'),
            'budget_type': campaign_data.get('budget', {}).get('budgetType'),
            'targeting_type': campaign_data.get('targetingType'),
            'portfolio_id': campaign_data.get('portfolioId'),
            'updated_at': datetime.utcnow().isoformat(),
            'last_sync_at': datetime.utcnow().isoformat()
        }
        
        if existing.data:
            # Update existing campaign
            self.db.table('campaigns')\
                .update(campaign_record)\
                .eq('id', existing.data[0]['id'])\
                .execute()
            
            return {'created': False, 'campaign_id': campaign_id}
        else:
            # Create new campaign
            campaign_record['created_at'] = datetime.utcnow().isoformat()
            
            self.db.table('campaigns')\
                .insert(campaign_record)\
                .execute()
            
            return {'created': True, 'campaign_id': campaign_id}
```

### Performance Data Integration
```python
async def update_campaign_performance(self, instance_id: str, date_range: dict = None):
    """Update campaign performance metrics"""
    
    if not date_range:
        # Default to last 30 days
        date_range = {
            'start_date': (datetime.utcnow() - timedelta(days=30)).date(),
            'end_date': datetime.utcnow().date()
        }
    
    try:
        instance = await self.get_instance_with_credentials(instance_id)
        user = self.get_user_with_tokens(instance['user_id'])
        
        # Get campaigns for this instance
        campaigns = self.db.table('campaigns')\
            .select('campaign_id, campaign_type')\
            .eq('instance_id', instance_id)\
            .execute()
        
        for campaign in campaigns.data:
            try:
                # Fetch performance data from Amazon API
                performance = await self.amazon_api.get_campaign_performance(
                    access_token=self.decrypt_token(user['encrypted_access_token']),
                    profile_id=instance['amc_accounts']['profile_id'],
                    campaign_id=campaign['campaign_id'],
                    campaign_type=campaign['campaign_type'],
                    start_date=date_range['start_date'],
                    end_date=date_range['end_date']
                )
                
                # Calculate derived metrics
                acos = (performance['spend'] / performance['sales'] * 100) if performance['sales'] > 0 else 0
                roas = (performance['sales'] / performance['spend']) if performance['spend'] > 0 else 0
                
                # Update campaign record
                self.db.table('campaigns')\
                    .update({
                        'impressions': performance['impressions'],
                        'clicks': performance['clicks'],
                        'spend': performance['spend'],
                        'sales': performance['sales'],
                        'acos': acos,
                        'roas': roas,
                        'performance_updated_at': datetime.utcnow().isoformat()
                    })\
                    .eq('campaign_id', campaign['campaign_id'])\
                    .eq('instance_id', instance_id)\
                    .execute()
                
            except Exception as e:
                logger.error(f"Failed to update performance for campaign {campaign['campaign_id']}: {e}")
                continue
        
        logger.info(f"Updated performance for {len(campaigns.data)} campaigns")
        
    except Exception as e:
        logger.error(f"Campaign performance update failed for instance {instance_id}: {e}")
        raise
```

## Campaign Filtering and Selection

### Advanced Filtering System
```python
async def get_campaigns_with_filters(self, instance_id: str, filters: dict = None) -> List[dict]:
    """Get campaigns with advanced filtering"""
    
    query = self.db.table('campaigns')\
        .select('*')\
        .eq('instance_id', instance_id)\
        .order('name')
    
    if filters:
        # Campaign type filter
        if 'campaign_types' in filters:
            query = query.in_('campaign_type', filters['campaign_types'])
        
        # State filter
        if 'states' in filters:
            query = query.in_('state', filters['states'])
        
        # Performance filters
        if 'min_spend' in filters:
            query = query.gte('spend', filters['min_spend'])
        
        if 'max_acos' in filters:
            query = query.lte('acos', filters['max_acos'])
        
        if 'min_roas' in filters:
            query = query.gte('roas', filters['min_roas'])
        
        # Date range filter
        if 'start_date' in filters:
            query = query.gte('start_date', filters['start_date'])
        
        if 'end_date' in filters:
            query = query.lte('end_date', filters['end_date'])
        
        # Search filter
        if 'search' in filters:
            search_term = f"%{filters['search']}%"
            query = query.ilike('name', search_term)
    
    result = query.execute()
    return result.data
```

### Campaign Selection Component
```typescript
// CampaignSelector.tsx - React component for campaign selection
interface CampaignSelectorProps {
  instanceId: string;
  value: string[];
  onChange: (campaignIds: string[]) => void;
  multiple?: boolean;
  filters?: CampaignFilters;
  placeholder?: string;
}

const CampaignSelector: React.FC<CampaignSelectorProps> = ({
  instanceId,
  value,
  onChange,
  multiple = true,
  filters,
  placeholder = "Select campaigns"
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [localFilters, setLocalFilters] = useState(filters || {});
  
  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns', instanceId, localFilters, searchTerm],
    queryFn: () => campaignService.list({
      instance_id: instanceId,
      ...localFilters,
      search: searchTerm
    }),
    enabled: !!instanceId
  });
  
  const handleSelectionChange = (selectedIds: string[]) => {
    onChange(selectedIds);
  };
  
  const handleFilterChange = (newFilters: Partial<CampaignFilters>) => {
    setLocalFilters({ ...localFilters, ...newFilters });
  };
  
  return (
    <div className="space-y-4">
      {/* Search Input */}
      <input
        type="text"
        placeholder="Search campaigns..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md"
      />
      
      {/* Filter Controls */}
      <CampaignFilters 
        filters={localFilters}
        onChange={handleFilterChange}
      />
      
      {/* Campaign List */}
      <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md">
        {isLoading ? (
          <div className="p-4 text-center">Loading campaigns...</div>
        ) : campaigns?.length === 0 ? (
          <div className="p-4 text-center text-gray-500">No campaigns found</div>
        ) : (
          campaigns?.map((campaign) => (
            <CampaignItem
              key={campaign.campaign_id}
              campaign={campaign}
              selected={value.includes(campaign.campaign_id)}
              onChange={(selected) => {
                if (multiple) {
                  const newValue = selected
                    ? [...value, campaign.campaign_id]
                    : value.filter(id => id !== campaign.campaign_id);
                  handleSelectionChange(newValue);
                } else {
                  handleSelectionChange(selected ? [campaign.campaign_id] : []);
                }
              }}
            />
          ))
        )}
      </div>
      
      {/* Selection Summary */}
      {value.length > 0 && (
        <div className="text-sm text-gray-600">
          {value.length} campaign{value.length !== 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  );
};
```

## Campaign Import Automation

### Scheduled Import System
```python
async def schedule_campaign_imports(self):
    """Schedule regular campaign imports for all instances"""
    
    # Get all active instances
    instances = self.db.table('amc_instances')\
        .select('id, user_id, campaigns_last_sync')\
        .eq('is_active', True)\
        .execute()
    
    for instance in instances.data:
        last_sync = instance.get('campaigns_last_sync')
        
        # Import if never synced or last sync was more than 24 hours ago
        should_sync = (
            not last_sync or
            datetime.utcnow() - datetime.fromisoformat(last_sync) > timedelta(hours=24)
        )
        
        if should_sync:
            try:
                await self.import_campaigns_for_instance(
                    instance['id'], 
                    instance['user_id']
                )
                logger.info(f"Completed scheduled import for instance {instance['id']}")
                
            except Exception as e:
                logger.error(f"Scheduled import failed for instance {instance['id']}: {e}")
```

### Import Status Tracking
```python
class CampaignImportStatus:
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.status = 'PENDING'
        self.progress = 0
        self.total_campaigns = 0
        self.processed_campaigns = 0
        self.errors = []
        self.started_at = datetime.utcnow()
    
    def update_progress(self, processed: int, total: int):
        self.processed_campaigns = processed
        self.total_campaigns = total
        self.progress = (processed / total * 100) if total > 0 else 0
    
    def add_error(self, campaign_id: str, error: str):
        self.errors.append({
            'campaign_id': campaign_id,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def complete(self, success: bool = True):
        self.status = 'COMPLETED' if success else 'FAILED'
        self.completed_at = datetime.utcnow()
        
        # Store import log
        self.store_import_log()
    
    def store_import_log(self):
        """Store import results for audit trail"""
        log_data = {
            'instance_id': self.instance_id,
            'status': self.status,
            'total_campaigns': self.total_campaigns,
            'processed_campaigns': self.processed_campaigns,
            'error_count': len(self.errors),
            'errors': self.errors,
            'started_at': self.started_at.isoformat(),
            'completed_at': getattr(self, 'completed_at', datetime.utcnow()).isoformat(),
            'duration_seconds': (
                getattr(self, 'completed_at', datetime.utcnow()) - self.started_at
            ).total_seconds()
        }
        
        # Store in import_logs table or similar
        # self.db.table('campaign_import_logs').insert(log_data).execute()
```

## Query Parameter Integration

### Campaign ID Parameter Substitution
```python
# Integration with query builder system
def format_campaign_ids_for_query(campaign_ids: List[str]) -> str:
    """Format campaign IDs for SQL IN clause"""
    if not campaign_ids:
        return "''"
    
    # Escape and quote each campaign ID
    escaped_ids = [f"'{campaign_id.replace("'", "''")}'" for campaign_id in campaign_ids]
    return ', '.join(escaped_ids)

# Example usage in workflow parameter substitution
def substitute_campaign_parameters(sql_query: str, campaign_ids: List[str]) -> str:
    """Replace {{campaign_ids}} parameter in SQL query"""
    formatted_ids = format_campaign_ids_for_query(campaign_ids)
    return sql_query.replace('{{campaign_ids}}', formatted_ids)
```

### Campaign Metadata for Queries
```python
async def get_campaign_metadata_for_query(campaign_ids: List[str], instance_id: str) -> dict:
    """Get campaign metadata to enhance query context"""
    
    campaigns = self.db.table('campaigns')\
        .select('campaign_id, name, campaign_type, state, spend, acos')\
        .in_('campaign_id', campaign_ids)\
        .eq('instance_id', instance_id)\
        .execute()
    
    return {
        'total_campaigns': len(campaigns.data),
        'campaign_types': list(set(c['campaign_type'] for c in campaigns.data)),
        'active_campaigns': len([c for c in campaigns.data if c['state'] == 'ENABLED']),
        'total_spend': sum(c['spend'] or 0 for c in campaigns.data),
        'avg_acos': sum(c['acos'] or 0 for c in campaigns.data) / len(campaigns.data) if campaigns.data else 0,
        'campaign_names': [c['name'] for c in campaigns.data]
    }
```

## Performance and Optimization

### Campaign Data Caching
```python
from functools import lru_cache
from typing import Optional

class CampaignCache:
    def __init__(self, ttl_seconds: int = 300):  # 5 minute TTL
        self.ttl_seconds = ttl_seconds
        self._cache = {}
    
    @lru_cache(maxsize=1000)
    def get_cached_campaigns(self, instance_id: str, cache_key: str) -> Optional[List[dict]]:
        """Get cached campaign data"""
        cache_entry = self._cache.get(f"{instance_id}:{cache_key}")
        
        if not cache_entry:
            return None
        
        # Check if cache entry is expired
        if datetime.utcnow() - cache_entry['timestamp'] > timedelta(seconds=self.ttl_seconds):
            del self._cache[f"{instance_id}:{cache_key}"]
            return None
        
        return cache_entry['data']
    
    def set_cached_campaigns(self, instance_id: str, cache_key: str, data: List[dict]):
        """Cache campaign data"""
        self._cache[f"{instance_id}:{cache_key}"] = {
            'data': data,
            'timestamp': datetime.utcnow()
        }
    
    def invalidate_instance_cache(self, instance_id: str):
        """Invalidate all cache entries for an instance"""
        keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{instance_id}:")]
        for key in keys_to_remove:
            del self._cache[key]
```

### Bulk Operations
```python
async def bulk_update_campaign_states(self, campaign_ids: List[str], 
                                     new_state: str, instance_id: str) -> dict:
    """Bulk update campaign states"""
    
    try:
        # Update in database
        result = self.db.table('campaigns')\
            .update({'state': new_state, 'updated_at': datetime.utcnow().isoformat()})\
            .in_('campaign_id', campaign_ids)\
            .eq('instance_id', instance_id)\
            .execute()
        
        # Optionally sync with Amazon API
        # await self.sync_campaign_states_with_amazon(campaign_ids, instance_id)
        
        return {
            'success': True,
            'updated_count': len(result.data),
            'campaign_ids': campaign_ids
        }
        
    except Exception as e:
        logger.error(f"Bulk campaign state update failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'updated_count': 0
        }
```

## Testing and Validation

### Campaign Import Testing
```python
async def test_campaign_import():
    """Test campaign import functionality"""
    
    # Mock Amazon API responses
    mock_campaigns = [
        {
            'campaignId': 'CAMP001',
            'name': 'Test Campaign 1',
            'state': 'ENABLED',
            'campaignType': 'sponsoredProducts',
            'budget': {'budget': 100.00, 'budgetType': 'DAILY'}
        }
    ]
    
    # Test import process
    result = await campaign_service.import_campaigns_for_instance(
        instance_id='test-instance',
        user_id='test-user',
        mock_data=mock_campaigns
    )
    
    assert result['success'] == True
    assert result['imported'] == 1
```

### Campaign Selection Testing
```typescript
// Test campaign selector component
describe('CampaignSelector', () => {
  it('filters campaigns by search term', async () => {
    const campaigns = [
      { campaign_id: '1', name: 'Summer Sale Campaign' },
      { campaign_id: '2', name: 'Winter Promotion' }
    ];
    
    render(<CampaignSelector campaigns={campaigns} />);
    
    const searchInput = screen.getByPlaceholderText('Search campaigns...');
    fireEvent.change(searchInput, { target: { value: 'Summer' } });
    
    expect(screen.getByText('Summer Sale Campaign')).toBeInTheDocument();
    expect(screen.queryByText('Winter Promotion')).not.toBeInTheDocument();
  });
});
```