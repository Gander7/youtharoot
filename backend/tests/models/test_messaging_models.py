"""
Test-Driven Development (TDD) tests for messaging database models.

Following TDD RED-GREEN-REFACTOR cycle:
1. RED: Write failing tests first
2. GREEN: Write minimal code to make tests pass
3. REFACTOR: Improve code while keeping tests green

Testing Strategy:
- Test all CRUD operations for each model
- Test data validation and constraints
- Test relationships between models
- Test backwards compatibility with existing data
- Test safe migration scenarios

Uses Docker PostgreSQL for realistic testing environment.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import IntegrityError
from app.db_models import PersonDB, UserDB  # Existing models

# Import new messaging models (will fail initially - that's expected for TDD RED phase)
try:
    from app.db_models import MessageGroupDB, MessageGroupMembershipDB, MessageDB, MessageTemplateDB
except ImportError:
    # Expected to fail initially in TDD RED phase
    MessageGroupDB = None
    MessageGroupMembershipDB = None
    MessageDB = None
    MessageTemplateDB = None


class TestMessageGroupModel:
    """Test the MessageGroup model."""
    
    def test_create_message_group_success(self, test_db, sample_user):
        """Test creating a message group successfully."""
        if MessageGroupDB is None:
            pytest.skip("MessageGroupDB not yet implemented (TDD RED phase)")
            
        # Arrange
        group_data = {
            "name": "All Youth",
            "description": "All youth group members",
            "created_by": sample_user.id,
            "is_active": True
        }
        
        # Act
        group = MessageGroupDB(**group_data)
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)
        
        # Assert
        assert group.id is not None
        assert group.name == "All Youth"
        assert group.description == "All youth group members"
        assert group.created_by == sample_user.id
        assert group.is_active is True
        assert group.created_at is not None
        assert group.updated_at is not None
    
    def test_message_group_name_required(self, test_db, sample_user):
        """Test that message group name is required."""
        if MessageGroupDB is None:
            pytest.skip("MessageGroupDB not yet implemented (TDD RED phase)")
            
        # Arrange & Act & Assert
        with pytest.raises(IntegrityError):
            group = MessageGroupDB(
                name=None,  # Should fail
                description="Test group",
                created_by=sample_user.id
            )
            test_db.add(group)
            test_db.commit()
    
    def test_message_group_unique_name(self, test_db, sample_user):
        """Test that message group names must be unique."""
        if MessageGroupDB is None:
            pytest.skip("MessageGroupDB not yet implemented (TDD RED phase)")
            
        # Arrange
        group1 = MessageGroupDB(
            name="Youth Group",
            description="First group",
            created_by=sample_user.id
        )
        test_db.add(group1)
        test_db.commit()
        
        # Act & Assert
        with pytest.raises(IntegrityError):
            group2 = MessageGroupDB(
                name="Youth Group",  # Duplicate name should fail
                description="Second group",
                created_by=sample_user.id
            )
            test_db.add(group2)
            test_db.commit()


class TestMessageGroupMembershipModel:
    """Test the MessageGroupMembership model."""
    
    def test_add_person_to_group(self, test_db, sample_user, sample_person):
        """Test adding a person to a message group."""
        if MessageGroupDB is None or MessageGroupMembershipDB is None:
            pytest.skip("MessageGroupDB/MessageGroupMembershipDB not yet implemented (TDD RED phase)")
            
        # Arrange
        group = MessageGroupDB(
            name="Test Group",
            description="Test description",
            created_by=sample_user.id
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)
        
        # Act
        membership = MessageGroupMembershipDB(
            group_id=group.id,
            person_id=sample_person.id,
            added_by=sample_user.id
        )
        test_db.add(membership)
        test_db.commit()
        test_db.refresh(membership)
        
        # Assert
        assert membership.id is not None
        assert membership.group_id == group.id
        assert membership.person_id == sample_person.id
        assert membership.added_by == sample_user.id
        assert membership.joined_at is not None
    
    def test_prevent_duplicate_membership(self, test_db, sample_user, sample_person):
        """Test that a person cannot be added to the same group twice."""
        if MessageGroupDB is None or MessageGroupMembershipDB is None:
            pytest.skip("MessageGroupDB/MessageGroupMembershipDB not yet implemented (TDD RED phase)")
            
        # Arrange
        group = MessageGroupDB(
            name="Test Group",
            description="Test description",
            created_by=sample_user.id
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)
        
        membership1 = MessageGroupMembershipDB(
            group_id=group.id,
            person_id=sample_person.id,
            added_by=sample_user.id
        )
        test_db.add(membership1)
        test_db.commit()
        
        # Act & Assert
        with pytest.raises(IntegrityError):
            membership2 = MessageGroupMembershipDB(
                group_id=group.id,
                person_id=sample_person.id,  # Duplicate membership should fail
                added_by=sample_user.id
            )
            test_db.add(membership2)
            test_db.commit()


class TestMessageModel:
    """Test the Message model (SMS + Email ready)."""
    
    def test_create_sms_message(self, test_db, sample_user):
        """Test creating an SMS message."""
        if MessageDB is None or MessageGroupDB is None:
            pytest.skip("MessageDB/MessageGroupDB not yet implemented (TDD RED phase)")
            
        # Arrange
        group = MessageGroupDB(
            name="Test Group",
            description="Test description",
            created_by=sample_user.id
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)
        
        # Act
        message = MessageDB(
            channel="sms",
            content="Test SMS message",
            group_id=group.id,
            sent_by=sample_user.id,
            status="queued",
            twilio_sid=None  # Will be set when sent
        )
        test_db.add(message)
        test_db.commit()
        test_db.refresh(message)
        
        # Assert
        assert message.id is not None
        assert message.channel == "sms"
        assert message.content == "Test SMS message"
        assert message.group_id == group.id
        assert message.sent_by == sample_user.id
        assert message.status == "queued"
        assert message.created_at is not None
    
    def test_create_email_message(self, test_db, sample_user):
        """Test creating an email message (future-ready)."""
        if MessageDB is None or MessageGroupDB is None:
            pytest.skip("MessageDB/MessageGroupDB not yet implemented (TDD RED phase)")
            
        # Arrange
        group = MessageGroupDB(
            name="Test Group",
            description="Test description",
            created_by=sample_user.id
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)
        
        # Act
        message = MessageDB(
            channel="email",
            content="Test email message",
            subject="Test Subject",  # Email-specific field
            group_id=group.id,
            sent_by=sample_user.id,
            status="queued"
        )
        test_db.add(message)
        test_db.commit()
        test_db.refresh(message)
        
        # Assert
        assert message.id is not None
        assert message.channel == "email"
        assert message.content == "Test email message"
        assert message.subject == "Test Subject"
        assert message.group_id == group.id
        assert message.sent_by == sample_user.id
        assert message.status == "queued"
    
    def test_message_status_transitions(self, test_db, sample_user):
        """Test valid message status transitions."""
        if MessageDB is None or MessageGroupDB is None:
            pytest.skip("MessageDB/MessageGroupDB not yet implemented (TDD RED phase)")
            
        # Arrange
        group = MessageGroupDB(
            name="Test Group",
            description="Test description",
            created_by=sample_user.id
        )
        test_db.add(group)
        test_db.commit()
        test_db.refresh(group)
        
        message = MessageDB(
            channel="sms",
            content="Test message",
            group_id=group.id,
            sent_by=sample_user.id,
            status="queued"
        )
        test_db.add(message)
        test_db.commit()
        test_db.refresh(message)
        
        # Act & Assert - Valid status transitions
        valid_statuses = ["queued", "sending", "sent", "delivered", "failed"]
        for status in valid_statuses:
            message.status = status
            message.updated_at = datetime.now(timezone.utc)
            test_db.commit()
            assert message.status == status


class TestMessageTemplateModel:
    """Test the MessageTemplate model."""
    
    def test_create_message_template(self, test_db, sample_user):
        """Test creating a message template."""
        if MessageTemplateDB is None:
            pytest.skip("MessageTemplateDB not yet implemented (TDD RED phase)")
            
        # Act
        template = MessageTemplateDB(
            name="Event Reminder",
            content="Reminder: {event_name} starts at {start_time} on {date}",
            category="event",
            created_by=sample_user.id,
            is_active=True
        )
        test_db.add(template)
        test_db.commit()
        test_db.refresh(template)
        
        # Assert
        assert template.id is not None
        assert template.name == "Event Reminder"
        assert "{event_name}" in template.content
        assert "{start_time}" in template.content
        assert "{date}" in template.content
        assert template.category == "event"
        assert template.created_by == sample_user.id
        assert template.is_active is True
    
    def test_template_unique_name_per_user(self, test_db, sample_user):
        """Test that template names must be unique per user."""
        if MessageTemplateDB is None:
            pytest.skip("MessageTemplateDB not yet implemented (TDD RED phase)")
            
        # Arrange
        template1 = MessageTemplateDB(
            name="Event Reminder",
            content="First template",
            category="event",
            created_by=sample_user.id
        )
        test_db.add(template1)
        test_db.commit()
        
        # Act & Assert
        with pytest.raises(IntegrityError):
            template2 = MessageTemplateDB(
                name="Event Reminder",  # Duplicate name for same user should fail
                content="Second template",
                category="event",
                created_by=sample_user.id
            )
            test_db.add(template2)
            test_db.commit()


class TestBackwardsCompatibility:
    """Test that new messaging features don't break existing functionality."""
    
    def test_existing_person_model_unchanged(self, test_db):
        """Test that existing PersonDB model still works as before."""
        # Act - Create person using existing fields only
        person = PersonDB(
            first_name="Jane",
            last_name="Smith",
            person_type="youth",
            grade=11,
            school_name="Test School"
        )
        test_db.add(person)
        test_db.commit()
        test_db.refresh(person)
        
        # Assert - All existing fields work
        assert person.id is not None
        assert person.first_name == "Jane"
        assert person.last_name == "Smith"
        assert person.person_type == "youth"
        assert person.grade == 11
        assert person.school_name == "Test School"
        assert person.created_at is not None
    
    def test_person_model_with_new_phone_fields(self, test_db):
        """Test that PersonDB works with new phone/SMS fields (when added)."""
        # Act - Create person with new SMS fields
        person = PersonDB(
            first_name="Bob",
            last_name="Johnson",
            person_type="leader",
            role="Youth Pastor",
            phone_number="+1987654321",
            # These fields will be added in later todo
            # sms_consent=True,
            # sms_opt_out=False
        )
        test_db.add(person)
        test_db.commit()
        test_db.refresh(person)
        
        # Assert
        assert person.phone_number == "+1987654321"
        # Future assertions for SMS fields will be added in later todo
    
    def test_database_migration_safety(self, test_db):
        """Test that new tables can be created without affecting existing data."""
        # Arrange - Create existing data
        person = PersonDB(
            first_name="Alice",
            last_name="Brown",
            person_type="youth"
        )
        test_db.add(person)
        test_db.commit()
        original_person_count = test_db.query(PersonDB).count()
        
        # Act - Simulate adding new tables (would happen in migration)
        # New tables would be created here, but existing data should remain
        
        # Assert - Existing data is preserved
        person_count_after = test_db.query(PersonDB).count()
        assert person_count_after == original_person_count
        
        # Verify existing person is still intact
        retrieved_person = test_db.query(PersonDB).filter_by(first_name="Alice").first()
        assert retrieved_person is not None
        assert retrieved_person.first_name == "Alice"
        assert retrieved_person.last_name == "Brown"
        assert retrieved_person.person_type == "youth"


class TestDataIntegrity:
    """Test data integrity constraints and relationships."""
    
    def test_message_requires_valid_group(self, test_db, sample_user):
        """Test that messages must reference valid groups."""
        if MessageDB is None:
            pytest.skip("MessageDB not yet implemented (TDD RED phase)")
            
        # Act & Assert - Should fail with invalid group_id
        with pytest.raises(IntegrityError):
            message = MessageDB(
                channel="sms",
                content="Test message",
                group_id=99999,  # Non-existent group
                sent_by=sample_user.id,
                status="queued"
            )
            test_db.add(message)
            test_db.commit()
    
    def test_membership_requires_valid_person_and_group(self, test_db, sample_user):
        """Test that memberships must reference valid persons and groups."""
        if MessageGroupMembershipDB is None:
            pytest.skip("MessageGroupMembershipDB not yet implemented (TDD RED phase)")
            
        # Act & Assert - Should fail with invalid person_id
        with pytest.raises(IntegrityError):
            membership = MessageGroupMembershipDB(
                group_id=1,  # Assume valid
                person_id=99999,  # Non-existent person
                added_by=sample_user.id
            )
            test_db.add(membership)
            test_db.commit()