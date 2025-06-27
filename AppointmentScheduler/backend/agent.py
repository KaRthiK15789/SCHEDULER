import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from openai import OpenAI

from .calendar_service import calendar_service
from .conversation_graph import ConversationGraph
from .models import ConversationState, BookingRequest

logger = logging.getLogger(__name__)

class BookingAgent:
    """
    Main booking agent that handles conversation flow and booking logic
    """
    
    def __init__(self):
        # Initialize conversation graph
        self.conversation_graph = ConversationGraph()
        
        # Store conversation states
        self.conversations: Dict[str, ConversationState] = {}
    
    def get_current_time(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()
    
    async def process_message(self, message: str, conversation_id: str) -> Dict[str, Any]:
        """
        Process a user message and return appropriate response
        """
        try:
            # Get or create conversation state
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = ConversationState(
                    conversation_id=conversation_id
                )
            
            conversation = self.conversations[conversation_id]
            conversation.updated_at = datetime.now()
            
            # Analyze user intent and extract information
            intent_analysis = await self._analyze_intent(message, conversation)
            
            # Update conversation state with extracted information
            conversation.user_intent = intent_analysis.get("intent")
            if intent_analysis.get("extracted_info"):
                conversation.extracted_info.update(intent_analysis["extracted_info"])
            
            # Process through conversation graph
            response_data = await self.conversation_graph.process_node(
                conversation, message, intent_analysis
            )
            
            # Update conversation state
            conversation.current_node = response_data.get("next_node", conversation.current_node)
            conversation.last_response = response_data.get("response")
            
            # Handle booking confirmation if needed
            if response_data.get("action") == "confirm_booking":
                booking_result = await self._confirm_booking(conversation)
                if booking_result["success"]:
                    response_data["booking_confirmed"] = True
                    response_data["booking_details"] = booking_result["details"]
            elif response_data.get("action") == "booking_confirmed":
                response_data["booking_confirmed"] = True
                response_data["booking_details"] = response_data.get("booking_details", {})
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request. Please try again.",
                "booking_confirmed": False,
                "booking_details": {}
            }
    
    async def _analyze_intent(self, message: str, conversation: ConversationState) -> Dict[str, Any]:
        """
        Analyze user intent and extract relevant information using pattern matching
        """
        try:
            # Import datetime utils for date parsing
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from utils.datetime_utils import parse_relative_date, parse_time_expression
            
            message_lower = message.lower()
            
            # Try to parse date and time from the message
            parsed_date = parse_relative_date(message)
            parsed_time = parse_time_expression(message)
            
            # Determine intent based on keywords and context
            intent = "general_query"
            if any(word in message_lower for word in ["book", "schedule", "meeting", "appointment", "call"]):
                intent = "book_appointment"
            elif any(word in message_lower for word in ["available", "availability", "free", "open"]):
                intent = "check_availability"
            elif any(word in message_lower for word in ["cancel", "reschedule", "change"]):
                intent = "reschedule"
            elif any(word in message_lower for word in ["yes", "confirm", "ok", "sure", "works", "good", "fine", "perfect", "great"]):
                # Check if this is a confirmation in context
                if conversation.current_node == "confirm_booking" or conversation.pending_confirmation:
                    intent = "confirm"
                else:
                    intent = "book_appointment"
            elif any(word in message_lower for word in ["no", "not", "different", "another", "other"]):
                intent = "decline"
            
            # If we have extracted date/time info, it's likely a booking intent
            if (parsed_date or parsed_time) and intent == "general_query":
                intent = "book_appointment"
            
            # Determine time preference
            time_preference = "flexible"
            if parsed_time:
                time_preference = "specific"
            elif any(word in message_lower for word in ["morning"]):
                time_preference = "morning"
            elif any(word in message_lower for word in ["afternoon"]):
                time_preference = "afternoon"
            elif any(word in message_lower for word in ["evening"]):
                time_preference = "evening"
            
            # Determine date preference
            date_preference = "flexible"
            if parsed_date:
                date_preference = "specific"
            elif any(word in message_lower for word in ["tomorrow", "today", "monday", "tuesday", "wednesday", "thursday", "friday"]):
                date_preference = "relative"
            
            # Extract duration
            duration = 30
            if "30" in message or "thirty" in message_lower:
                duration = 30
            elif "60" in message or "hour" in message_lower:
                duration = 60
            elif "15" in message or "fifteen" in message_lower:
                duration = 15
            
            result = {
                "intent": intent,
                "confidence": 0.9,
                "extracted_info": {
                    "date": parsed_date,
                    "time": parsed_time,
                    "duration": duration,
                    "date_preference": date_preference,
                    "time_preference": time_preference,
                    "additional_context": f"Original message: {message}"
                }
            }
            
            logger.info(f"Intent analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {str(e)}")
            return {
                "intent": "general_query",
                "confidence": 0.5,
                "extracted_info": {}
            }
    
    async def get_availability(self, date: str) -> Dict[str, Any]:
        """
        Get availability for a specific date
        """
        try:
            slots = await calendar_service.get_availability(date)
            return {
                "date": date,
                "available_slots": [
                    {"start_time": slot.start_time, "end_time": slot.end_time}
                    for slot in slots
                ]
            }
        except Exception as e:
            logger.error(f"Error getting availability: {str(e)}")
            return {"date": date, "available_slots": []}
    
    async def _confirm_booking(self, conversation: ConversationState) -> Dict[str, Any]:
        """
        Confirm and create a booking
        """
        try:
            if not conversation.pending_confirmation:
                return {"success": False, "error": "No pending booking to confirm"}
            
            booking = conversation.pending_confirmation
            result = await calendar_service.book_appointment(booking)
            
            if result["success"]:
                return {
                    "success": True,
                    "details": {
                        "date": booking.date,
                        "time": booking.time,
                        "duration": booking.duration,
                        "title": booking.title
                    }
                }
            else:
                return {"success": False, "error": result.get("error", "Booking failed")}
                
        except Exception as e:
            logger.error(f"Error confirming booking: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def generate_response(self, conversation: ConversationState, 
                              context: Dict[str, Any]) -> str:
        """
        Generate a natural language response using template-based responses
        """
        try:
            # Generate responses based on conversation state and context
            node = conversation.current_node
            intent = conversation.user_intent
            extracted_info = conversation.extracted_info
            
            if node == "start":
                return "Hello! I'm your AI booking assistant. I can help you schedule appointments, check availability, and manage your calendar. What would you like to do today?"
            
            elif intent == "book_appointment":
                if extracted_info.get("date") and extracted_info.get("time"):
                    return f"I understand you'd like to book an appointment. Let me check what's available and get this scheduled for you."
                elif extracted_info.get("date"):
                    return f"Great! I see you want to schedule something. What time would work best for you?"
                else:
                    return "I'd be happy to help you schedule an appointment! What date would you prefer?"
            
            elif intent == "check_availability":
                if extracted_info.get("date"):
                    return f"Let me check what's available for you on that date."
                else:
                    return "I can check availability for you. What date are you interested in?"
            
            else:
                return "I'm here to help you with appointment scheduling. I can book new appointments, check availability, and find suitable time slots. What would you like to do?"
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm here to help you schedule appointments. What would you like to do?"
