"""
Test PostgreSQL migration functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import text
from app.database import evolve_schema, migrate_existing_events_to_datetime, convert_halifax_to_utc
import pytz
from datetime import datetime, timezone


class TestPostgreSQLMigration:
    """Test PostgreSQL database migration functionality"""

    def test_convert_halifax_to_utc_function_handles_daylight_saving_correctly(self):
        """Test that Halifax to UTC conversion correctly handles daylight saving time"""
        halifax_tz = pytz.timezone('America/Halifax')
        
        # Test October date (should be ADT = UTC-3)
        start_utc, end_utc = convert_halifax_to_utc(
            '2025-10-16', '19:00', '21:00', halifax_tz
        )
        
        # 19:00 Halifax (ADT, UTC-3) should be 22:00 UTC
        assert start_utc.hour == 22
        assert start_utc.minute == 0
        assert start_utc.tzinfo == timezone.utc
        
        # 21:00 Halifax (ADT, UTC-3) should be 00:00 UTC next day
        assert end_utc.hour == 0
        assert end_utc.minute == 0
        assert end_utc.day == 17  # Next day
        assert end_utc.tzinfo == timezone.utc

    def test_convert_halifax_to_utc_handles_winter_time(self):
        """Test Halifax to UTC conversion in winter (AST = UTC-4)"""
        halifax_tz = pytz.timezone('America/Halifax')
        
        # Test January date (should be AST = UTC-4)
        start_utc, end_utc = convert_halifax_to_utc(
            '2025-01-15', '19:00', '21:00', halifax_tz
        )
        
        # 19:00 Halifax (AST, UTC-4) should be 23:00 UTC
        assert start_utc.hour == 23
        assert start_utc.minute == 0
        assert start_utc.tzinfo == timezone.utc

    @patch('app.database.text')
    def test_migrate_existing_events_handles_missing_table_gracefully(self, mock_text):
        """Test that migration handles case where events table doesn't exist"""
        
        # Mock connection
        mock_conn = Mock()
        
        # Mock table check query - return empty result (table doesn't exist)
        table_check_result = Mock()
        table_check_result.fetchone.return_value = None
        
        # Mock events query - should not be called
        events_result = Mock()
        events_result.fetchall.return_value = []
        
        # Configure mock to return different results for different queries
        mock_conn.execute.side_effect = [table_check_result, events_result]
        
        # This should complete without error and not attempt to migrate
        migrate_existing_events_to_datetime(mock_conn)
        
        # Verify table existence was checked
        assert mock_conn.execute.call_count == 1
        table_check_call = mock_conn.execute.call_args_list[0]
        # The actual SQL text will be wrapped in text(), so just check it was called
        assert table_check_call is not None

    @patch('app.database.text')
    def test_migrate_existing_events_processes_multiple_events(self, mock_text):
        """Test that migration can handle multiple events"""
        
        # Mock connection
        mock_conn = Mock()
        
        # Mock table exists
        table_check_result = Mock()
        table_check_result.fetchone.return_value = ('events',)
        
        # Mock events to migrate
        events_result = Mock()
        events_result.fetchall.return_value = [
            (1, '2025-10-16', '19:00', '21:00'),
            (2, '2025-10-17', '20:00', '22:00'),
        ]
        
        # Mock update results
        update_result = Mock()
        
        # Configure mock responses
        mock_conn.execute.side_effect = [
            table_check_result,  # Table exists check
            events_result,       # Events to migrate query
            update_result,       # First update
            update_result,       # Second update
        ]
        
        # Run migration
        migrate_existing_events_to_datetime(mock_conn)
        
        # Verify all queries were executed
        assert mock_conn.execute.call_count == 4

    @patch('app.database.text')
    def test_migrate_existing_events_handles_no_events_to_migrate(self, mock_text):
        """Test migration when no events need migrating"""
        
        # Mock connection
        mock_conn = Mock()
        
        # Mock table exists
        table_check_result = Mock()
        table_check_result.fetchone.return_value = ('events',)
        
        # Mock no events to migrate
        events_result = Mock()
        events_result.fetchall.return_value = []
        
        mock_conn.execute.side_effect = [table_check_result, events_result]
        
        # Should complete without error
        migrate_existing_events_to_datetime(mock_conn)
        
        # Should only call table check and events query
        assert mock_conn.execute.call_count == 2

    @patch('app.database.text')
    def test_migrate_existing_events_continues_on_individual_event_error(self, mock_text):
        """Test that migration continues when one event fails"""
        
        # Mock connection
        mock_conn = Mock()
        
        # Mock table exists
        table_check_result = Mock()
        table_check_result.fetchone.return_value = ('events',)
        
        # Mock events to migrate - one with invalid data
        events_result = Mock()
        events_result.fetchall.return_value = [
            (1, '2025-10-16', '19:00', '21:00'),  # Valid
            (2, 'invalid-date', '25:00', '99:99'),  # Invalid
            (3, '2025-10-17', '20:00', '22:00'),  # Valid
        ]
        
        # Mock update results - second one will fail during conversion
        update_result = Mock()
        
        # Configure mock responses
        mock_conn.execute.side_effect = [
            table_check_result,  # Table exists check  
            events_result,       # Events to migrate query
            update_result,       # First update (successful)
            # Second update won't happen due to conversion error
            update_result,       # Third update (successful)
        ]
        
        # Should complete without throwing exception
        migrate_existing_events_to_datetime(mock_conn)
        
        # Should process valid events despite invalid one
        # 1 table check + 1 events query + 2 successful updates = 4 calls
        assert mock_conn.execute.call_count == 4

    @patch('builtins.print')
    def test_evolve_schema_handles_postgresql_errors_gracefully(self, mock_print):
        """Test that schema evolution handles PostgreSQL errors gracefully"""
        
        # Mock engine and connection that raises an error
        mock_engine = Mock()
        mock_conn = Mock()
        mock_conn.execute.side_effect = Exception("Database connection error")
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn
        
        # Should not raise exception - should catch and print warning
        evolve_schema(mock_engine)
        
        # Should have printed error message
        mock_print.assert_called()
        error_calls = [call for call in mock_print.call_args_list if '⚠️' in str(call)]
        assert len(error_calls) > 0

    def test_database_migration_integration_with_memory_backend(self):
        """Integration test that migration works with existing memory backend"""
        
        # This test verifies that our migration code doesn't break existing functionality
        from app.database import migrate_events_to_datetime
        
        # Test data similar to what memory backend might have
        test_events = [
            {
                'id': 1,
                'date': '2025-10-16',
                'name': 'Youth Group',
                'desc': 'Weekly meeting',
                'start_time': '19:00',
                'end_time': '21:00',
                'location': 'Main Hall'
            }
        ]
        
        # Should successfully migrate
        migrated = migrate_events_to_datetime(test_events)
        
        # Should preserve all original fields
        assert len(migrated) == 1
        event = migrated[0]
        assert event['id'] == 1
        assert event['date'] == '2025-10-16'
        assert event['name'] == 'Youth Group'
        assert event['start_time'] == '19:00'
        assert event['end_time'] == '21:00'
        
        # Should add new datetime fields
        assert 'start_datetime' in event
        assert 'end_datetime' in event
        assert event['start_datetime'] is not None
        assert event['end_datetime'] is not None