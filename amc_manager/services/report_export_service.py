"""Service for managing report exports"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from ..services.db_service import DatabaseService, with_connection_retry
from ..core.logger_simple import get_logger

logger = get_logger(__name__)


class ReportExportService(DatabaseService):
    """Service for managing report exports and file generation"""

    def __init__(self):
        super().__init__()

    @with_connection_retry
    def create_export(self, export_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new export request

        Args:
            export_data: Export request data including:
                - report_configuration_id: Report configuration to export
                - export_format: Format (pdf, png, csv, excel)
                - user_id: User requesting the export

        Returns:
            Created export request
        """
        try:
            # Validate export format
            if not self.validate_export_format(export_data.get('export_format')):
                raise ValueError(f"Invalid export format: {export_data.get('export_format')}")

            # Prepare data for insertion
            insert_data = {
                'report_configuration_id': export_data['report_configuration_id'],
                'export_format': export_data['export_format'],
                'user_id': export_data['user_id'],
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.client.table('report_exports').insert(insert_data).execute()

            if response.data:
                logger.info(f"Created export request: {response.data[0]['id']}")
                return response.data[0]
            else:
                raise Exception("Failed to create export request")

        except Exception as e:
            logger.error(f"Error creating export request: {e}")
            raise

    @with_connection_retry
    def get_export(self, export_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an export by ID

        Args:
            export_id: Export ID
            user_id: User ID for authorization

        Returns:
            Export record or None if not found
        """
        try:
            response = self.client.table('report_exports')\
                .select('*')\
                .eq('id', export_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()

            if response.data:
                return response.data
            return None

        except Exception as e:
            logger.error(f"Error fetching export {export_id}: {e}")
            return None

    @with_connection_retry
    def list_user_exports(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all exports for a user

        Args:
            user_id: User ID
            status: Optional filter by status

        Returns:
            List of export records
        """
        try:
            query = self.client.table('report_exports')\
                .select('*')\
                .eq('user_id', user_id)

            if status:
                query = query.eq('status', status)

            response = query.order('created_at', desc=True).execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error listing exports for user {user_id}: {e}")
            return []

    @with_connection_retry
    def update_export_status(
        self,
        export_id: str,
        status: str,
        file_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update the status of an export

        Args:
            export_id: Export ID
            status: New status (pending, processing, completed, failed)
            file_url: URL of generated file (for completed exports)
            error_message: Error message (for failed exports)

        Returns:
            Updated export record or None if not found
        """
        try:
            # Validate status
            if not self.validate_export_status(status):
                raise ValueError(f"Invalid export status: {status}")

            update_data = {'status': status}

            if status == 'completed':
                if not file_url:
                    raise ValueError("File URL required for completed export")
                update_data['file_url'] = file_url
                update_data['generated_at'] = datetime.utcnow().isoformat()
                # Set expiration to 7 days from now
                update_data['expires_at'] = (datetime.utcnow() + timedelta(days=7)).isoformat()

            elif status == 'failed':
                update_data['error_message'] = error_message

            response = self.client.table('report_exports')\
                .update(update_data)\
                .eq('id', export_id)\
                .execute()

            if response.data:
                logger.info(f"Updated export {export_id} status to {status}")
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating export {export_id} status: {e}")
            raise

    @with_connection_retry
    def update_export_file_info(self, export_id: str, file_url: str, file_size: int) -> Optional[Dict[str, Any]]:
        """
        Update file information for an export

        Args:
            export_id: Export ID
            file_url: URL of the exported file
            file_size: Size of the file in bytes

        Returns:
            Updated export record or None if not found
        """
        try:
            update_data = {
                'file_url': file_url,
                'file_size': file_size,
                'status': 'completed',
                'generated_at': datetime.utcnow().isoformat(),
                'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
            }

            response = self.client.table('report_exports')\
                .update(update_data)\
                .eq('id', export_id)\
                .execute()

            if response.data:
                logger.info(f"Updated export {export_id} file info")
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error updating export {export_id} file info: {e}")
            raise

    @with_connection_retry
    def delete_export(self, export_id: str, user_id: str) -> bool:
        """
        Delete an export record

        Args:
            export_id: Export ID
            user_id: User ID for authorization

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = self.client.table('report_exports')\
                .delete()\
                .eq('id', export_id)\
                .eq('user_id', user_id)\
                .execute()

            if response.data:
                logger.info(f"Deleted export: {export_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting export {export_id}: {e}")
            return False

    @with_connection_retry
    def delete_expired_exports(self, cutoff_date: Optional[datetime] = None) -> int:
        """
        Delete expired export records

        Args:
            cutoff_date: Optional cutoff date, defaults to now

        Returns:
            Number of exports deleted
        """
        try:
            if cutoff_date is None:
                cutoff_date = datetime.utcnow()

            response = self.client.table('report_exports')\
                .delete()\
                .lt('expires_at', cutoff_date.isoformat())\
                .execute()

            count = len(response.data) if response.data else 0
            logger.info(f"Deleted {count} expired exports")
            return count

        except Exception as e:
            logger.error(f"Error deleting expired exports: {e}")
            return 0

    @with_connection_retry
    def cancel_export(self, export_id: str, user_id: str) -> bool:
        """
        Cancel a pending or processing export

        Args:
            export_id: Export ID
            user_id: User ID for authorization

        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            # First check current status
            export = self.get_export(export_id, user_id)
            if not export:
                return False

            # Can only cancel pending or processing exports
            if export['status'] not in ['pending', 'processing']:
                logger.warning(f"Cannot cancel export {export_id} with status {export['status']}")
                return False

            # Update status to cancelled
            response = self.client.table('report_exports')\
                .update({'status': 'cancelled'})\
                .eq('id', export_id)\
                .eq('user_id', user_id)\
                .execute()

            if response.data:
                logger.info(f"Cancelled export: {export_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error cancelling export {export_id}: {e}")
            return False

    @with_connection_retry
    def get_export_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get export statistics for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with export statistics
        """
        try:
            exports = self.list_user_exports(user_id)

            # Initialize stats
            stats = {
                'total': len(exports),
                'completed': 0,
                'pending': 0,
                'processing': 0,
                'failed': 0,
                'cancelled': 0,
                'by_format': defaultdict(int),
                'total_size_bytes': 0,
                'average_generation_time_seconds': 0
            }

            generation_times = []

            for export in exports:
                # Count by status
                status = export.get('status', 'unknown')
                if status in stats:
                    stats[status] += 1

                # Count by format
                format_type = export.get('export_format', 'unknown')
                stats['by_format'][format_type] += 1

                # Sum file sizes
                if export.get('file_size'):
                    stats['total_size_bytes'] += export['file_size']

                # Calculate generation times
                if export.get('created_at') and export.get('generated_at'):
                    created = datetime.fromisoformat(export['created_at'].replace('Z', '+00:00'))
                    generated = datetime.fromisoformat(export['generated_at'].replace('Z', '+00:00'))
                    generation_time = (generated - created).total_seconds()
                    generation_times.append(generation_time)

            # Calculate average generation time
            if generation_times:
                stats['average_generation_time_seconds'] = sum(generation_times) / len(generation_times)

            # Convert defaultdict to regular dict for JSON serialization
            stats['by_format'] = dict(stats['by_format'])

            return stats

        except Exception as e:
            logger.error(f"Error getting export stats for user {user_id}: {e}")
            return {}

    @with_connection_retry
    def get_pending_exports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending exports for processing

        Args:
            limit: Maximum number of exports to retrieve

        Returns:
            List of pending export records
        """
        try:
            response = self.client.table('report_exports')\
                .select('*')\
                .eq('status', 'pending')\
                .order('created_at')\
                .limit(limit)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching pending exports: {e}")
            return []

    @with_connection_retry
    def get_exports_by_report_config(self, report_config_id: str) -> List[Dict[str, Any]]:
        """
        Get all exports for a specific report configuration

        Args:
            report_config_id: Report configuration ID

        Returns:
            List of export records
        """
        try:
            response = self.client.table('report_exports')\
                .select('*')\
                .eq('report_configuration_id', report_config_id)\
                .order('created_at', desc=True)\
                .execute()

            return response.data if response.data else []

        except Exception as e:
            logger.error(f"Error fetching exports for report config {report_config_id}: {e}")
            return []

    @with_connection_retry
    def check_duplicate_export(
        self,
        report_config_id: str,
        user_id: str,
        export_format: str,
        hours: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a similar export was recently created to avoid duplicates

        Args:
            report_config_id: Report configuration ID
            user_id: User ID
            export_format: Export format
            hours: Number of hours to look back for duplicates

        Returns:
            Existing export if found, None otherwise
        """
        try:
            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            response = self.client.table('report_exports')\
                .select('*')\
                .eq('report_configuration_id', report_config_id)\
                .eq('user_id', user_id)\
                .eq('export_format', export_format)\
                .in_('status', ['pending', 'processing', 'completed'])\
                .gte('created_at', cutoff_time)\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()

            if response.data:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Error checking for duplicate export: {e}")
            return None

    def validate_export_format(self, export_format: str) -> bool:
        """
        Validate export format against allowed values

        Args:
            export_format: Export format to validate

        Returns:
            True if valid, False otherwise
        """
        valid_formats = ['pdf', 'png', 'csv', 'excel']
        return export_format in valid_formats

    def validate_export_status(self, status: str) -> bool:
        """
        Validate export status against allowed values

        Args:
            status: Status to validate

        Returns:
            True if valid, False otherwise
        """
        valid_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        return status in valid_statuses

    def get_file_extension(self, export_format: str) -> str:
        """
        Get file extension for export format

        Args:
            export_format: Export format

        Returns:
            File extension including dot
        """
        extensions = {
            'pdf': '.pdf',
            'png': '.png',
            'csv': '.csv',
            'excel': '.xlsx'
        }
        return extensions.get(export_format, '.dat')

    def get_mime_type(self, export_format: str) -> str:
        """
        Get MIME type for export format

        Args:
            export_format: Export format

        Returns:
            MIME type string
        """
        mime_types = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'csv': 'text/csv',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        return mime_types.get(export_format, 'application/octet-stream')