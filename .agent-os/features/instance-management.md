# Instance Management System

## Overview

The instance management system handles configuration and management of Amazon Marketing Cloud (AMC) instances, enabling users to connect multiple AMC environments and manage access across different Amazon advertiser accounts.

## Key Components

### Backend Services
- `amc_manager/services/instance_service.py` - Instance CRUD operations
- `amc_manager/services/amc_api_client_with_retry.py` - AMC connectivity testing
- `amc_manager/api/supabase/instances.py` - API endpoints

### Frontend Components
- `frontend/src/pages/InstanceList.tsx` - Instance management interface
- `frontend/src/components/InstanceForm.tsx` - Create/edit instances
- `frontend/src/components/InstanceCard.tsx` - Instance display and actions
- `frontend/src/services/instance.service.ts` - Instance API client

### Database Tables
- `amc_instances` - Core instance configurations
- `amc_accounts` - Amazon account details with entity_id
- `instance_brands` - Brand associations for instances
- `users` - User ownership and access control

## Technical Implementation

### Instance Configuration
```python
# instance_service.py - Instance creation
async def create_instance(self, user_id: str, instance_data: dict):
    """Create new AMC instance configuration"""
    
    # Validate instance connectivity
    await self.validate_instance_connection(instance_data)
    
    # Create instance record
    instance = self.db.table('amc_instances').insert({
        'user_id': user_id,
        'instance_id': instance_data['instance_id'],      # AMC string ID (e.g., "amcibersblt")
        'name': instance_data['name'],
        'description': instance_data.get('description'),
        'region': instance_data['region'],
        'account_id': instance_data['account_id'],        # FK to amc_accounts
        'is_active': True,
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    return instance

async def validate_instance_connection(self, instance_data: dict):
    """Test AMC instance connectivity"""
    try:
        # Test connection with provided credentials
        test_result = await self.amc_client.test_connection(
            instance_id=instance_data['instance_id'],
            entity_id=instance_data['entity_id']
        )
        
        if not test_result['success']:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot connect to AMC instance: {test_result['error']}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Instance validation failed: {str(e)}"
        )
```

### Critical ID Management
```python
class AMCInstance:
    """
    Critical distinction between internal UUID and AMC instance ID:
    - id: UUID primary key for internal database operations
    - instance_id: String identifier used for AMC API calls (e.g., "amcibersblt")
    """
    
    def __init__(self):
        self.id = uuid.uuid4()                    # Internal UUID
        self.instance_id = None                   # AMC string ID - REQUIRED for API
        self.account_id = None                    # FK to amc_accounts table
        
    def get_amc_credentials(self):
        """Get credentials for AMC API calls"""
        return {
            'instance_id': self.instance_id,      # Use string ID, NOT UUID!
            'entity_id': self.amc_account.account_id  # From joined table
        }
```

### Instance-Account Relationship
```python
async def get_instance_with_account(self, instance_id: str):
    """Get instance with associated account details"""
    
    # CRITICAL: Always join amc_accounts for entity_id
    result = self.db.table('amc_instances')\
        .select('*, amc_accounts(*)')\
        .eq('id', instance_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    instance = result.data[0]
    
    # Validate account association
    if not instance['amc_accounts']:
        raise HTTPException(
            status_code=400, 
            detail="Instance missing required account association"
        )
    
    return instance
```

## AMC Account Management

### Account Creation and Linking
```python
async def create_amc_account(self, account_data: dict):
    """Create AMC account record"""
    account = self.db.table('amc_accounts').insert({
        'account_id': account_data['account_id'],    # This becomes entity_id for AMC API
        'account_name': account_data['account_name'],
        'advertiser_id': account_data.get('advertiser_id'),
        'country_code': account_data.get('country_code', 'US'),
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    return account

async def link_instance_to_account(self, instance_id: str, account_id: str):
    """Link existing instance to AMC account"""
    self.db.table('amc_instances')\
        .update({'account_id': account_id})\
        .eq('id', instance_id)\
        .execute()
```

### Brand Association System
```python
# instance_brands.py - Brand management
async def associate_brands_with_instance(self, instance_id: str, brand_ids: List[str]):
    """Associate brands with AMC instance"""
    
    # Clear existing associations
    self.db.table('instance_brands')\
        .delete()\
        .eq('instance_id', instance_id)\
        .execute()
    
    # Create new associations
    brand_associations = [
        {
            'instance_id': instance_id,
            'brand_name': brand_id,
            'created_at': datetime.utcnow().isoformat()
        }
        for brand_id in brand_ids
    ]
    
    if brand_associations:
        self.db.table('instance_brands')\
            .insert(brand_associations)\
            .execute()

async def get_instance_brands(self, instance_id: str) -> List[str]:
    """Get brands associated with instance"""
    brands = self.db.table('instance_brands')\
        .select('brand_name')\
        .eq('instance_id', instance_id)\
        .execute()
    
    return [brand['brand_name'] for brand in brands.data]
```

## Data Flow

1. **Instance Creation**: User provides AMC instance details
2. **Validation**: System tests connectivity to AMC
3. **Account Linking**: Associate with AMC account (entity_id source)
4. **Brand Association**: Link relevant brands to instance
5. **Configuration Storage**: Store encrypted configuration
6. **Access Control**: Ensure user-level isolation

## Instance Status Management

### Health Monitoring
```python
async def check_instance_health(self, instance_id: str):
    """Check AMC instance connectivity and health"""
    instance = await self.get_instance_with_account(instance_id)
    
    try:
        # Test basic connectivity
        health_check = await self.amc_client.health_check(
            instance_id=instance['instance_id'],
            entity_id=instance['amc_accounts']['account_id']
        )
        
        # Update instance status
        self.db.table('amc_instances')\
            .update({
                'last_health_check': datetime.utcnow().isoformat(),
                'health_status': 'HEALTHY' if health_check['success'] else 'UNHEALTHY',
                'health_error': health_check.get('error')
            })\
            .eq('id', instance_id)\
            .execute()
        
        return health_check
        
    except Exception as e:
        # Mark instance as unhealthy
        self.db.table('amc_instances')\
            .update({
                'last_health_check': datetime.utcnow().isoformat(),
                'health_status': 'ERROR',
                'health_error': str(e)
            })\
            .eq('id', instance_id)\
            .execute()
        
        raise HTTPException(status_code=503, detail=f"Instance health check failed: {str(e)}")
```

### Instance Status States
- `ACTIVE` - Instance configured and healthy
- `INACTIVE` - Instance disabled by user
- `ERROR` - Connectivity or configuration issues
- `PENDING` - Initial configuration in progress

## Frontend Integration

### Instance Selection Component
```typescript
// InstanceSelector.tsx
interface InstanceSelectorProps {
  selectedInstanceId: string | null;
  onInstanceChange: (instanceId: string) => void;
  filterActiveOnly?: boolean;
}

const InstanceSelector: React.FC<InstanceSelectorProps> = ({
  selectedInstanceId,
  onInstanceChange,
  filterActiveOnly = true
}) => {
  const { data: instances, isLoading } = useQuery({
    queryKey: ['instances'],
    queryFn: () => instanceService.list({ active: filterActiveOnly }),
  });

  return (
    <select
      value={selectedInstanceId || ''}
      onChange={(e) => onInstanceChange(e.target.value)}
      className="form-select"
    >
      <option value="">Select AMC Instance</option>
      {instances?.map((instance) => (
        <option key={instance.id} value={instance.id}>
          {instance.name} ({instance.instance_id})
        </option>
      ))}
    </select>
  );
};
```

### Instance Health Indicator
```typescript
const InstanceHealthIndicator: React.FC<{ instance: AMCInstance }> = ({ instance }) => {
  const getHealthColor = (status: string) => {
    switch (status) {
      case 'HEALTHY': return 'green';
      case 'UNHEALTHY': return 'yellow';
      case 'ERROR': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div 
        className={`w-3 h-3 rounded-full bg-${getHealthColor(instance.health_status)}-500`}
      />
      <span className="text-sm text-gray-600">
        {instance.health_status || 'Unknown'}
      </span>
    </div>
  );
};
```

## Security Considerations

### Access Control
```python
async def verify_instance_access(self, user_id: str, instance_id: str):
    """Verify user has access to instance"""
    instance = self.db.table('amc_instances')\
        .select('user_id')\
        .eq('id', instance_id)\
        .execute()
    
    if not instance.data:
        raise HTTPException(status_code=404, detail="Instance not found")
    
    if instance.data[0]['user_id'] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return True
```

### Configuration Encryption
```python
class SecureInstanceConfig:
    """Secure storage of sensitive instance configuration"""
    
    def __init__(self, cipher: Fernet):
        self.cipher = cipher
    
    def encrypt_config(self, config: dict) -> str:
        """Encrypt sensitive configuration data"""
        config_json = json.dumps(config)
        return self.cipher.encrypt(config_json.encode()).decode()
    
    def decrypt_config(self, encrypted_config: str) -> dict:
        """Decrypt configuration data"""
        decrypted_json = self.cipher.decrypt(encrypted_config.encode()).decode()
        return json.loads(decrypted_json)
```

## Error Handling

### Connection Validation Errors
```python
class InstanceConnectionError(Exception):
    """Instance connectivity issues"""
    pass

class InvalidInstanceConfiguration(Exception):
    """Invalid instance configuration"""
    pass

async def handle_instance_errors(self, instance_id: str, error: Exception):
    """Handle and log instance-related errors"""
    error_details = {
        'instance_id': instance_id,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Log error details
    logger.error(f"Instance error: {error_details}")
    
    # Update instance status if needed
    if isinstance(error, InstanceConnectionError):
        await self.mark_instance_unhealthy(instance_id, str(error))
```

## Interconnections

### With Workflow System
- Workflows require valid AMC instance for execution
- Instance credentials used for all AMC API calls
- Instance health affects workflow execution capability

### With Authentication System
- Instance access controlled by user authentication
- User tokens used for AMC API authentication
- Multi-user instance sharing (future feature)

### With Scheduling System
- Scheduled workflows tied to specific instances
- Instance health affects schedule execution
- Cross-instance scheduling validation

### With Data Collections
- Collections operate within specific AMC instances
- Instance configuration affects collection capabilities
- Multi-instance collection coordination

## Performance Optimization

### Instance Caching
```python
from functools import lru_cache

@lru_cache(maxsize=128)
async def get_cached_instance_config(instance_id: str):
    """Cache frequently accessed instance configurations"""
    return await self.get_instance_with_account(instance_id)

# Cache invalidation on updates
async def update_instance(self, instance_id: str, updates: dict):
    result = await self.db_update_instance(instance_id, updates)
    
    # Clear cache
    self.get_cached_instance_config.cache_clear()
    
    return result
```

### Health Check Optimization
```python
async def bulk_health_check(self, instance_ids: List[str]):
    """Perform health checks on multiple instances concurrently"""
    tasks = [
        self.check_instance_health(instance_id) 
        for instance_id in instance_ids
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return dict(zip(instance_ids, results))
```

## Testing Strategy

### Unit Tests
```python
def test_instance_creation():
    # Test instance configuration validation

def test_account_linking():
    # Test instance-account associations

def test_health_monitoring():
    # Test connectivity monitoring
```

### Integration Tests
```python
async def test_amc_connectivity():
    # Test actual AMC instance connections

async def test_multi_instance_operations():
    # Test cross-instance functionality
```

## Instance Templates System (Added 2025-10-15)

### Overview
Instance Templates provide a simplified way to save and reuse SQL queries for specific AMC instances without the complexity of global query templates.

**Key Features**:
- Instance-scoped SQL template storage
- Quick access via "Templates" tab on instance detail pages
- Parameter detection and auto-population from instance mappings
- Direct execution via Template Execution Wizard
- Usage count tracking

### Core Components

**Backend**:
- `/amc_manager/services/instance_template_service.py` - Service layer with CRUD operations and 5-minute caching
- `/amc_manager/api/supabase/instance_templates.py` - 6 REST endpoints with JWT authentication
- Database table: `instance_templates` with RLS policies

**Frontend**:
- `/frontend/src/components/instances/InstanceTemplateEditor.tsx` - Modal for creating/editing templates
- `/frontend/src/components/instances/InstanceTemplates.tsx` - List view with template cards
- `/frontend/src/components/instances/TemplateExecutionWizard.tsx` - 4-step execution wizard

### Recent Changes (2025-11-19)

#### Critical Cache Invalidation Fix
Fixed critical bug where updated templates would show old SQL when executing through the Template Execution Wizard.

**Backend Fix** (`instance_template_service.py`):
- **Problem**: After invalidating cache, `update_template()` method called `get_template()` for ownership check, which re-cached OLD data before the database update happened
- **Solution**: Now fetches directly from database without caching for ownership check
- **Enhancement**: Invalidates cache both BEFORE and AFTER the update to ensure fresh data
- **Impact**: Backend cache always contains latest template data after updates

**Frontend Fix** (`TemplateExecutionWizard.tsx`):
- **Problem**: Wizard received template as a prop from parent component, displaying old data from memory even after template was updated
- **Solution**: Added `useQuery` hook to fetch fresh template data when wizard opens (with `staleTime: 0` to always fetch)
- **Enhancement**: Added loading indicator while fetching fresh template data
- **Impact**: Wizard now always displays the latest template SQL from database

**Bug Impact**: This was a critical UX bug affecting users who:
1. Created a template
2. Updated the template's SQL
3. Clicked "Use Template" to execute it
→ Would see the OLD SQL in the execution wizard instead of the updated version

**Files Modified**:
- `/amc_manager/services/instance_template_service.py` - Backend cache invalidation logic
- `/frontend/src/components/instances/TemplateExecutionWizard.tsx` - Frontend data fetching

**Related Commit**: `61353d0` (2025-11-19)

### Technical Implementation

**Service Layer with Caching**:
```python
class InstanceTemplateService(DatabaseService):
    def __init__(self):
        super().__init__()
        self._cache = {}  # 5-minute TTL cache

    @with_connection_retry
    def update_template(self, template_id: str, template_data: Dict[str, Any], user_id: str) -> Optional[Dict[str, Any]]:
        """Update instance template with proper cache invalidation"""

        # Invalidate cache BEFORE ownership check to prevent re-caching old data
        self._invalidate_cache(template_id)

        # Fetch directly from DB for ownership check (without caching)
        existing = self.client.table('instance_templates')\
            .select('user_id')\
            .eq('template_id', template_id)\
            .execute()

        if not existing.data or existing.data[0]['user_id'] != user_id:
            return None

        # Perform update
        template_data['updated_at'] = datetime.utcnow().isoformat()
        response = self.client.table('instance_templates')\
            .update(template_data)\
            .eq('template_id', template_id)\
            .execute()

        # Invalidate cache AFTER update to ensure fresh data on next fetch
        self._invalidate_cache(template_id)

        return response.data[0] if response.data else None
```

**Frontend Fresh Data Fetching**:
```typescript
const TemplateExecutionWizard: React.FC<Props> = ({ template, onClose, onSuccess }) => {
  // Fetch fresh template data when wizard opens (ignore prop)
  const { data: freshTemplate, isLoading } = useQuery({
    queryKey: ['instance-template', template.instanceId, template.templateId],
    queryFn: () => instanceTemplateService.getTemplate(template.instanceId, template.templateId),
    staleTime: 0,  // Always fetch fresh data
    enabled: true
  });

  const templateToUse = freshTemplate || template;

  if (isLoading) {
    return <div>Loading template...</div>;
  }

  // Rest of wizard implementation uses fresh template data
};
```

### Database Schema
```sql
CREATE TABLE instance_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    sql_query TEXT NOT NULL,
    instance_id UUID REFERENCES amc_instances(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    tags JSONB DEFAULT '[]',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### API Endpoints
```http
GET    /api/instances/{instance_id}/templates              # List templates
POST   /api/instances/{instance_id}/templates              # Create template
GET    /api/instances/{instance_id}/templates/{template_id} # Get template
PUT    /api/instances/{instance_id}/templates/{template_id} # Update template
DELETE /api/instances/{instance_id}/templates/{template_id} # Delete template
POST   /api/instances/{instance_id}/templates/{template_id}/use # Increment usage
POST   /api/instances/{instance_id}/templates/{template_id}/execute # Execute template
POST   /api/instances/{instance_id}/templates/{template_id}/schedule # Create schedule
```

### Template Execution Wizard (Added 2025-10-15)

A streamlined 4-step wizard for direct execution of Instance Templates:

**Step 1: Template Display**
- Shows template SQL preview (read-only Monaco editor)
- Displays instance and brand badges
- No editing - just confirmation

**Step 2: Execution Type Selection**
- "Run Once" (immediate execution)
- "Recurring Schedule" (automated)

**Step 3: Configuration**
- **Run Once**: Date range with AMC 14-day lag warning, rolling window toggle
- **Recurring**: Frequency (daily/weekly/monthly), time, timezone, rolling date range

**Step 4: Review & Submit**
- Auto-generated execution name: `{Brand} - {Template} - {StartDate} - {EndDate}`
- Optional Snowflake integration (run once only)
- Submit creates execution or schedule

### Parameter Injection (Added 2025-10-16)

Automatic parameter detection and substitution in Instance Template Editor:

**Features**:
- **Auto-Detection**: Detects parameters in SQL (`{{param}}`, `:param`, `$param`)
- **Auto-Population**: ASINs and campaigns auto-populate from instance mappings
- **Live Preview**: SQL preview with parameters replaced (Monaco Editor, 400px)
- **Smart Saving**: Saves complete SQL with parameters replaced (no placeholders)

**Parameter Types**:
- `date` → Date picker
- `asin`/`asins` → Textarea (auto-populated from mappings)
- `campaign` → Textarea (auto-populated from mappings)
- Other → Text input

**Preview Panel**:
```typescript
<ParameterPreviewPanel
  sqlQuery={previewSQL}      // SQL with parameters replaced
  isOpen={isPreviewOpen}
  onToggle={() => setIsPreviewOpen(!isPreviewOpen)}
/>
```

### Critical Gotchas

1. **Cache Invalidation**: Always invalidate cache BEFORE and AFTER updates to prevent stale data
2. **Fresh Data Fetching**: Use `staleTime: 0` in React Query when data must be fresh (e.g., wizards)
3. **Prop vs Query Data**: Don't rely on props for data that can change - fetch fresh when needed
4. **Parameters Replaced**: Templates store complete SQL (parameters already substituted), not placeholders
5. **Instance ID Format**: Use UUID (`instance.id`) for API calls, not AMC instance string

### Related Documentation
- Main feature documentation: `/mnt/c/Users/Aeciu/Projects/amazon-helper-2/CLAUDE.md` (Instance Templates section)
- Technical spec: `.agent-os/specs/2025-10-15-instance-templates/spec.md`
- Execution wizard spec: `.agent-os/specs/2025-10-15-template-execution-wizard/spec.md`
- Parameter injection spec: `.agent-os/specs/2025-10-16-template-parameter-injection/spec.md`

## Monitoring and Analytics

### Instance Usage Metrics
```sql
-- Track instance utilization
SELECT
  i.name,
  i.instance_id,
  COUNT(w.id) as total_workflows,
  COUNT(we.id) as total_executions,
  AVG(we.execution_duration) as avg_duration
FROM amc_instances i
LEFT JOIN workflows w ON w.instance_id = i.id
LEFT JOIN workflow_executions we ON we.workflow_id = w.id
GROUP BY i.id, i.name, i.instance_id;
```

### Health Monitoring Dashboard
- Instance connectivity status
- API response times
- Error rate tracking
- Usage pattern analysis