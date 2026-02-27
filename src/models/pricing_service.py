"""
Pricing Service - Dynamic pricing management for rooms, devices, and services
Only accessible by admin and it_admin roles
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import src.db as db
from datetime import date, datetime
from typing import Optional, Dict, Any, List
import pandas as pd


class PricingService:
    """
    Service class for managing pricing catalog.
    Only admin and it_admin can view and edit pricing.
    """

    def __init__(self):
        """Initialize PricingService with database connection."""
        self.connection_pool = db.get_db_pool()

    def get_all_pricing(self) -> pd.DataFrame:
        """
        Get all pricing items with current effective rates.
        
        Returns:
            DataFrame with pricing information
        """
        query = """
            SELECT 
                pc.id,
                pc.item_type as category,
                CASE 
                    WHEN pc.item_type = 'room' THEN r.name
                    WHEN pc.item_type = 'device' THEN d.name
                    ELSE 'Unknown'
                END as item_name,
                pc.pricing_tier,
                pc.daily_rate,
                pc.weekly_rate,
                pc.monthly_rate,
                pc.effective_date,
                pc.expiry_date,
                pc.notes,
                pc.created_at
            FROM pricing_catalog pc
            LEFT JOIN rooms r ON pc.item_type = 'room' AND pc.item_id = r.id
            LEFT JOIN devices d ON pc.item_type = 'device' AND pc.item_id = d.id
            WHERE pc.effective_date <= CURRENT_DATE
            AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            ORDER BY pc.item_type, item_name
        """
        return db.run_query(query)

    def get_pricing_by_category(self, category: str) -> pd.DataFrame:
        """
        Get pricing for a specific category (room, device, etc.).
        
        Args:
            category: The item type category
            
        Returns:
            DataFrame with pricing for that category
        """
        query = """
            SELECT 
                pc.id,
                pc.item_type as category,
                CASE 
                    WHEN pc.item_type = 'room' THEN r.name
                    WHEN pc.item_type = 'device' THEN d.name
                    ELSE 'Unknown'
                END as item_name,
                pc.pricing_tier,
                pc.daily_rate,
                pc.weekly_rate,
                pc.monthly_rate,
                pc.effective_date,
                pc.expiry_date,
                pc.notes
            FROM pricing_catalog pc
            LEFT JOIN rooms r ON pc.item_type = 'room' AND pc.item_id = r.id
            LEFT JOIN devices d ON pc.item_type = 'device' AND pc.item_id = d.id
            WHERE pc.item_type = %s
            AND pc.effective_date <= CURRENT_DATE
            AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            ORDER BY item_name
        """
        return db.run_query(query, (category,))

    def update_pricing(
        self,
        pricing_id: int,
        daily_rate: Optional[float] = None,
        weekly_rate: Optional[float] = None,
        monthly_rate: Optional[float] = None,
        notes: Optional[str] = None,
        expiry_date: Optional[date] = None,
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update pricing for an item.
        
        Args:
            pricing_id: The pricing catalog ID
            daily_rate: New daily rate (optional)
            weekly_rate: New weekly rate (optional)
            monthly_rate: New monthly rate (optional)
            notes: Notes about the pricing (optional)
            expiry_date: When this pricing expires (optional)
            updated_by: Username of person making the update
            
        Returns:
            Dict with success status
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                # Build dynamic update query
                updates = []
                params = []
                
                if daily_rate is not None:
                    updates.append("daily_rate = %s")
                    params.append(daily_rate)
                
                if weekly_rate is not None:
                    updates.append("weekly_rate = %s")
                    params.append(weekly_rate)
                
                if monthly_rate is not None:
                    updates.append("monthly_rate = %s")
                    params.append(monthly_rate)
                
                if notes is not None:
                    updates.append("notes = %s")
                    params.append(notes)
                
                if expiry_date is not None:
                    updates.append("expiry_date = %s")
                    params.append(expiry_date)
                
                if not updates:
                    return {'success': False, 'message': 'No fields to update'}
                
                query = f"""
                    UPDATE pricing_catalog 
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING id
                """
                params.append(pricing_id)
                
                cur.execute(query, params)
                result = cur.fetchone()
                
                if result:
                    conn.commit()
                    return {
                        'success': True,
                        'message': f'Pricing #{pricing_id} updated successfully'
                    }
                else:
                    return {'success': False, 'message': 'Pricing item not found'}
                    
        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'message': f'Failed to update pricing: {str(e)}'}
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def create_pricing(
        self,
        item_type: str,
        item_id: int,
        daily_rate: Optional[float] = None,
        weekly_rate: Optional[float] = None,
        monthly_rate: Optional[float] = None,
        pricing_tier: str = 'standard',
        effective_date: date = None,
        expiry_date: Optional[date] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new pricing entry.
        
        Args:
            item_type: 'room' or 'device'
            item_id: The room_id or device_id
            daily_rate: Daily rate (optional)
            weekly_rate: Weekly rate (optional)
            monthly_rate: Monthly rate (optional)
            pricing_tier: 'standard', 'premium', etc.
            effective_date: When pricing becomes effective
            expiry_date: When pricing expires (optional)
            notes: Notes about the pricing
            created_by: Username of creator
            
        Returns:
            Dict with success status and new pricing ID
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            with conn.cursor() as cur:
                if effective_date is None:
                    effective_date = date.today()
                
                # Get user_id if provided
                user_id = None
                if created_by:
                    cur.execute("SELECT user_id FROM users WHERE username = %s", (created_by,))
                    user_result = cur.fetchone()
                    if user_result:
                        user_id = user_result[0]
                
                query = """
                    INSERT INTO pricing_catalog 
                    (item_type, item_id, pricing_tier, daily_rate, weekly_rate, monthly_rate,
                     effective_date, expiry_date, notes, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                cur.execute(query, (
                    item_type, item_id, pricing_tier, daily_rate, weekly_rate, monthly_rate,
                    effective_date, expiry_date, notes, user_id
                ))
                
                result = cur.fetchone()
                if result:
                    conn.commit()
                    return {
                        'success': True,
                        'pricing_id': result[0],
                        'message': f'Pricing created successfully for {item_type} #{item_id}'
                    }
                else:
                    return {'success': False, 'message': 'Failed to create pricing'}
                    
        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'message': f'Failed to create pricing: {str(e)}'}
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def get_rooms_without_pricing(self) -> pd.DataFrame:
        """Get rooms that don't have pricing set up yet."""
        query = """
            SELECT r.id, r.name, r.max_capacity
            FROM rooms r
            WHERE NOT EXISTS (
                SELECT 1 FROM pricing_catalog pc 
                WHERE pc.item_type = 'room' 
                AND pc.item_id = r.id
                AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            )
            AND r.is_active = true
            ORDER BY r.name
        """
        return db.run_query(query)

    def get_devices_without_pricing(self) -> pd.DataFrame:
        """Get devices that don't have pricing set up yet."""
        query = """
            SELECT d.id, d.name, dc.name as category
            FROM devices d
            JOIN device_categories dc ON d.category_id = dc.id
            WHERE NOT EXISTS (
                SELECT 1 FROM pricing_catalog pc 
                WHERE pc.item_type = 'device' 
                AND pc.item_id = d.id
                AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            )
            AND d.status != 'retired'
            ORDER BY dc.name, d.name
        """
        return db.run_query(query)

    def get_pricing_history(self, item_type: str, item_id: int) -> pd.DataFrame:
        """
        Get pricing history for a specific item.
        
        Args:
            item_type: 'room' or 'device'
            item_id: The room or device ID
            
        Returns:
            DataFrame with pricing history
        """
        query = """
            SELECT 
                pc.id,
                pc.pricing_tier,
                pc.daily_rate,
                pc.weekly_rate,
                pc.monthly_rate,
                pc.effective_date,
                pc.expiry_date,
                pc.notes,
                pc.created_at,
                u.username as created_by
            FROM pricing_catalog pc
            LEFT JOIN users u ON pc.created_by = u.user_id
            WHERE pc.item_type = %s
            AND pc.item_id = %s
            ORDER BY pc.effective_date DESC
        """
        return db.run_query(query, (item_type, item_id))
