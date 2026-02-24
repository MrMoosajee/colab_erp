"""
Notification Manager - Handles in-app notifications for IT Boss and Room Boss.
Keeps notifications forever for AI training purposes.
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Optional
import src.db as db


class NotificationManager:
    """
    Manages notifications for IT Boss and Room Boss.
    All notifications kept forever for AI training.
    """
    
    # Notification types
    TYPE_LOW_STOCK = 'low_stock'
    TYPE_CONFLICT_NO_ALTERNATIVES = 'conflict_no_alternatives'
    TYPE_OFFSITE_CONFLICT = 'offsite_conflict'
    TYPE_RETURN_OVERDUE = 'return_overdue'
    TYPE_DAILY_SUMMARY = 'daily_summary'
    
    def __init__(self):
        """Initialize NotificationManager."""
        pass
    
    def create_notification(
        self,
        notification_type: str,
        title: str,
        message: str,
        recipients: List[str],
        category_id: Optional[int] = None,
        related_booking_id: Optional[int] = None,
        related_device_id: Optional[int] = None
    ) -> Dict:
        """
        Create a new notification.
        
        Args:
            notification_type: Type of notification (low_stock, conflict, etc.)
            title: Short title for the notification
            message: Full message content
            recipients: List of roles to notify ['it_boss', 'room_boss']
            category_id: Optional device category ID
            related_booking_id: Optional related booking ID
            related_device_id: Optional related device ID
            
        Returns:
            Dict with success status and notification ID
        """
        try:
            query = """
                INSERT INTO notification_log 
                (notification_type, message, recipients, category_id, sent_via)
                VALUES (%s, %s, %s, %s, ARRAY['dashboard'])
                RETURNING id
            """
            
            result = db.run_transaction(
                query,
                (notification_type, f"{title}: {message}", recipients, category_id),
                fetch_one=True
            )
            
            if result:
                return {
                    'success': True,
                    'notification_id': result[0],
                    'message': f'Notification created for {recipients}'
                }
            else:
                return {'success': False, 'error': 'Failed to create notification'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_notifications_for_user(
        self,
        user_role: str,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get notifications for a specific user role.
        
        Args:
            user_role: Role of the user ('it_boss', 'room_boss', 'admin')
            unread_only: If True, only return unread notifications
            notification_type: Optional filter by type
            limit: Maximum number of notifications to return
            
        Returns:
            DataFrame with notifications
        """
        try:
            # Build query dynamically
            where_clauses = ["%s = ANY(recipients)"]
            params = [user_role]
            
            if unread_only:
                where_clauses.append("is_read = false")
            
            if notification_type:
                where_clauses.append("notification_type = %s")
                params.append(notification_type)
            
            where_clause = " AND ".join(where_clauses)
            
            query = f"""
                SELECT 
                    id,
                    notification_type,
                    message,
                    recipients,
                    is_read,
                    read_at,
                    created_at,
                    category_id,
                    threshold_percent
                FROM notification_log
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
            """
            params.append(limit)
            
            return db.run_query(query, tuple(params))
            
        except Exception as e:
            print(f"Error fetching notifications: {e}")
            return pd.DataFrame()
    
    def get_unread_count(self, user_role: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_role: Role of the user
            
        Returns:
            Integer count of unread notifications
        """
        try:
            query = """
                SELECT COUNT(*) as unread_count
                FROM notification_log
                WHERE %s = ANY(recipients)
                AND is_read = false
            """
            
            result = db.run_query(query, (user_role,))
            
            if not result.empty:
                return int(result.iloc[0]['unread_count'])
            return 0
            
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0
    
    def mark_as_read(self, notification_id: int) -> Dict:
        """
        Mark a specific notification as read.
        
        Args:
            notification_id: ID of the notification to mark
            
        Returns:
            Dict with success status
        """
        try:
            query = """
                UPDATE notification_log
                SET is_read = true, read_at = NOW()
                WHERE id = %s
            """
            
            db.run_transaction(query, (notification_id,))
            
            return {
                'success': True,
                'message': f'Notification {notification_id} marked as read'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def mark_all_as_read(self, user_role: str) -> Dict:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_role: Role of the user
            
        Returns:
            Dict with success status and count
        """
        try:
            query = """
                UPDATE notification_log
                SET is_read = true, read_at = NOW()
                WHERE %s = ANY(recipients)
                AND is_read = false
                RETURNING id
            """
            
            result = db.run_query(query, (user_role,))
            count = len(result)
            
            return {
                'success': True,
                'message': f'Marked {count} notifications as read',
                'count': count
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_low_stock(
        self,
        category: str,
        available_count: int,
        threshold: int = 5
    ) -> Optional[Dict]:
        """
        Check if stock is low and create notification if needed.
        
        Args:
            category: Device category name
            available_count: Number of available devices
            threshold: Minimum acceptable stock
            
        Returns:
            Dict with notification details if created, None otherwise
        """
        if available_count >= threshold:
            return None
        
        title = f"LOW STOCK: {category}s"
        message = f"Only {available_count} {category}s available. Threshold: {threshold}"
        recipients = ['it_boss', 'room_boss']
        
        return self.create_notification(
            notification_type=self.TYPE_LOW_STOCK,
            title=title,
            message=message,
            recipients=recipients
        )
    
    def notify_conflict_no_alternatives(
        self,
        device_serial: str,
        category: str,
        booking1_id: int,
        booking2_id: int
    ) -> Dict:
        """
        Notify when device conflict has no alternatives.
        
        Args:
            device_serial: Serial number of conflicting device
            category: Device category
            booking1_id: First conflicting booking
            booking2_id: Second conflicting booking
            
        Returns:
            Dict with success status
        """
        title = f"CONFLICT: No alternatives for {device_serial}"
        message = f"Device {device_serial} ({category}) has conflict between bookings #{booking1_id} and #{booking2_id}. No alternative devices available."
        recipients = ['it_boss', 'room_boss']
        
        return self.create_notification(
            notification_type=self.TYPE_CONFLICT_NO_ALTERNATIVES,
            title=title,
            message=message,
            recipients=recipients
        )
    
    def notify_offsite_conflict(
        self,
        device_serial: str,
        booking_id: int,
        client_name: str
    ) -> Dict:
        """
        Notify IT Boss about off-site rental conflict.
        
        Args:
            device_serial: Serial number
            booking_id: Booking ID
            client_name: Client name
            
        Returns:
            Dict with success status
        """
        title = f"OFFSITE CONFLICT: {device_serial}"
        message = f"Off-site rental conflict for device {device_serial} in booking #{booking_id} (Client: {client_name})"
        recipients = ['it_boss']
        
        return self.create_notification(
            notification_type=self.TYPE_OFFSITE_CONFLICT,
            title=title,
            message=message,
            recipients=recipients
        )
    
    def check_overdue_returns(self) -> List[Dict]:
        """
        Check for overdue off-site rentals and create notifications.
        
        Returns:
            List of created notifications
        """
        try:
            query = """
                SELECT 
                    or2.id as rental_id,
                    or2.rental_no,
                    or2.contact_person,
                    or2.return_expected_date,
                    b.client_name,
                    d.serial_number,
                    CURRENT_DATE - or2.return_expected_date as days_overdue
                FROM offsite_rentals or2
                JOIN booking_device_assignments bda ON or2.booking_device_assignment_id = bda.id
                JOIN bookings b ON bda.booking_id = b.id
                JOIN devices d ON bda.device_id = d.id
                WHERE or2.returned_at IS NULL
                AND or2.return_expected_date < CURRENT_DATE
                AND NOT EXISTS (
                    SELECT 1 FROM notification_log nl
                    WHERE nl.message LIKE '%' || or2.rental_no || '%'
                    AND nl.notification_type = 'return_overdue'
                    AND nl.created_at > CURRENT_DATE - INTERVAL '1 day'
                )
            """
            
            overdue_df = db.run_query(query)
            notifications = []
            
            for _, rental in overdue_df.iterrows():
                title = f"OVERDUE: Rental #{rental['rental_no']}"
                message = f"Off-site rental #{rental['rental_no']} is {rental['days_overdue']} days overdue. Client: {rental['client_name']}, Device: {rental['serial_number']}"
                recipients = ['it_boss']
                
                result = self.create_notification(
                    notification_type=self.TYPE_RETURN_OVERDUE,
                    title=title,
                    message=message,
                    recipients=recipients
                )
                notifications.append(result)
            
            return notifications
            
        except Exception as e:
            print(f"Error checking overdue returns: {e}")
            return []
    
    def get_daily_summary(self, user_role: str) -> Dict:
        """
        Get daily summary of notifications for a user.
        
        Args:
            user_role: Role of the user
            
        Returns:
            Dict with summary statistics
        """
        try:
            # Count by type
            query = """
                SELECT 
                    notification_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN is_read THEN 0 ELSE 1 END) as unread
                FROM notification_log
                WHERE %s = ANY(recipients)
                AND created_at >= CURRENT_DATE - INTERVAL '24 hours'
                GROUP BY notification_type
            """
            
            summary_df = db.run_query(query, (user_role,))
            
            summary = {
                'total_24h': 0,
                'unread_24h': 0,
                'by_type': {}
            }
            
            for _, row in summary_df.iterrows():
                notif_type = row['notification_type']
                count = int(row['count'])
                unread = int(row['unread'])
                
                summary['total_24h'] += count
                summary['unread_24h'] += unread
                summary['by_type'][notif_type] = {
                    'total': count,
                    'unread': unread
                }
            
            return summary
            
        except Exception as e:
            print(f"Error getting daily summary: {e}")
            return {'total_24h': 0, 'unread_24h': 0, 'by_type': {}}