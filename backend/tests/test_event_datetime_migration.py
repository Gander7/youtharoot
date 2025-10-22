"""
Test suite for event datetime migration from date/time strings to UTC datetimes.
Following TDD methodology - these tests will fail initially (RED phase).
"""

import pytest
from datetime import datetime, timezone
from app.models import Event, EventCreate, EventUpdate
from app.db_models import EventDB
from app.repositories.memory import InMemoryEventRepository
import pytz

class TestEventDateTimeMigration:
    """Test suite for event datetime migration from date/time strings to UTC datetimes"""
    
    @pytest.fixture
    def halifax_tz(self):
        return pytz.timezone('America/Halifax')
    
    @pytest.fixture
    def sample_legacy_event_data(self):
        """Legacy event data with separate date and time fields"""
        return {
            "name": "Youth Group Meeting",
            "date": "2025-10-16",  # Halifax date
            "start_time": "19:00",  # Halifax time
            "end_time": "21:00",    # Halifax time
            "location": "Church Hall"
        }
    
    def test_event_model_should_have_new_datetime_fields(self):
        """Test that Event model has new datetime fields while keeping legacy fields"""
        # This test will fail initially - RED phase
        event_data = {
            "id": 1,
            "name": "Test Event",
            "date": "2025-10-16",
            "start_time": "19:00", 
            "end_time": "21:00",
            "location": "Test Location",
            "start_datetime": datetime(2025, 10, 16, 23, 0, 0, tzinfo=timezone.utc),  # 7PM Halifax = 11PM UTC
            "end_datetime": datetime(2025, 10, 17, 1, 0, 0, tzinfo=timezone.utc)     # 9PM Halifax = 1AM UTC next day
        }
        
        event = Event(**event_data)
        
        # Should have both legacy and new fields
        assert event.date == "2025-10-16"
        assert event.start_time == "19:00"
        assert event.end_time == "21:00"
        assert event.start_datetime == datetime(2025, 10, 16, 23, 0, 0, tzinfo=timezone.utc)
        assert event.end_datetime == datetime(2025, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
    
    def test_event_create_should_accept_legacy_fields_and_generate_utc_datetimes(self):
        """Test that EventCreate can convert legacy Halifax date/time to UTC datetimes"""
        # This will fail initially - RED phase
        legacy_data = {
            "name": "Test Event",
            "date": "2025-10-16",
            "start_time": "19:00",
            "end_time": "21:00",
            "location": "Test Location"
        }
        
        event_create = EventCreate(**legacy_data)
        
        # Should auto-generate UTC datetimes from Halifax date/time
        expected_start_utc = datetime(2025, 10, 16, 22, 0, 0, tzinfo=timezone.utc)  # 7PM Halifax = 10PM UTC (ADT is UTC-3)
        expected_end_utc = datetime(2025, 10, 17, 0, 0, 0, tzinfo=timezone.utc)     # 9PM Halifax = 12AM UTC next day
        
        assert event_create.start_datetime == expected_start_utc
        assert event_create.end_datetime == expected_end_utc
    
    def test_halifax_to_utc_conversion_should_handle_daylight_saving(self, halifax_tz):
        """Test conversion handles Atlantic Daylight Time (ADT) and Atlantic Standard Time (AST)"""
        # Summer date (ADT = UTC-3)
        summer_data = {
            "name": "Summer Event",
            "date": "2025-07-15",  # During daylight saving
            "start_time": "19:00",
            "end_time": "21:00",
            "location": "Test"
        }
        
        # Winter date (AST = UTC-4) 
        winter_data = {
            "name": "Winter Event", 
            "date": "2025-01-15",  # During standard time
            "start_time": "19:00",
            "end_time": "21:00",
            "location": "Test"
        }
        
        summer_event = EventCreate(**summer_data)
        winter_event = EventCreate(**winter_data)
        
        # Summer: 7PM ADT = 10PM UTC (UTC-3)
        assert summer_event.start_datetime.hour == 22  # 7PM + 3 hours = 10PM UTC
        
        # Winter: 7PM AST = 11PM UTC (UTC-4)  
        assert winter_event.start_datetime.hour == 23  # 7PM + 4 hours = 11PM UTC
    
    def test_database_schema_should_have_new_datetime_columns(self):
        """Test that EventDB has new datetime columns"""
        # This will fail initially - RED phase
        event_db = EventDB(
            id=1,
            name="Test Event",
            date="2025-10-16",
            start_time="19:00",
            end_time="21:00", 
            location="Test",
            start_datetime=datetime(2025, 10, 16, 23, 0, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 10, 17, 1, 0, 0, tzinfo=timezone.utc)
        )
        
        assert hasattr(event_db, 'start_datetime')
        assert hasattr(event_db, 'end_datetime')
        assert event_db.start_datetime.tzinfo == timezone.utc
        assert event_db.end_datetime.tzinfo == timezone.utc
    
    def test_migration_script_should_convert_existing_data(self, sample_legacy_event_data, halifax_tz):
        """Test migration script converts existing Halifax date/time to UTC"""
        # This will be implemented in migration script
        from app.database import migrate_events_to_datetime
        
        # Mock existing data
        existing_events = [sample_legacy_event_data]
        
        migrated_events = migrate_events_to_datetime(existing_events)
        
        migrated = migrated_events[0]
        
        # Should have converted Halifax time to UTC
        # 2025-10-16 19:00 Halifax should become UTC datetime
        expected_start_utc = halifax_tz.localize(
            datetime(2025, 10, 16, 19, 0)
        ).astimezone(timezone.utc)
        
        assert migrated['start_datetime'] == expected_start_utc
    
    @pytest.mark.asyncio
    async def test_repository_should_handle_both_legacy_and_new_fields(self):
        """Test that repositories can work with both old and new datetime fields"""
        # This ensures backward compatibility
        repo = InMemoryEventRepository()
        
        # Create event with legacy fields
        legacy_event_data = EventCreate(
            name="Legacy Event",
            date="2025-10-16", 
            start_time="19:00",
            end_time="21:00",
            location="Test"
        )
        
        created_event = await repo.create_event(legacy_event_data)
        
        # Should have both legacy and new fields populated
        assert created_event.date == "2025-10-16"
        assert created_event.start_time == "19:00"
        assert created_event.end_time == "21:00"
        assert created_event.start_datetime is not None
        assert created_event.end_datetime is not None
        assert created_event.start_datetime.tzinfo == timezone.utc

    def test_event_update_should_regenerate_datetimes_when_legacy_fields_change(self):
        """Test that updating legacy date/time fields regenerates UTC datetimes"""
        # This will fail initially - RED phase
        update_data = {
            "date": "2025-10-17",
            "start_time": "20:00",
            "end_time": "22:00"
        }
        
        event_update = EventUpdate(**update_data)
        
        # Should auto-generate new UTC datetimes
        expected_start_utc = datetime(2025, 10, 17, 23, 0, 0, tzinfo=timezone.utc)  # 8PM Halifax = 11PM UTC (ADT is UTC-3)
        expected_end_utc = datetime(2025, 10, 18, 1, 0, 0, tzinfo=timezone.utc)    # 10PM Halifax = 1AM UTC next day
        
        assert event_update.start_datetime == expected_start_utc
        assert event_update.end_datetime == expected_end_utc

    def test_event_model_should_handle_missing_datetime_fields_gracefully(self):
        """Test that Event model handles cases where datetime fields are None"""
        # For backward compatibility with existing data
        event_data = {
            "id": 1,
            "name": "Legacy Event",
            "date": "2025-10-16",
            "start_time": "19:00",
            "end_time": "21:00",
            "location": "Test Location"
            # start_datetime and end_datetime are None/missing
        }
        
        event = Event(**event_data)
        
        # Should handle missing datetime fields gracefully
        assert event.date == "2025-10-16"
        assert event.start_time == "19:00"
        assert event.end_time == "21:00"
        assert event.start_datetime is None
        assert event.end_datetime is None

class TestDateTimeConversionUtilities:
    """Test the utility functions for date/time conversion"""
    
    def test_convert_halifax_to_utc_function(self):
        """Test the core Halifax to UTC conversion function"""
        from app.database import convert_halifax_to_utc
        
        halifax_tz = pytz.timezone('America/Halifax')
        
        # Test October date (during standard time)
        start_utc, end_utc = convert_halifax_to_utc(
            "2025-10-16", "19:00", "21:00", halifax_tz
        )
        
        # 7PM Halifax in October = 10PM UTC (ADT is UTC-3)
        assert start_utc.hour == 22
        assert start_utc.minute == 0
        assert start_utc.tzinfo == timezone.utc
        
        # 9PM Halifax in October = 12AM UTC next day
        assert end_utc.hour == 0
        assert end_utc.minute == 0
        assert end_utc.day == 17  # Next day in UTC
    
    def test_convert_halifax_to_utc_with_daylight_saving(self):
        """Test conversion during daylight saving time periods"""
        from app.database import convert_halifax_to_utc
        
        halifax_tz = pytz.timezone('America/Halifax')
        
        # Test July date (during daylight saving time)
        start_utc, end_utc = convert_halifax_to_utc(
            "2025-07-15", "19:00", "21:00", halifax_tz
        )
        
        # 7PM Halifax in July = 10PM UTC (ADT is UTC-3)
        assert start_utc.hour == 22
        assert start_utc.minute == 0
        assert start_utc.day == 15  # Same day in UTC during DST