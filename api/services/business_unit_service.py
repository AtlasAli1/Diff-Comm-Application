"""
Business Unit service - handles business unit configuration and management
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from ..models.business_unit import (
    BusinessUnit,
    BusinessUnitCreate,
    BusinessUnitUpdate,
    BusinessUnitStats,
    CommissionRates
)


class BusinessUnitService:
    """Service class for business unit management"""
    
    def __init__(self):
        pass
    
    async def get_business_units(self) -> Tuple[List[BusinessUnit], int]:
        """Get all business units"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        settings = session.get_business_unit_settings()
        if not settings:
            return [], 0
        
        business_units = []
        for i, (name, config) in enumerate(settings.items()):
            rates = CommissionRates(
                lead_gen_rate=Decimal(str(config.get('lead_gen_rate', 0))),
                sold_by_rate=Decimal(str(config.get('sold_by_rate', 0))),
                work_done_rate=Decimal(str(config.get('work_done_rate', 0)))
            )
            
            business_unit = BusinessUnit(
                id=i,
                name=name,
                description=config.get('description', ''),
                enabled=config.get('enabled', True),
                rates=rates,
                auto_added=config.get('auto_added', False),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            business_units.append(business_unit)
        
        return business_units, len(business_units)
    
    async def get_business_unit_by_id(self, unit_id: int) -> Optional[BusinessUnit]:
        """Get business unit by ID"""
        
        business_units, _ = await self.get_business_units()
        if unit_id >= len(business_units):
            return None
        
        return business_units[unit_id]
    
    async def get_business_unit_by_name(self, name: str) -> Optional[BusinessUnit]:
        """Get business unit by name"""
        
        business_units, _ = await self.get_business_units()
        for unit in business_units:
            if unit.name == name:
                return unit
        return None
    
    async def create_or_update_business_unit(self, unit_data: BusinessUnitCreate) -> BusinessUnit:
        """Create or update business unit configuration"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        settings = session.get_business_unit_settings()
        
        # Create new configuration
        config = {
            'lead_gen_rate': float(unit_data.rates.lead_gen_rate),
            'sold_by_rate': float(unit_data.rates.sold_by_rate),
            'work_done_rate': float(unit_data.rates.work_done_rate),
            'enabled': unit_data.enabled,
            'description': unit_data.description or '',
            'auto_added': unit_data.auto_added,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        settings[unit_data.name] = config
        session.save_business_unit_settings(settings)
        
        # Return created/updated unit
        business_units, _ = await self.get_business_units()
        for unit in business_units:
            if unit.name == unit_data.name:
                return unit
        
        # Fallback - should not reach here
        raise ValueError("Failed to create business unit")
    
    async def update_business_unit(self, unit_id: int, unit_data: BusinessUnitUpdate) -> BusinessUnit:
        """Update existing business unit"""
        
        # Get current units
        business_units, _ = await self.get_business_units()
        if unit_id >= len(business_units):
            raise ValueError(f"Business unit with ID {unit_id} not found")
        
        current_unit = business_units[unit_id]
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        settings = session.get_business_unit_settings()
        current_config = settings.get(current_unit.name, {})
        
        # Update configuration with provided data
        if unit_data.name is not None and unit_data.name != current_unit.name:
            # Rename the business unit
            settings[unit_data.name] = settings.pop(current_unit.name)
            current_config = settings[unit_data.name]
        
        if unit_data.description is not None:
            current_config['description'] = unit_data.description
        
        if unit_data.enabled is not None:
            current_config['enabled'] = unit_data.enabled
        
        if unit_data.rates is not None:
            current_config['lead_gen_rate'] = float(unit_data.rates.lead_gen_rate)
            current_config['sold_by_rate'] = float(unit_data.rates.sold_by_rate)
            current_config['work_done_rate'] = float(unit_data.rates.work_done_rate)
        
        current_config['updated_at'] = datetime.now().isoformat()
        
        session.save_business_unit_settings(settings)
        
        # Return updated unit
        return await self.get_business_unit_by_id(unit_id)
    
    async def delete_business_unit(self, unit_id: int):
        """Delete business unit"""
        
        business_units, _ = await self.get_business_units()
        if unit_id >= len(business_units):
            raise ValueError(f"Business unit with ID {unit_id} not found")
        
        unit_to_delete = business_units[unit_id]
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        settings = session.get_business_unit_settings()
        if unit_to_delete.name in settings:
            del settings[unit_to_delete.name]
            session.save_business_unit_settings(settings)
    
    async def get_business_unit_stats(self) -> BusinessUnitStats:
        """Get business unit statistics"""
        
        business_units, total = await self.get_business_units()
        
        if not business_units:
            return BusinessUnitStats(
                total_units=0,
                enabled_units=0,
                disabled_units=0,
                auto_added_units=0,
                manually_created_units=0,
                avg_lead_gen_rate=Decimal('0.00'),
                avg_sales_rate=Decimal('0.00'),
                avg_work_done_rate=Decimal('0.00')
            )
        
        enabled_count = sum(1 for unit in business_units if unit.enabled)
        disabled_count = total - enabled_count
        auto_added_count = sum(1 for unit in business_units if unit.auto_added)
        manual_count = total - auto_added_count
        
        # Calculate averages
        avg_lead_gen = sum(unit.rates.lead_gen_rate for unit in business_units) / total
        avg_sales = sum(unit.rates.sold_by_rate for unit in business_units) / total
        avg_work_done = sum(unit.rates.work_done_rate for unit in business_units) / total
        
        return BusinessUnitStats(
            total_units=total,
            enabled_units=enabled_count,
            disabled_units=disabled_count,
            auto_added_units=auto_added_count,
            manually_created_units=manual_count,
            avg_lead_gen_rate=avg_lead_gen,
            avg_sales_rate=avg_sales,
            avg_work_done_rate=avg_work_done
        )