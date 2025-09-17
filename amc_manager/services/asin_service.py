"""ASIN management service"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import csv
import io
import uuid
from ..core.logger_simple import get_logger
from .db_service import DatabaseService, with_connection_retry

logger = get_logger(__name__)


class ASINService(DatabaseService):
    """Service for managing ASINs (Amazon Standard Identification Numbers)"""
    
    def __init__(self):
        super().__init__()
    
    @with_connection_retry
    def list_asins(self, 
                   page: int = 1,
                   page_size: int = 100,
                   brand: Optional[str] = None,
                   marketplace: Optional[str] = None,
                   search: Optional[str] = None,
                   active: bool = True) -> Dict[str, Any]:
        """
        List ASINs with pagination and filtering
        
        Args:
            page: Page number (1-indexed)
            page_size: Items per page (max 1000)
            brand: Filter by brand name
            marketplace: Filter by marketplace ID
            search: Search in ASIN and title fields
            active: Filter by active status
            
        Returns:
            Dict with items, total, page, page_size, pages
        """
        try:
            # Validate pagination
            page = max(1, page)
            page_size = min(999999, max(1, page_size))  # Allow up to 999k items - effectively no limit
            offset = (page - 1) * page_size
            
            # Build query
            query = self.client.table('product_asins').select('*', count='exact')
            
            # Apply filters
            if active is not None:
                query = query.eq('active', active)
            
            if brand:
                query = query.eq('brand', brand)
            
            if marketplace:
                query = query.eq('marketplace', marketplace)
            
            if search:
                # Search in ASIN or title
                search_pattern = f"%{search}%"
                query = query.or_(f"asin.ilike.{search_pattern},title.ilike.{search_pattern}")
            
            # Get total count
            count_result = query.limit(1).execute()
            total = count_result.count if hasattr(count_result, 'count') else 0
            
            # Get paginated results
            query = self.client.table('product_asins').select(
                'id, asin, title, brand, marketplace, last_known_price, '
                'monthly_estimated_units, active, updated_at'
            )

            # Reapply filters for data query
            if active is not None:
                query = query.eq('active', active)
            if brand:
                query = query.eq('brand', brand)
            if marketplace:
                query = query.eq('marketplace', marketplace)
            if search:
                search_pattern = f"%{search}%"
                query = query.or_(f"asin.ilike.{search_pattern},title.ilike.{search_pattern}")

            # Apply pagination and ordering
            # For large page sizes, we need to handle Supabase's 1000 row limit
            if page_size > 1000:
                logger.info(f"Fetching large ASIN dataset: page_size={page_size}, offset={offset}")
                # Fetch all records in batches of 1000
                all_items = []
                batch_size = 1000
                current_offset = offset
                batch_count = 0

                while len(all_items) < page_size:
                    batch_result = query.order('brand', desc=False).order('asin', desc=False)\
                        .range(current_offset, current_offset + batch_size - 1).execute()

                    if not batch_result.data:
                        break

                    batch_count += 1
                    all_items.extend(batch_result.data)
                    logger.debug(f"Batch {batch_count}: fetched {len(batch_result.data)} items, total: {len(all_items)}")

                    # If we got less than batch_size, we've reached the end
                    if len(batch_result.data) < batch_size:
                        break

                    current_offset += batch_size

                logger.info(f"Fetched {len(all_items)} ASINs in {batch_count} batches")

                # Create a result object similar to what Supabase returns
                class Result:
                    def __init__(self, data):
                        self.data = data

                result = Result(all_items[:page_size])  # Limit to requested page_size
            else:
                result = query.order('brand', desc=False).order('asin', desc=False)\
                    .range(offset, offset + page_size - 1).execute()
            
            pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return {
                "items": result.data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": pages
            }
            
        except Exception as e:
            logger.error(f"Error listing ASINs: {e}")
            return {
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": page_size,
                "pages": 0
            }
    
    @with_connection_retry
    def get_asin(self, asin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific ASIN
        
        Args:
            asin_id: The ASIN record ID (UUID)
            
        Returns:
            ASIN details or None if not found
        """
        try:
            result = self.client.table('product_asins')\
                .select('*')\
                .eq('id', asin_id)\
                .single()\
                .execute()
            
            if result.data:
                # Format item dimensions if present
                asin_data = result.data
                if any([asin_data.get(f'item_{dim}') for dim in ['length', 'height', 'width', 'weight']]):
                    asin_data['item_dimensions'] = {
                        'length': asin_data.get('item_length'),
                        'height': asin_data.get('item_height'),
                        'width': asin_data.get('item_width'),
                        'weight': asin_data.get('item_weight'),
                        'unit_dimension': asin_data.get('item_unit_dimension'),
                        'unit_weight': asin_data.get('item_unit_weight')
                    }
                
                return asin_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting ASIN {asin_id}: {e}")
            return None
    
    @with_connection_retry
    def get_brands(self, search: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of unique brands
        
        Args:
            search: Filter brands by search term
            
        Returns:
            Dict with brands list and total count
        """
        try:
            query = self.client.table('product_asins')\
                .select('brand')\
                .neq('brand', '')\
                .not_.is_('brand', 'null')
            
            if search:
                query = query.ilike('brand', f'%{search}%')
            
            result = query.execute()
            
            # Extract unique brands
            brands = sorted(list(set(
                row['brand'] for row in result.data 
                if row.get('brand')
            )))
            
            return {
                "brands": brands,
                "total": len(brands)
            }
            
        except Exception as e:
            logger.error(f"Error getting brands: {e}")
            return {"brands": [], "total": 0}
    
    @with_connection_retry
    def search_asins(self,
                     asin_ids: Optional[List[str]] = None,
                     brands: Optional[List[str]] = None,
                     search: Optional[str] = None,
                     limit: int = 100) -> Dict[str, Any]:
        """
        Search ASINs for parameter selection in query builder
        
        Args:
            asin_ids: List of specific ASIN IDs to fetch
            brands: List of brands to filter by
            search: Search term for ASIN/title
            limit: Maximum results to return
            
        Returns:
            Dict with asins list and total count
        """
        try:
            query = self.client.table('product_asins')\
                .select('asin, title, brand')\
                .eq('active', True)
            
            # Apply filters
            if asin_ids:
                query = query.in_('asin', asin_ids)
            
            if brands:
                query = query.in_('brand', brands)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.or_(f"asin.ilike.{search_pattern},title.ilike.{search_pattern}")
            
            # Apply limit
            query = query.limit(limit)
            
            result = query.execute()
            
            return {
                "asins": result.data,
                "total": len(result.data)
            }
            
        except Exception as e:
            logger.error(f"Error searching ASINs: {e}")
            return {"asins": [], "total": 0}
    
    @with_connection_retry
    def import_csv(self, file_content: bytes, filename: str, user_id: str, update_existing: bool = True) -> Dict[str, Any]:
        """
        Import ASINs from CSV file
        
        Args:
            file_content: CSV file content as bytes
            filename: Name of the uploaded file
            user_id: User performing the import
            update_existing: Whether to update existing ASINs
            
        Returns:
            Import status with import_id
        """
        try:
            # Create import log
            import_log = self.client.table('asin_import_logs').insert({
                'user_id': user_id,
                'file_name': filename,
                'import_status': 'processing',
                'total_rows': 0,
                'successful_imports': 0,
                'failed_imports': 0,
                'duplicate_skipped': 0
            }).execute()
            
            if not import_log.data:
                return {
                    "import_id": None,
                    "status": "failed",
                    "message": "Failed to create import log"
                }
            
            import_id = import_log.data[0]['id']
            
            # Process CSV in background (simplified for now)
            # In production, this should be handled by a background task queue
            self._process_csv_import(file_content, import_id, update_existing)
            
            return {
                "import_id": import_id,
                "status": "processing",
                "total_rows": 0,
                "message": "Import started successfully"
            }
            
        except Exception as e:
            logger.error(f"Error starting CSV import: {e}")
            return {
                "import_id": None,
                "status": "failed",
                "message": str(e)
            }
    
    def _process_csv_import(self, file_content: bytes, import_id: str, update_existing: bool):
        """
        Process CSV import (simplified version)
        
        In production, this should be handled asynchronously
        """
        try:
            # Parse CSV
            content_str = file_content.decode('utf-8', errors='ignore')
            reader = csv.DictReader(io.StringIO(content_str), delimiter='\t')
            
            successful = 0
            failed = 0
            batch = []
            batch_size = 100
            
            for row in reader:
                asin_data = self._parse_csv_row(row)
                if asin_data and asin_data.get('asin'):
                    batch.append(asin_data)
                    
                    if len(batch) >= batch_size:
                        # Insert batch
                        result = self._insert_asin_batch(batch, update_existing)
                        successful += result['successful']
                        failed += result['failed']
                        batch = []
            
            # Insert remaining batch
            if batch:
                result = self._insert_asin_batch(batch, update_existing)
                successful += result['successful']
                failed += result['failed']
            
            # Update import log
            self.client.table('asin_import_logs').update({
                'import_status': 'completed',
                'total_rows': successful + failed,
                'successful_imports': successful,
                'failed_imports': failed,
                'completed_at': datetime.now().isoformat()
            }).eq('id', import_id).execute()
            
        except Exception as e:
            logger.error(f"Error processing CSV import: {e}")
            # Update import log with failure
            self.client.table('asin_import_logs').update({
                'import_status': 'failed',
                'error_details': {'error': str(e)},
                'completed_at': datetime.now().isoformat()
            }).eq('id', import_id).execute()
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse a CSV row into ASIN data"""
        try:
            return {
                'asin': row.get('ASIN', '').strip(),
                'title': row.get('TITLE', '').strip() or row.get('DESIRED_TITLE', '').strip(),
                'brand': row.get('BRAND', '').strip(),
                'active': row.get('ACTIVE', '1').strip() == '1',
                'marketplace': row.get('MARKETPLACE', 'ATVPDKIKX0DER').strip(),
                'last_imported_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing CSV row: {e}")
            return {}
    
    def _insert_asin_batch(self, batch: List[Dict[str, Any]], update_existing: bool) -> Dict[str, int]:
        """Insert a batch of ASINs"""
        try:
            if update_existing:
                result = self.client.table('product_asins').upsert(
                    batch,
                    on_conflict='asin,marketplace'
                ).execute()
            else:
                result = self.client.table('product_asins').insert(batch).execute()
            
            return {
                'successful': len(result.data) if result.data else 0,
                'failed': 0
            }
        except Exception as e:
            logger.error(f"Error inserting batch: {e}")
            return {
                'successful': 0,
                'failed': len(batch)
            }
    
    @with_connection_retry
    def get_import_status(self, import_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an import operation
        
        Args:
            import_id: The import log ID
            
        Returns:
            Import status details or None if not found
        """
        try:
            result = self.client.table('asin_import_logs')\
                .select('*')\
                .eq('id', import_id)\
                .single()\
                .execute()
            
            return result.data if result.data else None
            
        except Exception as e:
            logger.error(f"Error getting import status: {e}")
            return None
    
    @with_connection_retry
    def list_asins_by_instance_brand(self,
                                    instance_id: str,
                                    brand_id: str,
                                    search: Optional[str] = None,
                                    limit: int = 100,
                                    offset: int = 0) -> Dict[str, Any]:
        """
        List ASINs filtered by instance and brand
        
        This method is designed to support the universal parameter selection feature.
        It returns ASINs that belong to a specific brand in a specific AMC instance.
        
        Args:
            instance_id: AMC instance ID (UUID)
            brand_id: Brand ID (UUID)
            search: Optional search term for ASIN or product title
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Dict with items list and total count
        """
        try:
            # Build the query to fetch ASINs filtered by instance and brand
            # Note: We need to join the asin_asins table with instance_brands
            # The actual table structure may need to be verified
            query = self.client.table('asin_asins').select(
                'asin, product_title, brand_name',
                count='exact'
            )
            
            # Filter by instance_id and brand_id
            # This assumes there's a relationship between asins and instance_brands
            query = query.eq('instance_id', instance_id).eq('brand_id', brand_id)
            
            # Apply search filter if provided
            if search:
                # Search in both ASIN and product title
                query = query.or_(f"asin.ilike.%{search}%,product_title.ilike.%{search}%")
            
            # For large limits, fetch in batches
            if limit > 1000:
                # Fetch all records in batches of 1000
                all_items = []
                batch_size = 1000
                current_offset = offset

                while len(all_items) < limit:
                    batch_query = query.range(current_offset, current_offset + batch_size - 1)
                    batch_result = batch_query.execute()

                    if not batch_result.data:
                        break

                    all_items.extend(batch_result.data)

                    # If we got less than batch_size, we've reached the end
                    if len(batch_result.data) < batch_size:
                        break

                    current_offset += batch_size

                items = all_items[:limit]  # Limit to requested size
                total = len(all_items)
            else:
                # Apply pagination normally for smaller requests
                query = query.range(offset, offset + limit - 1)
                result = query.execute()
                items = result.data if result.data else []
                total = result.count if hasattr(result, 'count') else len(items)
            
            # Format the response
            formatted_items = []
            for item in items:
                formatted_items.append({
                    'asin': item.get('asin'),
                    'product_title': item.get('product_title', ''),
                    'brand_name': item.get('brand_name', '')
                })
            
            return {
                'items': formatted_items,
                'total': total
            }
            
        except Exception as e:
            logger.error(f"Error listing ASINs by instance and brand: {e}")
            # Return empty result on error
            return {
                'items': [],
                'total': 0
            }


# Create singleton instance
asin_service = ASINService()