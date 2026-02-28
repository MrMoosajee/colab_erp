"""
Pricing Service - Dynamic pricing management for rooms, devices, and catering
Only accessible by admin and it_admin roles
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import src.db as db
from datetime import date, datetime
from typing import Optional, Dict, Any
import pandas as pd


class PricingService:
    """
    Service class for managing pricing catalog.
    Supports: room pricing, collective device pricing, catering/supplies pricing
    """

    def __init__(self):
        """Initialize PricingService."""
        pass

    # =========================================================================
    # ROOM PRICING
    # =========================================================================

    def get_room_pricing(self) -> pd.DataFrame:
        """Get all room pricing."""
        query = """
            SELECT 
                pc.id,
                r.name as item_name,
                'room' as category,
                pc.daily_rate,
                pc.weekly_rate,
                pc.monthly_rate,
                pc.pricing_tier,
                pc.notes,
                r.max_capacity
            FROM pricing_catalog pc
            JOIN rooms r ON pc.item_type = 'room' AND pc.item_id = r.id
            WHERE pc.effective_date <= CURRENT_DATE
            AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            ORDER BY r.name
        """
        return db.run_query(query)

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

    # =========================================================================
    # DEVICE PRICING (Collective by Category)
    # =========================================================================

    def get_device_pricing(self) -> pd.DataFrame:
        """Get collective device pricing by category."""
        query = """
            SELECT 
                pc.id,
                dc.name as item_name,
                'device' as category,
                pc.daily_rate,
                pc.weekly_rate,
                pc.monthly_rate,
                pc.pricing_tier,
                pc.notes,
                COUNT(d.id) as device_count
            FROM pricing_catalog pc
            JOIN device_categories dc ON pc.item_type = 'device_category' AND pc.item_id = dc.id
            LEFT JOIN devices d ON d.category_id = dc.id AND d.status != 'retired'
            WHERE pc.effective_date <= CURRENT_DATE
            AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            GROUP BY pc.id, dc.name, pc.daily_rate, pc.weekly_rate, pc.monthly_rate, pc.pricing_tier, pc.notes
            ORDER BY dc.name
        """
        return db.run_query(query)

    def get_device_categories_without_pricing(self) -> pd.DataFrame:
        """Get device categories that don't have pricing set up yet."""
        query = """
            SELECT dc.id, dc.name, COUNT(d.id) as device_count
            FROM device_categories dc
            LEFT JOIN devices d ON d.category_id = dc.id AND d.status != 'retired'
            WHERE NOT EXISTS (
                SELECT 1 FROM pricing_catalog pc 
                WHERE pc.item_type = 'device_category' 
                AND pc.item_id = dc.id
                AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            )
            GROUP BY dc.id, dc.name
            ORDER BY dc.name
        """
        return db.run_query(query)

    # =========================================================================
    # CATERING & SUPPLIES PRICING
    # =========================================================================

    def get_catering_pricing(self) -> pd.DataFrame:
        """Get all catering and supplies pricing."""
        query = """
            SELECT 
                pc.id,
                pc.item_name,
                'catering' as category,
                pc.daily_rate as unit_price,
                pc.unit,
                pc.pricing_tier,
                pc.notes,
                pc.effective_date
            FROM pricing_catalog pc
            WHERE pc.item_type = 'catering'
            AND pc.effective_date <= CURRENT_DATE
            AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            ORDER BY pc.item_name
        """
        return db.run_query(query)

    def get_catering_items(self) -> pd.DataFrame:
        """Get all available catering items."""
        query = """
            SELECT 
                pc.id,
                pc.item_name,
                pc.daily_rate as unit_price,
                pc.unit,
                pc.notes
            FROM pricing_catalog pc
            WHERE pc.item_type = 'catering'
            AND pc.effective_date <= CURRENT_DATE
            AND (pc.expiry_date IS NULL OR pc.expiry_date >= CURRENT_DATE)
            AND pc.is_active = true
            ORDER BY pc.item_name
        """
        return db.run_query(query)

    # =========================================================================
    # PRICING MANAGEMENT
    # =========================================================================

    def create_room_pricing(
        self,
        room_id: int,
        daily_rate: float,
        weekly_rate: Optional[float] = None,
        monthly_rate: Optional[float] = None,
        pricing_tier: str = 'standard',
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create pricing for a room."""
        return self._create_pricing(
            item_type='room',
            item_id=room_id,
            item_name=None,
            daily_rate=daily_rate,
            weekly_rate=weekly_rate,
            monthly_rate=monthly_rate,
            unit='per day',
            pricing_tier=pricing_tier,
            notes=notes
        )

    def create_device_category_pricing(
        self,
        category_id: int,
        daily_rate: float,
        weekly_rate: Optional[float] = None,
        monthly_rate: Optional[float] = None,
        pricing_tier: str = 'standard',
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create collective pricing for a device category."""
        return self._create_pricing(
            item_type='device_category',
            item_id=category_id,
            item_name=None,
            daily_rate=daily_rate,
            weekly_rate=weekly_rate,
            monthly_rate=monthly_rate,
            unit='per device',
            pricing_tier=pricing_tier,
            notes=notes
        )

    def create_catering_pricing(
        self,
        item_name: str,
        unit_price: float,
        unit: str = 'per person',
        pricing_tier: str = 'standard',
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create pricing for a catering/supplies item."""
        return self._create_pricing(
            item_type='catering',
            item_id=0,  # Not used for catering
            item_name=item_name,
            daily_rate=unit_price,
            weekly_rate=None,
            monthly_rate=None,
            unit=unit,
            pricing_tier=pricing_tier,
            notes=notes
        )

    def _create_pricing(
        self,
        item_type: str,
        item_id: int,
        item_name: Optional[str],
        daily_rate: float,
        weekly_rate: Optional[float],
        monthly_rate: Optional[float],
        unit: str,
        pricing_tier: str,
        notes: Optional[str]
    ) -> Dict[str, Any]:
        """Internal method to create pricing entry."""
        try:
            query = """
                INSERT INTO pricing_catalog 
                (item_type, item_id, item_name, daily_rate, weekly_rate, monthly_rate,
                 unit, pricing_tier, notes, effective_date, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, true)
                RETURNING id
            """
            result = db.run_transaction(
                query,
                (item_type, item_id, item_name, daily_rate, weekly_rate, monthly_rate,
                 unit, pricing_tier, notes),
                fetch_one=True
            )
            
            if result:
                return {
                    'success': True,
                    'pricing_id': result[0],
                    'message': f'Pricing created successfully'
                }
            return {'success': False, 'message': 'Failed to create pricing'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def update_pricing(
        self,
        pricing_id: int,
        daily_rate: Optional[float] = None,
        weekly_rate: Optional[float] = None,
        monthly_rate: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update pricing rates."""
        try:
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
            
            if not updates:
                return {'success': False, 'message': 'No fields to update'}
            
            query = f"""
                UPDATE pricing_catalog 
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id
            """
            params.append(pricing_id)
            
            result = db.run_transaction(query, params, fetch_one=True)
            
            if result:
                return {'success': True, 'message': 'Pricing updated successfully'}
            return {'success': False, 'message': 'Pricing not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def delete_pricing(self, pricing_id: int) -> Dict[str, Any]:
        """Soft delete pricing by setting expiry date."""
        try:
            query = """
                UPDATE pricing_catalog 
                SET expiry_date = CURRENT_DATE - 1
                WHERE id = %s
            """
            db.run_transaction(query, (pricing_id,))
            return {'success': True, 'message': 'Pricing removed successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
