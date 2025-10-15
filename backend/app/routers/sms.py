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

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.services.sms_service import SMSService, SMSSettings, SMSError, ValidationError
from app.messaging_models import MessageStatus, MessageChannel
from app.db_models import MessageDB, PersonDB, MessageGroupDB, MessageGroupMembershipDB
from app.repositories import get_group_repository
from app.config import settings


router = APIRouter(prefix="/api/sms", tags=["SMS"])


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
    results: List[Dict[str, Any]]


class MessageHistoryResponse(BaseModel):
    """Response model for message history."""
    messages: List[Dict[str, Any]]
    total_count: int
    group_id: Optional[int] = None


class SMSAnalyticsResponse(BaseModel):
    """Response model for SMS analytics."""
    total_sent: int
    total_delivered: int
    total_failed: int
    delivery_rate: float
    total_cost: float
    date_range: Optional[Dict[str, str]] = None


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
        if result["success"] and request.person_id:
            message_record = MessageDB(
                channel=MessageChannel.SMS,
                content=request.message,
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
        group = group_repo.get_group(request.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # Get group members who haven't opted out
        members = group_repo.get_group_members(request.group_id)
        if not members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible recipients found in group"
            )
        
        # Get SMS recipients (filters opted-out users)
        eligible_recipients = sms_service.get_sms_recipients([m.person_id for m in members])
        
        if not eligible_recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible recipients found - all group members have opted out of SMS"
            )
        
        # Send SMS to each eligible recipient
        results = []
        sent_count = 0
        failed_count = 0
        
        for recipient in eligible_recipients:
            try:
                result = sms_service.send_message(
                    to_phone=recipient["phone_number"],
                    message_body=request.message,
                    person_id=recipient["id"]
                )
                
                if result["success"]:
                    sent_count += 1
                    
                    # Log message to database
                    message_record = MessageDB(
                        channel=MessageChannel.SMS,
                        content=request.message,
                        group_id=request.group_id,
                        sent_by=current_user.id,
                        status=MessageStatus.SENT,
                        twilio_sid=result["message_sid"],
                        sent_at=datetime.now(timezone.utc)
                    )
                    db.add(message_record)
                else:
                    failed_count += 1
                
                results.append({
                    "person_id": recipient["id"],
                    "phone_number": recipient["phone_number"],
                    "success": result["success"],
                    "message_sid": result["message_sid"],
                    "status": result["status"],
                    "error": result["error"]
                })
                
            except Exception as e:
                failed_count += 1
                results.append({
                    "person_id": recipient["id"],
                    "phone_number": recipient["phone_number"],
                    "success": False,
                    "message_sid": None,
                    "status": "failed",
                    "error": str(e)
                })
        
        db.commit()
        
        # Calculate skipped count (total members - eligible recipients)
        total_members = len(members)
        skipped_count = total_members - len(eligible_recipients)
        
        return GroupSMSSendResponse(
            success=sent_count > 0,
            sent_count=sent_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results
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
        
        # Process webhook through SMS service
        result = sms_service.handle_webhook(webhook_data, url, signature)
        
        return {
            "status": "processed",
            "message_sid": result["message_sid"],
            "updated": result["updated"]
        }
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook signature: {str(e)}"
        )
    except Exception as e:
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
            date_range=date_range
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving SMS analytics: {str(e)}"
        )