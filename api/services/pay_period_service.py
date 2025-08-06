"""
Pay Period service layer - business logic for pay period management
"""

from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from ..models.pay_period import (
    PayPeriod,
    PayPeriodCreate,
    PayScheduleConfig,
    PayPeriodStats,
    PaySchedule
)


class PayPeriodService:
    """Service class for pay period management business logic"""
    
    def __init__(self):
        # In a real application, this would be a database connection
        pass
    
    async def get_pay_periods(self, year: Optional[int] = None) -> Tuple[List[PayPeriod], int]:
        """Get pay periods with optional year filtering"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        periods_data = session.get_pay_periods()
        if not periods_data:
            return [], 0
        
        periods = []
        for i, period_data in enumerate(periods_data):
            period = PayPeriod(
                id=i,
                period_number=period_data.get('number', i + 1),
                start_date=datetime.fromisoformat(period_data['start_date']).date(),
                end_date=datetime.fromisoformat(period_data['end_date']).date(),
                pay_date=datetime.fromisoformat(period_data['pay_date']).date(),
                is_current=period_data.get('is_current', False),
                created_at=datetime.now()
            )
            
            # Filter by year if specified
            if year is None or period.start_date.year == year:
                periods.append(period)
        
        return periods, len(periods)
    
    async def get_pay_period_by_id(self, period_id: int) -> Optional[PayPeriod]:
        """Get pay period by ID"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        periods_data = session.get_pay_periods()
        if not periods_data or period_id >= len(periods_data):
            return None
        
        period_data = periods_data[period_id]
        return PayPeriod(
            id=period_id,
            period_number=period_data.get('number', period_id + 1),
            start_date=datetime.fromisoformat(period_data['start_date']).date(),
            end_date=datetime.fromisoformat(period_data['end_date']).date(),
            pay_date=datetime.fromisoformat(period_data['pay_date']).date(),
            is_current=period_data.get('is_current', False),
            created_at=datetime.now()
        )
    
    async def get_current_pay_period(self) -> Optional[PayPeriod]:
        """Get the current active pay period"""
        
        periods, _ = await self.get_pay_periods()
        today = date.today()
        
        # Find period that contains today's date
        for period in periods:
            if period.start_date <= today <= period.end_date:
                return period
        
        return None
    
    async def create_pay_period(self, period_data: PayPeriodCreate) -> PayPeriod:
        """Create a new pay period"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        periods = session.get_pay_periods()
        
        # Create new period data
        new_period_data = {
            'number': period_data.period_number,
            'start_date': period_data.start_date.isoformat(),
            'end_date': period_data.end_date.isoformat(),
            'pay_date': period_data.pay_date.isoformat(),
            'is_current': period_data.is_current,
            'created_at': datetime.now().isoformat()
        }
        
        periods.append(new_period_data)
        session.save_pay_periods(periods)
        
        return PayPeriod(
            id=len(periods) - 1,
            period_number=period_data.period_number,
            start_date=period_data.start_date,
            end_date=period_data.end_date,
            pay_date=period_data.pay_date,
            is_current=period_data.is_current,
            created_at=datetime.now()
        )
    
    async def delete_pay_period(self, period_id: int):
        """Delete a pay period"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        periods = session.get_pay_periods()
        if period_id >= len(periods):
            raise ValueError(f"Pay period with ID {period_id} not found")
        
        periods.pop(period_id)
        session.save_pay_periods(periods)
    
    async def generate_pay_periods(
        self, 
        config: PayScheduleConfig, 
        num_periods: int
    ) -> List[PayPeriod]:
        """Generate multiple pay periods based on schedule"""
        
        periods = []
        current_start = config.first_period_start
        
        for i in range(num_periods):
            # Calculate period end based on schedule
            if config.schedule == PaySchedule.WEEKLY:
                period_end = current_start + timedelta(days=6)
                next_start = current_start + timedelta(days=7)
            elif config.schedule == PaySchedule.BIWEEKLY:
                period_end = current_start + timedelta(days=13)
                next_start = current_start + timedelta(days=14)
            elif config.schedule == PaySchedule.SEMIMONTHLY:
                # Semi-monthly: 1st-15th and 16th-end of month
                if current_start.day == 1:
                    period_end = current_start.replace(day=15)
                    next_start = current_start.replace(day=16)
                else:
                    # Go to end of month, then start next month
                    next_month = current_start.replace(day=1) + relativedelta(months=1)
                    period_end = next_month - timedelta(days=1)
                    next_start = next_month
            else:  # MONTHLY
                next_month = current_start + relativedelta(months=1)
                period_end = next_month - timedelta(days=1)
                next_start = next_month
            
            # Calculate pay date
            pay_date = period_end + timedelta(days=config.pay_delay_days)
            
            # Create period
            period_create = PayPeriodCreate(
                period_number=i + 1,
                start_date=current_start,
                end_date=period_end,
                pay_date=pay_date,
                is_current=False
            )
            
            period = await self.create_pay_period(period_create)
            periods.append(period)
            
            current_start = next_start
        
        return periods
    
    async def get_pay_schedule_config(self) -> Optional[PayScheduleConfig]:
        """Get current pay schedule configuration"""
        
        from ..adapters.session_adapter import SessionAdapter
        session = SessionAdapter()
        
        # This would be stored separately in a real app
        # For now, infer from existing periods
        periods, _ = await self.get_pay_periods()
        if len(periods) < 2:
            return None
        
        # Infer schedule from period duration
        first_period = periods[0]
        second_period = periods[1]
        
        days_between = (second_period.start_date - first_period.start_date).days
        period_length = (first_period.end_date - first_period.start_date).days + 1
        pay_delay = (first_period.pay_date - first_period.end_date).days
        
        if days_between == 7:
            schedule = PaySchedule.WEEKLY
        elif days_between == 14:
            schedule = PaySchedule.BIWEEKLY
        elif period_length > 25:  # Approximation for monthly
            schedule = PaySchedule.MONTHLY
        else:
            schedule = PaySchedule.SEMIMONTHLY
        
        return PayScheduleConfig(
            schedule=schedule,
            first_period_start=first_period.start_date,
            pay_delay_days=pay_delay
        )
    
    async def save_pay_schedule_config(self, config: PayScheduleConfig) -> PayScheduleConfig:
        """Save pay schedule configuration"""
        
        # In a real app, this would be saved to database
        # For now, just return the config as confirmation
        return config
    
    async def get_pay_period_stats(self) -> PayPeriodStats:
        """Get pay period statistics"""
        
        periods, total = await self.get_pay_periods()
        current_period = await self.get_current_pay_period()
        config = await self.get_pay_schedule_config()
        
        # Find next pay date
        next_pay_date = None
        today = date.today()
        for period in periods:
            if period.pay_date >= today:
                next_pay_date = period.pay_date
                break
        
        # Calculate periods remaining in year
        year_periods = [p for p in periods if p.start_date.year == today.year]
        remaining = len([p for p in year_periods if p.start_date > today])
        
        return PayPeriodStats(
            total_periods=total,
            current_period_number=current_period.period_number if current_period else None,
            next_pay_date=next_pay_date,
            periods_remaining=remaining,
            schedule_type=config.schedule if config else None
        )