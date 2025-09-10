# ASIN Management System

## Overview

The ASIN management system provides functionality to track, organize, and manage Amazon Standard Identification Numbers (ASINs) within RecomAMP. It enables users to create ASIN lists for query parameter substitution, track product performance, and maintain organized product catalogs.

## Key Components

### Backend Services
- `amc_manager/services/asin_service.py` - ASIN CRUD operations and validation
- `amc_manager/services/product_api_client.py` - Product data fetching
- `amc_manager/api/supabase/asins.py` - ASIN API endpoints

### Frontend Components
- `frontend/src/pages/ASINManagement.tsx` - ASIN management interface
- `frontend/src/components/ASINImporter.tsx` - ASIN import functionality
- `frontend/src/components/ASINSelector.tsx` - ASIN selection for queries
- `frontend/src/components/ASINBulkEditor.tsx` - Bulk operations interface

### Database Tables
- `asins` - ASIN records with metadata
- `asin_lists` - Named ASIN collections
- `asin_list_items` - Many-to-many relationship for list membership

## ASIN Data Model

### Core ASIN Entity
```python
# asins table schema
class ASIN:
    id: UUID                   # Internal ID
    asin: str                 # Amazon ASIN (primary identifier)
    title: str                # Product title
    brand: str                # Product brand
    category: str             # Product category
    image_url: str            # Product image URL
    price: Decimal            # Current price
    
    # User organization
    user_id: UUID             # FK to users
    tags: List[str]           # User-defined tags
    notes: str                # User notes
    
    # Performance metrics (if available)
    sales_rank: int           # BSR (Best Sellers Rank)
    review_count: int         # Number of reviews
    average_rating: float     # Average review rating
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    last_validated_at: datetime
    is_active: bool           # Still available on Amazon
    
    # Product details
    parent_asin: str          # Parent ASIN for variations
    variation_theme: str      # Color, Size, etc.
    dimensions: dict          # Product dimensions
    weight: Decimal           # Product weight
```

### ASIN List System
```python
# asin_lists table schema
class ASINList:
    id: UUID                  # Internal ID
    name: str                # List name
    description: str         # List description
    user_id: UUID            # FK to users
    
    # Organization
    category: str            # List category
    tags: List[str]          # List tags
    is_public: bool          # Shareable with other users
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    asin_count: int          # Cached count of ASINs

# asin_list_items table schema  
class ASINListItem:
    id: UUID                 # Internal ID
    list_id: UUID           # FK to asin_lists
    asin_id: UUID           # FK to asins
    
    # List-specific metadata
    position: int           # Order within list
    added_at: datetime      # When added to list
    added_by: UUID          # User who added it
    notes: str             # Item-specific notes
```

## ASIN Import and Validation

### ASIN Import Service
```python
# asin_service.py - ASIN import and validation
class ASINService(DatabaseService):
    def __init__(self):
        super().__init__()
        self.product_api = ProductAPIClient()
        self.asin_pattern = re.compile(r'^B[0-9A-Z]{9}$')
    
    async def import_asins_from_text(self, text: str, user_id: str, 
                                   validate: bool = True) -> dict:
        """Import ASINs from text input (comma-separated, line-separated, etc.)"""
        
        # Extract ASINs from text using regex
        potential_asins = self.extract_asins_from_text(text)
        
        results = {
            'total_found': len(potential_asins),
            'valid_asins': [],
            'invalid_asins': [],
            'imported': 0,
            'updated': 0,
            'errors': []
        }
        
        for asin in potential_asins:
            try:
                # Basic format validation
                if not self.validate_asin_format(asin):
                    results['invalid_asins'].append({
                        'asin': asin,
                        'reason': 'Invalid ASIN format'
                    })
                    continue
                
                results['valid_asins'].append(asin)
                
                # Import or update ASIN
                if validate:
                    # Fetch product data from Amazon
                    product_data = await self.fetch_product_data(asin)
                    import_result = await self.import_asin_with_data(
                        asin, user_id, product_data
                    )
                else:
                    # Import without validation
                    import_result = await self.import_asin_minimal(asin, user_id)
                
                if import_result['created']:
                    results['imported'] += 1
                else:
                    results['updated'] += 1
                    
            except Exception as e:
                results['errors'].append({
                    'asin': asin,
                    'error': str(e)
                })
                logger.error(f"Failed to import ASIN {asin}: {e}")
        
        return results
    
    def extract_asins_from_text(self, text: str) -> List[str]:
        """Extract potential ASINs from text input"""
        # Clean and normalize text
        cleaned_text = re.sub(r'[^\w\s,\n]', '', text.upper())
        
        # Find all ASIN-like patterns
        asin_matches = self.asin_pattern.findall(cleaned_text)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(asin_matches))
    
    def validate_asin_format(self, asin: str) -> bool:
        """Validate ASIN format (B followed by 9 alphanumeric characters)"""
        return bool(self.asin_pattern.match(asin.upper()))
    
    async def fetch_product_data(self, asin: str) -> dict:
        """Fetch product data from Amazon Product API"""
        try:
            # Use Amazon Product API or scraping service
            product_data = await self.product_api.get_product_info(asin)
            
            return {
                'title': product_data.get('title'),
                'brand': product_data.get('brand'),
                'category': product_data.get('category'),
                'image_url': product_data.get('image_url'),
                'price': product_data.get('price'),
                'sales_rank': product_data.get('sales_rank'),
                'review_count': product_data.get('review_count'),
                'average_rating': product_data.get('average_rating'),
                'is_active': product_data.get('available', True)
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch product data for {asin}: {e}")
            return {}
    
    async def import_asin_with_data(self, asin: str, user_id: str, 
                                  product_data: dict) -> dict:
        """Import ASIN with full product data"""
        
        # Check if ASIN already exists for this user
        existing = self.db.table('asins')\
            .select('id')\
            .eq('asin', asin)\
            .eq('user_id', user_id)\
            .execute()
        
        asin_record = {
            'asin': asin,
            'user_id': user_id,
            'title': product_data.get('title'),
            'brand': product_data.get('brand'),
            'category': product_data.get('category'),
            'image_url': product_data.get('image_url'),
            'price': product_data.get('price'),
            'sales_rank': product_data.get('sales_rank'),
            'review_count': product_data.get('review_count'),
            'average_rating': product_data.get('average_rating'),
            'is_active': product_data.get('is_active', True),
            'last_validated_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if existing.data:
            # Update existing ASIN
            self.db.table('asins')\
                .update(asin_record)\
                .eq('id', existing.data[0]['id'])\
                .execute()
            
            return {'created': False, 'asin': asin}
        else:
            # Create new ASIN
            asin_record['created_at'] = datetime.utcnow().isoformat()
            
            result = self.db.table('asins')\
                .insert(asin_record)\
                .execute()
            
            return {'created': True, 'asin': asin}
    
    async def import_asin_minimal(self, asin: str, user_id: str) -> dict:
        """Import ASIN with minimal data (no validation)"""
        existing = self.db.table('asins')\
            .select('id')\
            .eq('asin', asin)\
            .eq('user_id', user_id)\
            .execute()
        
        if existing.data:
            # Update timestamp only
            self.db.table('asins')\
                .update({'updated_at': datetime.utcnow().isoformat()})\
                .eq('id', existing.data[0]['id'])\
                .execute()
            
            return {'created': False, 'asin': asin}
        else:
            # Create minimal record
            asin_record = {
                'asin': asin,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            self.db.table('asins')\
                .insert(asin_record)\
                .execute()
            
            return {'created': True, 'asin': asin}
```

## ASIN List Management

### List Operations
```python
class ASINListService(DatabaseService):
    async def create_asin_list(self, user_id: str, list_data: dict) -> dict:
        """Create new ASIN list"""
        
        list_record = {
            'name': list_data['name'],
            'description': list_data.get('description'),
            'user_id': user_id,
            'category': list_data.get('category'),
            'tags': list_data.get('tags', []),
            'is_public': list_data.get('is_public', False),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'asin_count': 0
        }
        
        result = self.db.table('asin_lists')\
            .insert(list_record)\
            .execute()
        
        return result.data[0]
    
    async def add_asins_to_list(self, list_id: str, asin_ids: List[str], 
                              user_id: str) -> dict:
        """Add ASINs to list"""
        
        # Verify list ownership
        list_info = await self.verify_list_access(list_id, user_id)
        
        # Get current max position
        max_position = self.db.table('asin_list_items')\
            .select('position')\
            .eq('list_id', list_id)\
            .order('position', desc=True)\
            .limit(1)\
            .execute()
        
        current_position = max_position.data[0]['position'] if max_position.data else 0
        
        # Check for existing items
        existing_items = self.db.table('asin_list_items')\
            .select('asin_id')\
            .eq('list_id', list_id)\
            .in_('asin_id', asin_ids)\
            .execute()
        
        existing_asin_ids = [item['asin_id'] for item in existing_items.data]
        new_asin_ids = [asin_id for asin_id in asin_ids if asin_id not in existing_asin_ids]
        
        # Add new items
        new_items = []
        for asin_id in new_asin_ids:
            current_position += 1
            new_items.append({
                'list_id': list_id,
                'asin_id': asin_id,
                'position': current_position,
                'added_at': datetime.utcnow().isoformat(),
                'added_by': user_id
            })
        
        if new_items:
            self.db.table('asin_list_items')\
                .insert(new_items)\
                .execute()
        
        # Update list ASIN count
        await self.update_list_count(list_id)
        
        return {
            'added': len(new_items),
            'skipped': len(existing_asin_ids),
            'total': len(asin_ids)
        }
    
    async def remove_asins_from_list(self, list_id: str, asin_ids: List[str], 
                                   user_id: str) -> dict:
        """Remove ASINs from list"""
        
        # Verify list ownership
        await self.verify_list_access(list_id, user_id)
        
        # Remove items
        result = self.db.table('asin_list_items')\
            .delete()\
            .eq('list_id', list_id)\
            .in_('asin_id', asin_ids)\
            .execute()
        
        # Update list count
        await self.update_list_count(list_id)
        
        return {'removed': len(result.data)}
    
    async def reorder_list_items(self, list_id: str, ordered_asin_ids: List[str], 
                               user_id: str) -> dict:
        """Reorder items in list"""
        
        # Verify list ownership
        await self.verify_list_access(list_id, user_id)
        
        # Update positions
        for position, asin_id in enumerate(ordered_asin_ids, 1):
            self.db.table('asin_list_items')\
                .update({'position': position})\
                .eq('list_id', list_id)\
                .eq('asin_id', asin_id)\
                .execute()
        
        return {'reordered': len(ordered_asin_ids)}
    
    async def update_list_count(self, list_id: str):
        """Update cached ASIN count for list"""
        count_result = self.db.table('asin_list_items')\
            .select('id', count='exact')\
            .eq('list_id', list_id)\
            .execute()
        
        count = count_result.count or 0
        
        self.db.table('asin_lists')\
            .update({
                'asin_count': count,
                'updated_at': datetime.utcnow().isoformat()
            })\
            .eq('id', list_id)\
            .execute()
```

## Frontend ASIN Management

### ASIN Import Component
```typescript
// ASINImporter.tsx - ASIN import interface
interface ASINImporterProps {
  onImportComplete: (results: ImportResults) => void;
  onClose: () => void;
}

const ASINImporter: React.FC<ASINImporterProps> = ({ onImportComplete, onClose }) => {
  const [importText, setImportText] = useState('');
  const [validateProducts, setValidateProducts] = useState(true);
  const [isImporting, setIsImporting] = useState(false);
  const [importResults, setImportResults] = useState<ImportResults | null>(null);
  
  const handleImport = async () => {
    if (!importText.trim()) return;
    
    setIsImporting(true);
    
    try {
      const results = await asinService.importFromText({
        text: importText,
        validate: validateProducts
      });
      
      setImportResults(results);
      onImportComplete(results);
      
    } catch (error) {
      console.error('Import failed:', error);
    } finally {
      setIsImporting(false);
    }
  };
  
  const getPreviewASINs = () => {
    // Extract and preview ASINs from text
    const asinPattern = /B[0-9A-Z]{9}/g;
    const matches = importText.match(asinPattern) || [];
    return Array.from(new Set(matches));
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Import ASINs</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ×
          </button>
        </div>
        
        {!importResults ? (
          <>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  ASIN List (comma-separated, line-separated, or mixed)
                </label>
                <textarea
                  value={importText}
                  onChange={(e) => setImportText(e.target.value)}
                  placeholder="B08N5WRWNW, B07FZ8S74R&#10;B09KMVNY9J&#10;amazon.com/dp/B08X1Q2B9T"
                  className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md resize-none"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="validate"
                  checked={validateProducts}
                  onChange={(e) => setValidateProducts(e.target.checked)}
                />
                <label htmlFor="validate" className="text-sm">
                  Validate products and fetch details (slower but more accurate)
                </label>
              </div>
              
              {importText && (
                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="text-sm font-medium mb-2">Preview:</h4>
                  <div className="flex flex-wrap gap-2">
                    {getPreviewASINs().slice(0, 10).map((asin) => (
                      <span key={asin} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                        {asin}
                      </span>
                    ))}
                    {getPreviewASINs().length > 10 && (
                      <span className="text-gray-500 text-xs">
                        +{getPreviewASINs().length - 10} more
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {getPreviewASINs().length} ASIN{getPreviewASINs().length !== 1 ? 's' : ''} found
                  </p>
                </div>
              )}
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={onClose}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleImport}
                disabled={!importText.trim() || isImporting}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isImporting ? 'Importing...' : 'Import ASINs'}
              </button>
            </div>
          </>
        ) : (
          <ImportResults results={importResults} onClose={onClose} />
        )}
      </div>
    </div>
  );
};
```

### ASIN Selection Component
```typescript
// ASINSelector.tsx - ASIN selection for query parameters
interface ASINSelectorProps {
  value: string[];
  onChange: (asins: string[]) => void;
  multiple?: boolean;
  showLists?: boolean;
  placeholder?: string;
}

const ASINSelector: React.FC<ASINSelectorProps> = ({
  value,
  onChange,
  multiple = true,
  showLists = true,
  placeholder = "Select ASINs"
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTab, setSelectedTab] = useState<'individual' | 'lists'>('individual');
  
  const { data: asins, isLoading: loadingASINs } = useQuery({
    queryKey: ['asins', searchTerm],
    queryFn: () => asinService.search({ query: searchTerm }),
    enabled: selectedTab === 'individual'
  });
  
  const { data: lists, isLoading: loadingLists } = useQuery({
    queryKey: ['asin-lists'],
    queryFn: () => asinListService.list(),
    enabled: selectedTab === 'lists' && showLists
  });
  
  const handleASINToggle = (asin: string) => {
    if (multiple) {
      const newValue = value.includes(asin)
        ? value.filter(a => a !== asin)
        : [...value, asin];
      onChange(newValue);
    } else {
      onChange(value.includes(asin) ? [] : [asin]);
    }
  };
  
  const handleListSelection = async (listId: string) => {
    const listASINs = await asinListService.getListASINs(listId);
    const asinValues = listASINs.map(item => item.asin);
    
    if (multiple) {
      // Add all ASINs from list that aren't already selected
      const newASINs = asinValues.filter(asin => !value.includes(asin));
      onChange([...value, ...newASINs]);
    } else {
      onChange(asinValues.slice(0, 1)); // Take first ASIN only
    }
  };
  
  return (
    <div className="space-y-4">
      <div className="flex space-x-1">
        <button
          onClick={() => setSelectedTab('individual')}
          className={`px-3 py-2 text-sm rounded-md ${
            selectedTab === 'individual'
              ? 'bg-blue-100 text-blue-700'
              : 'text-gray-600 hover:text-gray-800'
          }`}
        >
          Individual ASINs
        </button>
        {showLists && (
          <button
            onClick={() => setSelectedTab('lists')}
            className={`px-3 py-2 text-sm rounded-md ${
              selectedTab === 'lists'
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            ASIN Lists
          </button>
        )}
      </div>
      
      {selectedTab === 'individual' && (
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Search ASINs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md"
          />
          
          <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md">
            {loadingASINs ? (
              <div className="p-4 text-center">Loading ASINs...</div>
            ) : asins?.length === 0 ? (
              <div className="p-4 text-center text-gray-500">No ASINs found</div>
            ) : (
              asins?.map((asin) => (
                <ASINItem
                  key={asin.asin}
                  asin={asin}
                  selected={value.includes(asin.asin)}
                  onChange={(selected) => handleASINToggle(asin.asin)}
                />
              ))
            )}
          </div>
        </div>
      )}
      
      {selectedTab === 'lists' && showLists && (
        <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-md">
          {loadingLists ? (
            <div className="p-4 text-center">Loading lists...</div>
          ) : lists?.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No ASIN lists found</div>
          ) : (
            lists?.map((list) => (
              <div
                key={list.id}
                onClick={() => handleListSelection(list.id)}
                className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100"
              >
                <div className="font-medium">{list.name}</div>
                <div className="text-sm text-gray-600">
                  {list.asin_count} ASINs
                </div>
              </div>
            ))
          )}
        </div>
      )}
      
      {value.length > 0 && (
        <div className="text-sm text-gray-600">
          {value.length} ASIN{value.length !== 1 ? 's' : ''} selected
          {value.length <= 5 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {value.map((asin) => (
                <span
                  key={asin}
                  className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
                >
                  {asin}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

## Query Integration

### ASIN Parameter Formatting
```python
def format_asin_list_for_query(asin_list: List[str]) -> str:
    """Format ASIN list for SQL IN clause"""
    if not asin_list:
        return "''"
    
    # Validate ASINs and escape for SQL
    validated_asins = []
    for asin in asin_list:
        if validate_asin_format(asin):
            escaped_asin = asin.replace("'", "''")
            validated_asins.append(f"'{escaped_asin}'")
    
    return ', '.join(validated_asins)

# Example usage in query substitution
def substitute_asin_parameters(sql_query: str, asin_list: List[str]) -> str:
    """Replace {{asin_list}} parameter in SQL query"""
    formatted_asins = format_asin_list_for_query(asin_list)
    return sql_query.replace('{{asin_list}}', formatted_asins)
```

## Performance Optimization

### Bulk ASIN Operations
```python
async def bulk_validate_asins(self, asins: List[str], user_id: str) -> dict:
    """Validate multiple ASINs efficiently"""
    
    # Batch API requests to avoid rate limits
    batch_size = 10
    results = {
        'validated': [],
        'invalid': [],
        'errors': []
    }
    
    for i in range(0, len(asins), batch_size):
        batch = asins[i:i + batch_size]
        
        try:
            batch_results = await self.product_api.batch_validate_asins(batch)
            
            for asin, is_valid in batch_results.items():
                if is_valid:
                    results['validated'].append(asin)
                else:
                    results['invalid'].append(asin)
                    
        except Exception as e:
            logger.error(f"Batch validation failed for batch {i//batch_size}: {e}")
            results['errors'].extend(batch)
        
        # Rate limiting delay
        await asyncio.sleep(0.5)
    
    return results

async def bulk_update_asin_data(self, user_id: str) -> dict:
    """Update product data for all user's ASINs"""
    
    # Get all ASINs that need updating (older than 7 days)
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    
    asins_to_update = self.db.table('asins')\
        .select('asin')\
        .eq('user_id', user_id)\
        .lt('last_validated_at', cutoff_date.isoformat())\
        .execute()
    
    updated_count = 0
    error_count = 0
    
    for asin_record in asins_to_update.data:
        try:
            product_data = await self.fetch_product_data(asin_record['asin'])
            
            if product_data:
                self.db.table('asins')\
                    .update({
                        **product_data,
                        'last_validated_at': datetime.utcnow().isoformat(),
                        'updated_at': datetime.utcnow().isoformat()
                    })\
                    .eq('asin', asin_record['asin'])\
                    .eq('user_id', user_id)\
                    .execute()
                
                updated_count += 1
            
        except Exception as e:
            logger.error(f"Failed to update ASIN {asin_record['asin']}: {e}")
            error_count += 1
        
        # Rate limiting
        await asyncio.sleep(0.2)
    
    return {
        'updated': updated_count,
        'errors': error_count,
        'total': len(asins_to_update.data)
    }
```

## Testing and Validation

### ASIN Validation Tests
```python
def test_asin_format_validation():
    """Test ASIN format validation"""
    service = ASINService()
    
    # Valid ASINs
    assert service.validate_asin_format('B08N5WRWNW') == True
    assert service.validate_asin_format('B07FZ8S74R') == True
    
    # Invalid ASINs
    assert service.validate_asin_format('invalid') == False
    assert service.validate_asin_format('B08N5WRW') == False  # Too short
    assert service.validate_asin_format('A08N5WRWNW') == False  # Wrong prefix

def test_asin_extraction_from_text():
    """Test ASIN extraction from various text formats"""
    service = ASINService()
    
    text = """
    B08N5WRWNW, B07FZ8S74R
    amazon.com/dp/B09KMVNY9J
    https://www.amazon.com/gp/product/B08X1Q2B9T/
    """
    
    asins = service.extract_asins_from_text(text)
    expected = ['B08N5WRWNW', 'B07FZ8S74R', 'B09KMVNY9J', 'B08X1Q2B9T']
    
    assert set(asins) == set(expected)
```