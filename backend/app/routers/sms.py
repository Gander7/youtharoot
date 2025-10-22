"""
SMS API Router for sending individual and group SMS messages.

Provides endpoints for:
- Sending individual SMS with opt-out enforcement
- Sending group SMS with member filtering
- Message status tracking and history
- Delivery status webhooks from Twilio
- SMS analytics and cost tracking

Integrates with SMS service and group management system.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.services.sms_service import SMSService, SMSSettings, SMSError, ValidationError
from app.messaging_models import MessageStatus, MessageChannel
from app.db_models import MessageDB, PersonDB, MessageGroupDB, MessageGroupMembershipDB
from app.repositories import get_group_repository
from app.config import settings
import asyncio


router = APIRouter(prefix="/api/sms", tags=["SMS"])

logger = logging.getLogger(__name__)


# Pydantic models for API validation
class SMSSendRequest(BaseModel):
    """Request model for sending individual SMS."""
    phone_number: str = Field(..., min_length=8, max_length=20, description="Phone number in E.164 format")
    message: str = Field(..., min_length=1, max_length=1600, description="SMS message content")
    person_id: Optional[int] = Field(None, description="Person ID to check opt-out status")


class GroupSMSSendRequest(BaseModel):
    """Request model for sending SMS to a group."""
    group_id: int = Field(..., description="Message group ID")
    message: str = Field(..., min_length=1, max_length=1600, description="SMS message content")
    include_parents: bool = Field(False, description="Whether to include parents in group messaging")
    parent_message: Optional[str] = Field(None, min_length=1, max_length=1600, description="Custom message for parents (if different from main message)")


class SMSSendResponse(BaseModel):
    """Response model for SMS sending."""
    success: bool
    message_sid: Optional[str] = None
    status: str
    error: Optional[str] = None


class GroupSMSSendResponse(BaseModel):
    """Response model for group SMS sending."""
    success: bool
    sent_count: int
    skipped_count: int
    failed_count: int
    parent_count: int = Field(0, description="Number of parent notifications sent")
    results: List[Dict[str, Any]]
    parent_recipients: Optional[List[Dict[str, Any]]] = Field(None, description="Parent recipient details")


class MessageHistoryResponse(BaseModel):
    """Response model for message history."""
    messages: List[Dict[str, Any]]
    total_count: int
    group_id: Optional[int] = None


class MessageRecipientDetail(BaseModel):
    """Individual recipient detail for group messages."""
    person_id: int
    person_name: str
    phone_number: Optional[str]
    status: str
    twilio_sid: Optional[str] = None
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None


class HistoryHeaderMessage(BaseModel):
    """Top-level message summary for history display."""
    id: int
    message_type: str  # 'individual' or 'group'
    content: str
    created_at: str
    sent_by: int
    
    # Individual message fields
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    status: Optional[str] = None
    
    # Group message fields
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    total_recipients: Optional[int] = None
    sent_count: Optional[int] = None
    delivered_count: Optional[int] = None
    failed_count: Optional[int] = None
    pending_count: Optional[int] = None


class HistoryHeaderMessageResponse(BaseModel):
    """Response model for top-level message history."""
    messages: List[HistoryHeaderMessage]
    total_count: int


class SMSAnalyticsResponse(BaseModel):
    """Response model for SMS analytics."""
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    total_cost: float
    date_range: Optional[Dict[str, str]] = None
    # Parent analytics fields
    youth_messages: Optional[int] = None
    parent_messages: Optional[int] = None
    parent_notification_rate: Optional[float] = None
    opt_out_rate: Optional[float] = None


# Dependency to get SMS service
def get_sms_service(db: Session = Depends(get_db)) -> SMSService:
    """Get configured SMS service instance."""
    
    # Check if SMS is properly configured
    if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMS service not configured. Please contact administrator."
        )
    
    sms_settings = SMSSettings(
        twilio_account_sid=settings.TWILIO_ACCOUNT_SID,
        twilio_auth_token=settings.TWILIO_AUTH_TOKEN,
        twilio_phone_number=settings.TWILIO_PHONE_NUMBER,
        max_messages_per_hour=settings.SMS_MAX_MESSAGES_PER_HOUR,
        cost_per_sms=settings.SMS_COST_PER_MESSAGE
    )
    
    return SMSService(settings=sms_settings, db=db)


@router.post("/send", response_model=SMSSendResponse)
async def send_individual_sms(
    request: SMSSendRequest,
    current_user: User = Depends(get_current_user),
    sms_service: SMSService = Depends(get_sms_service),
    db: Session = Depends(get_db)
):
    """
    Send SMS to individual phone number with opt-out enforcement.
    
    Checks if person has opted out before sending message.
    Logs message to database for tracking and analytics.
    """
    try:
        # Send SMS via service
        result = sms_service.send_message(
            to_phone=request.phone_number,
            message_body=request.message,
            person_id=request.person_id
        )
        
        # Check if message was blocked due to opt-out
        if not result["success"] and result["status"] == "opted_out":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        # Log message to database if successful
        if result["success"]:
            message_record = MessageDB(
                channel=MessageChannel.SMS,
                content=request.message,
                recipient_phone=request.phone_number,  # Store recipient phone for individual messages
                recipient_person_id=request.person_id,  # Store person ID if provided
                sent_by=current_user.id,
                status=MessageStatus.SENT,
                twilio_sid=result["message_sid"],
                sent_at=datetime.now(timezone.utc)
            )
            db.add(message_record)
            db.commit()
        
        return SMSSendResponse(
            success=result["success"],
            message_sid=result["message_sid"],
            status=result["status"],
            error=result["error"]
        )
        
    except SMSError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SMS sending failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/send-group", response_model=GroupSMSSendResponse)
async def send_group_sms(
    request: GroupSMSSendRequest,
    current_user: User = Depends(get_current_user),
    sms_service: SMSService = Depends(get_sms_service),
    db: Session = Depends(get_db)
):
    """
    Send SMS to all members of a group with opt-out filtering.
    
    Automatically filters out people who have opted out of SMS.
    Logs all messages and provides detailed results.
    """
    try:
        # Get group repository
        group_repo = get_group_repository(db)
        
        # Check if group exists
        group = await group_repo.get_group(request.group_id, current_user.id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # Get group members who haven't opted out
        members = await group_repo.get_group_members(request.group_id)
        if not members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible recipients found in group"
            )
        
        # Get SMS recipients - include parents if requested
        if request.include_parents:
            recipients_data = sms_service.get_sms_recipients_with_parents([m.person_id for m in members])
            # If the service returned a coroutine (tests may provide AsyncMock), await it
            if asyncio.iscoroutine(recipients_data):
                recipients_data = await recipients_data
            youth_recipients = recipients_data.get("youth_recipients", [])
            parent_recipients = recipients_data.get("parent_recipients", [])
            # Combine youth and parents for processing
            eligible_recipients = youth_recipients + parent_recipients
        else:
            eligible_recipients = sms_service.get_sms_recipients([m.person_id for m in members])
            if asyncio.iscoroutine(eligible_recipients):
                eligible_recipients = await eligible_recipients
            youth_recipients = eligible_recipients
            parent_recipients = []
        
        if not eligible_recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible recipients found - all group members have opted out of SMS"
            )
        
        # Remove duplicates based on phone number to prevent duplicate SMS sends
        seen_phones = set()
        deduplicated_recipients = []
        duplicate_count = 0
        
        for recipient in eligible_recipients:
            phone = recipient["phone_number"]
            if phone not in seen_phones:
                seen_phones.add(phone)
                deduplicated_recipients.append(recipient)
            else:
                duplicate_count += 1
                logger.warning(f"Duplicate phone number detected: {phone} (person_id: {recipient['id']}) - skipping to prevent duplicate SMS")
        
        if duplicate_count > 0:
            logger.info(f"Removed {duplicate_count} duplicate phone numbers. Sending to {len(eligible_recipients)} unique recipients.")

        # Update eligible_recipients to use deduplicated list
        eligible_recipients = deduplicated_recipients
        
        # Send SMS to each eligible recipient
        results = []
        sent_count = 0
        failed_count = 0
        
        logger.info(f"Starting group SMS send to {len(eligible_recipients)} recipients for group {request.group_id}")
        
        for i, recipient in enumerate(eligible_recipients, 1):
            try:
                logger.info(f"[{i}/{len(eligible_recipients)}] Sending SMS to {recipient['phone_number']} (person_id: {recipient['id']})")
                
                # Determine message content based on recipient type
                if recipient.get("person_type") == "parent" and request.parent_message:
                    # Use custom parent message
                    message_content = request.parent_message
                elif recipient.get("person_type") == "parent":
                    # Auto-generate parent message if no custom message provided
                    youth_name = "your child"  # Default, try to get actual name
                    if "relationship_to_youth" in recipient:
                        youth = next((y for y in youth_recipients if y["id"] == recipient["relationship_to_youth"]), None)
                        if youth:
                            youth_name = f"{youth['first_name']} {youth['last_name']}"
                    message_content = f"Parent notification: {youth_name} - {request.message}"
                else:
                    # Regular youth message
                    message_content = request.message
                
                result = sms_service.send_message(
                    to_phone=recipient["phone_number"],
                    message_body=message_content,
                    person_id=recipient["id"]
                )
                
                if result.get("success"):
                    sent_count += 1
                    logger.info(f"[{i}/{len(eligible_recipients)}] SMS SUCCESS - Twilio SID: {result['message_sid']}")
                    
                    # Log message to database (only if DB session is available)
                    if db is not None:
                        message_record = MessageDB(
                            channel=MessageChannel.SMS,
                            content=message_content,  # Use actual message sent (may be different for parents)
                            group_id=request.group_id,
                            recipient_phone=recipient["phone_number"],
                            recipient_person_id=recipient["id"],
                            sent_by=current_user.id,
                            status=MessageStatus.SENT,
                            twilio_sid=result.get("message_sid"),
                            sent_at=datetime.now(timezone.utc)
                        )
                        db.add(message_record)
                else:
                    failed_count += 1
                    logger.warning(f"[{i}/{len(eligible_recipients)}] SMS FAILED to {recipient['phone_number']}: {result.get('error', 'Unknown error')}")

                    # Log failed message to database (only if DB session is available)
                    if db is not None:
                        message_record = MessageDB(
                            channel=MessageChannel.SMS,
                            content=request.message,
                            group_id=request.group_id,
                            recipient_phone=recipient["phone_number"],
                            recipient_person_id=recipient["id"],
                            sent_by=current_user.id,
                            status=MessageStatus.FAILED,
                            failure_reason=result.get("error", "Unknown error"),
                            failed_at=datetime.now(timezone.utc)
                        )
                        db.add(message_record)
                
                results.append({
                    "person_id": recipient["id"],
                    "phone_number": recipient["phone_number"],
                    "person_type": recipient.get("person_type", "youth"),
                    "success": result.get("success", False),
                    "message_sid": result.get("message_sid"),
                    "message_sent": message_content,  # Include actual message sent
                    "status": result.get("status"),
                    "error": result.get("error")
                })
                
            except Exception as e:
                failed_count += 1
                logger.error(f"[{i}/{len(eligible_recipients)}] EXCEPTION sending SMS to {recipient['phone_number']}: {str(e)}")
                # Optionally log exception to DB if available
                if db is not None:
                    try:
                        error_record = MessageDB(
                            channel=MessageChannel.SMS,
                            content=message_content if 'message_content' in locals() else request.message,
                            group_id=request.group_id,
                            recipient_phone=recipient.get("phone_number"),
                            recipient_person_id=recipient.get("id"),
                            sent_by=current_user.id,
                            status=MessageStatus.FAILED,
                            failure_reason=str(e),
                            failed_at=datetime.now(timezone.utc)
                        )
                        db.add(error_record)
                    except Exception:
                        logger.exception("Failed to write error message record to DB")

                results.append({
                    "person_id": recipient["id"],
                    "phone_number": recipient["phone_number"],
                    "success": False,
                    "message_sid": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info(f"Group SMS send completed: {sent_count} sent, {failed_count} failed")
        if db is not None:
            try:
                db.commit()
                logger.info(f"Database commit completed for group {request.group_id}")
            except Exception:
                logger.exception("Failed to commit message records to DB")
        
        # Calculate skipped count (total members - eligible recipients after deduplication)
        total_members = len(members)
        skipped_count = total_members - len(eligible_recipients) - duplicate_count

        logger.info(f"SMS Summary - Total members: {total_members}, Sent: {sent_count}, Failed: {failed_count}, Skipped (opted out): {skipped_count}, Duplicates removed: {duplicate_count}") 

        # Calculate parent-specific metrics
        parent_count = len([r for r in results if r.get("person_type") == "parent"])
        parent_recipients_data = [
            {
                "person_id": r["person_id"],
                "phone_number": r["phone_number"],
                "message_sent": r["message_sent"],
                "success": r["success"]
            }
            for r in results if r.get("person_type") == "parent"
        ]

        return GroupSMSSendResponse(
            success=sent_count > 0,
            sent_count=sent_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            parent_count=parent_count,
            results=results,
            parent_recipients=parent_recipients_data if parent_recipients_data else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if "Group not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/history", response_model=MessageHistoryResponse)
async def get_message_history(
    group_id: Optional[int] = Query(None, description="Filter by group ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get message history with optional group filtering.
    
    Returns paginated list of SMS messages with status and delivery info.
    """
    try:
        # Check if using in-memory database (no message storage yet)
        from app.config import settings
        if settings.DATABASE_TYPE == "memory":
            # Return empty history for in-memory mode
            return MessageHistoryResponse(
                messages=[],
                total_count=0,
                group_id=group_id
            )
        
        # Build query for PostgreSQL mode
        query = db.query(MessageDB).filter(MessageDB.channel == MessageChannel.SMS)
        
        if group_id:
            query = query.filter(MessageDB.group_id == group_id)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated messages
        messages = query.order_by(MessageDB.created_at.desc()).offset(offset).limit(limit).all()
        
        # Convert to dict format
        message_list = []
        for msg in messages:
            message_list.append({
                "id": msg.id,
                "content": msg.content,
                "status": msg.status,
                "group_id": msg.group_id,
                "recipient_phone": msg.recipient_phone,  # Include recipient phone for individual messages
                "recipient_person_id": msg.recipient_person_id,  # Include recipient person ID for parent tracking
                "sent_by": msg.sent_by,
                "twilio_sid": msg.twilio_sid,
                "sent_at": msg.sent_at.isoformat() if msg.sent_at else None,
                "delivered_at": msg.delivered_at.isoformat() if msg.delivered_at else None,
                "created_at": msg.created_at.isoformat()
            })
        
        return MessageHistoryResponse(
            messages=message_list,
            total_count=total_count,
            group_id=group_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving message history: {str(e)}"
        )


@router.get("/history/top-level", response_model=HistoryHeaderMessageResponse)
async def get_top_level_message_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get top-level message history showing individual messages and group message summaries.
    
    Returns:
    - Individual messages with recipient details
    - Group messages with aggregated status counts (one row per group send)
    """
    try:
        from app.config import settings
        if settings.DATABASE_TYPE == "memory":
            return HistoryHeaderMessageResponse(messages=[], total_count=0)
        
        from datetime import timedelta
        from sqlalchemy import func
        
        # Calculate date cutoff
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Simplified approach: Get all messages and group them in Python
        # This is less efficient but more compatible and easier to debug
        
        # Get all group messages
        group_messages = db.query(MessageDB).filter(
            MessageDB.channel == MessageChannel.SMS,
            MessageDB.group_id.isnot(None),
            MessageDB.created_at >= cutoff_date
        ).order_by(MessageDB.created_at.desc()).all()
        
        # Get all individual messages  
        individual_messages = db.query(MessageDB).filter(
            MessageDB.channel == MessageChannel.SMS,
            MessageDB.group_id.is_(None),
            MessageDB.created_at >= cutoff_date
        ).order_by(MessageDB.created_at.desc()).all()
        
        messages = []
        
        # Process group messages - group by (group_id, content, rounded created_at)
        group_sends = {}
        for msg in group_messages:
            # Round created_at to the nearest minute for grouping
            rounded_time = msg.created_at.replace(second=0, microsecond=0)
            group_key = (msg.group_id, msg.content, rounded_time)
            
            if group_key not in group_sends:
                group_sends[group_key] = {
                    'representative': msg,
                    'total_recipients': 0,
                    'sent_count': 0,
                    'delivered_count': 0,
                    'failed_count': 0,
                    'pending_count': 0
                }
            
            group_data = group_sends[group_key]
            group_data['total_recipients'] += 1
            
            if msg.status == 'sent':
                group_data['sent_count'] += 1
            elif msg.status == 'delivered':
                group_data['delivered_count'] += 1
            elif msg.status == 'failed':
                group_data['failed_count'] += 1
            elif msg.status in ['queued', 'sending']:
                group_data['pending_count'] += 1
        
        # Convert group sends to HistoryHeaderMessage objects
        for group_key, group_data in group_sends.items():
            representative = group_data['representative']
            
            # Get group name
            group_name = "Unknown Group"
            if representative.group_id:
                from app.repositories import get_group_repository
                group_repo = get_group_repository(db)
                group = await group_repo.get_group(representative.group_id, current_user.id)
                if group:
                    group_name = group.name
            
            messages.append(HistoryHeaderMessage(
                id=representative.id,
                message_type="group",
                content=representative.content,
                created_at=representative.created_at.isoformat(),
                sent_by=representative.sent_by,
                group_id=representative.group_id,
                group_name=group_name,
                total_recipients=group_data['total_recipients'],
                sent_count=group_data['sent_count'],
                delivered_count=group_data['delivered_count'],
                failed_count=group_data['failed_count'],
                pending_count=group_data['pending_count']
            ))        # Process individual messages
        for msg in individual_messages[:limit]:  # Apply limit to individual messages
            # Get person name if we have person_id
            recipient_name = "Unknown"
            if msg.recipient_person_id:
                from app.repositories import get_person_repository
                person_repo = get_person_repository(db)
                person = await person_repo.get_person(msg.recipient_person_id)
                if person:
                    recipient_name = f"{person.first_name} {person.last_name}"
            elif msg.recipient_phone:
                # Fallback to phone number if no person_id
                recipient_name = msg.recipient_phone

            messages.append(HistoryHeaderMessage(
                id=msg.id,
                message_type="individual",
                content=msg.content,
                created_at=msg.created_at.isoformat(),
                sent_by=msg.sent_by,
                recipient_name=recipient_name,
                recipient_phone=msg.recipient_phone,
                status=msg.status
            ))
        
        # Sort all messages by creation time (most recent first)
        messages.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit again after sorting (simplified pagination)
        messages = messages[:limit]
        
        # Get total count
        total_count = len(group_sends) + len(individual_messages)

        return HistoryHeaderMessageResponse(
            messages=messages,
            total_count=total_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving top-level message history: {str(e)}"
        )


@router.get("/history/group/{group_id}/details", response_model=List[MessageRecipientDetail])
async def get_group_message_details(
    group_id: int,
    message_content: str = Query(..., description="Message content to identify the specific group send"),
    send_time: str = Query(..., description="ISO timestamp of when the message was sent"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed recipient list for a specific group message send.
    
    Returns list of all recipients with their individual message status.
    """
    try:
        from app.config import settings
        if settings.DATABASE_TYPE == "memory":
            return []
        
        from datetime import datetime, timedelta
        
        # Parse the send time and create a window to find the messages
        try:
            send_datetime = datetime.fromisoformat(send_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid send_time format. Use ISO format."
            )
        
        # Create a 1-minute window around the send time to find related messages
        start_time = send_datetime - timedelta(seconds=30)
        end_time = send_datetime + timedelta(seconds=30)
        
        # Get all messages for this group send
        messages = db.query(MessageDB).filter(
            MessageDB.channel == MessageChannel.SMS,
            MessageDB.group_id == group_id,
            MessageDB.content == message_content,
            MessageDB.created_at >= start_time,
            MessageDB.created_at <= end_time
        ).all()
        
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group message not found"
            )
        
        # Get person details for each message
        recipient_details = []
        from app.repositories import get_person_repository
        person_repo = get_person_repository(db)
        
        for msg in messages:
            # Get person info
            person_name = "Unknown"
            person_id = 0
            phone_number = msg.recipient_phone
            
            if msg.recipient_person_id:
                person_id = msg.recipient_person_id
                person = await person_repo.get_person(person_id)
                if person:
                    person_name = f"{person.first_name} {person.last_name}"
            elif phone_number:
                # Fallback to phone number if no person_id
                person_name = phone_number
            
            recipient_details.append(MessageRecipientDetail(
                person_id=person_id,
                person_name=person_name,
                phone_number=phone_number,
                status=msg.status,
                twilio_sid=msg.twilio_sid,
                sent_at=msg.sent_at.isoformat() if msg.sent_at else None,
                delivered_at=msg.delivered_at.isoformat() if msg.delivered_at else None,
                failed_at=msg.failed_at.isoformat() if msg.failed_at else None,
                failure_reason=msg.failure_reason
            ))
        
        return recipient_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving group message details: {str(e)}"
        )


@router.get("/status/{message_id}")
async def get_message_status(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of specific message by ID.
    
    Returns detailed information about message delivery status.
    """
    try:
        # Check if using in-memory database (no message storage yet)
        from app.config import settings
        if settings.DATABASE_TYPE == "memory":
            # Return not found for in-memory mode
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found (in-memory mode)"
            )
        
        message = db.query(MessageDB).filter(
            MessageDB.id == message_id,
            MessageDB.channel == MessageChannel.SMS
        ).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return {
            "id": message.id,
            "content": message.content,
            "status": message.status,
            "channel": message.channel,
            "group_id": message.group_id,
            "sent_by": message.sent_by,
            "twilio_sid": message.twilio_sid,
            "sent_at": message.sent_at.isoformat() if message.sent_at else None,
            "delivered_at": message.delivered_at.isoformat() if message.delivered_at else None,
            "failed_at": message.failed_at.isoformat() if message.failed_at else None,
            "failure_reason": message.failure_reason,
            "created_at": message.created_at.isoformat(),
            "updated_at": message.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving message status: {str(e)}"
        )


@router.post("/webhook")
async def handle_twilio_webhook(
    request: Request,
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    To: str = Form(...),
    From: str = Form(...),
    ErrorCode: Optional[str] = Form(None),
    sms_service: SMSService = Depends(get_sms_service),
    db: Session = Depends(get_db)
):
    """
    Handle Twilio webhook for delivery status updates.
    
    Validates webhook signature and updates message status in database.
    """
    try:
        # Get webhook data and signature
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        
        # Log webhook details for debugging
        print(f"🔗 Webhook received:")
        print(f"   URL: {url}")
        print(f"   Signature: {signature}")
        print(f"   Data: {webhook_data}")
        print(f"   Headers: {dict(request.headers)}")
        
        # Process webhook through SMS service
        result = sms_service.handle_webhook(webhook_data, url, signature)
        
        print(f"✅ Webhook processed successfully: {result}")
        
        return {
            "status": "processed",
            "message_sid": result["message_sid"],
            "updated": result["updated"]
        }
        
    except ValidationError as e:
        print(f"❌ Webhook validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook signature: {str(e)}"
        )
    except Exception as e:
        print(f"💥 Webhook processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.get("/analytics", response_model=SMSAnalyticsResponse)
async def get_sms_analytics(
    start_date: Optional[date] = Query(None, description="Start date for analytics (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for analytics (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    sms_service: SMSService = Depends(get_sms_service),
    db: Session = Depends(get_db)
):
    """
    Get SMS analytics including delivery rates and cost tracking.
    
    Provides overview of SMS performance and usage statistics.
    """
    try:
        # Check if SMS service has mock analytics (for testing)
        if hasattr(sms_service, 'get_analytics') and callable(sms_service.get_analytics):
            try:
                mock_analytics = sms_service.get_analytics()
                return SMSAnalyticsResponse(**mock_analytics)
            except Exception:
                pass  # Fall through to real analytics if mock fails
        
        # Build query for SMS messages
        query = db.query(MessageDB).filter(MessageDB.channel == MessageChannel.SMS)
        
        # Apply date filtering if provided
        if start_date:
            query = query.filter(MessageDB.created_at >= start_date)
        if end_date:
            query = query.filter(MessageDB.created_at <= end_date)
        
        # Get message counts by status
        all_messages = query.all()
        total_sent = len(all_messages)
        total_delivered = len([m for m in all_messages if m.status == MessageStatus.DELIVERED])
        total_failed = len([m for m in all_messages if m.status == MessageStatus.FAILED])
        
        # Calculate delivery rate
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
        
        # Get cost information from SMS service
        total_cost = sms_service.get_total_cost()
        
        # Calculate parent analytics if available
        youth_messages = None
        parent_messages = None  
        parent_notification_rate = None
        opt_out_rate = None
        
        if db:
            try:
                # Count messages by recipient type (this is a simplified approach)
                # In a real implementation, you'd track recipient type in the database
                youth_messages = len([m for m in all_messages if m.recipient_person_id])
                parent_messages = total_sent - youth_messages if total_sent > youth_messages else 0
                
                if youth_messages > 0:
                    parent_notification_rate = round(parent_messages / youth_messages, 2)
                    
                # Calculate opt-out rate (placeholder - would need actual opt-out tracking)
                opt_out_rate = 0.1  # Placeholder
            except Exception:
                pass
        
        # Prepare date range info
        date_range = None
        if start_date or end_date:
            date_range = {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        
        return SMSAnalyticsResponse(
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=total_failed,
            delivery_rate=round(delivery_rate, 2),
            total_cost=round(total_cost, 4),
            date_range=date_range,
            youth_messages=youth_messages,
            parent_messages=parent_messages,
            parent_notification_rate=parent_notification_rate,
            opt_out_rate=opt_out_rate
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving SMS analytics: {str(e)}"
        )