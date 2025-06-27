from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: str = Field(..., description="Unique conversation identifier")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI agent response")
    booking_confirmed: bool = Field(default=False, description="Whether a booking was confirmed")
    booking_details: Dict[str, Any] = Field(default_factory=dict, description="Booking details if confirmed")
    conversation_id: str = Field(..., description="Conversation identifier")

class BookingRequest(BaseModel):
    date: str = Field(..., description="Booking date in YYYY-MM-DD format")
    time: str = Field(..., description="Booking time in HH:MM format")
    duration: int = Field(default=30, description="Duration in minutes")
    title: Optional[str] = Field(default="Meeting", description="Meeting title")
    description: Optional[str] = Field(default=None, description="Meeting description")

class TimeSlot(BaseModel):
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    available: bool = Field(..., description="Whether the slot is available")

class ConversationState(BaseModel):
    conversation_id: str
    current_node: str = "start"
    user_intent: Optional[str] = None
    extracted_info: Dict[str, Any] = Field(default_factory=dict)
    pending_confirmation: Optional[BookingRequest] = None
    last_response: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
