from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from .models import ConversationState, BookingRequest
from .calendar_service import calendar_service

logger = logging.getLogger(__name__)

class ConversationGraph:
    """
    Manages conversation flow using a graph-based approach similar to LangGraph
    """
    
    def __init__(self):
        self.nodes = {
            "start": self._handle_start,
            "intent_booking": self._handle_intent_booking,
            "collect_date": self._handle_collect_date,
            "collect_time": self._handle_collect_time,
            "show_availability": self._handle_show_availability,
            "confirm_booking": self._handle_confirm_booking,
            "booking_complete": self._handle_booking_complete,
            "handle_query": self._handle_general_query
        }
    
    async def process_node(self, conversation: ConversationState, 
                          user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the current conversation node and determine next action
        """
        current_node = conversation.current_node
        
        # Route to appropriate handler based on intent and current state
        intent = intent_analysis.get("intent")
        
        if intent == "book_appointment":
            if current_node == "start":
                next_node = "intent_booking"
            elif current_node in ["collect_date", "collect_time", "show_availability"]:
                next_node = "intent_booking"
            else:
                next_node = "intent_booking"
        elif intent == "check_availability":
            next_node = "show_availability"
        elif intent == "confirm" or (current_node == "confirm_booking" and intent == "book_appointment"):
            next_node = "confirm_booking"
        elif intent == "decline":
            next_node = "collect_time"
        else:
            # If we have date/time info but general query, treat as booking
            extracted_info = intent_analysis.get("extracted_info", {})
            if extracted_info.get("date") or extracted_info.get("time"):
                next_node = "intent_booking"
            else:
                next_node = "handle_query"
        
        # Execute the node handler
        if next_node in self.nodes:
            return await self.nodes[next_node](conversation, user_message, intent_analysis)
        else:
            return await self.nodes["handle_query"](conversation, user_message, intent_analysis)
    
    async def _handle_start(self, conversation: ConversationState, 
                           user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle initial conversation start
        """
        return {
            "response": "Hello! I'm your AI booking assistant. I can help you schedule appointments, check availability, and manage your calendar. What would you like to do today?",
            "next_node": "intent_booking"
        }
    
    async def _handle_intent_booking(self, conversation: ConversationState, 
                                   user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle booking intent and collect missing information
        """
        extracted_info = intent_analysis.get("extracted_info", {})
        
        # Check what information we have
        has_date = extracted_info.get("date") or conversation.extracted_info.get("date")
        has_time = extracted_info.get("time") or conversation.extracted_info.get("time")
        
        if not has_date:
            return {
                "response": "I'd be happy to help you schedule an appointment! What date would you prefer? You can say something like 'tomorrow', 'next Friday', or give me a specific date.",
                "next_node": "collect_date"
            }
        elif not has_time:
            date_str = has_date
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d")
            except:
                formatted_date = date_str
            
            return {
                "response": f"Great! I see you want to schedule something for {formatted_date}. What time would work best for you?",
                "next_node": "collect_time"
            }
        else:
            # We have both date and time, show availability or confirm
            return await self._handle_show_availability(conversation, user_message, intent_analysis)
    
    async def _handle_collect_date(self, conversation: ConversationState, 
                                 user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect date information from user
        """
        extracted_info = intent_analysis.get("extracted_info", {})
        date = extracted_info.get("date")
        
        if date:
            # Date extracted, move to time collection
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d")
                
                return {
                    "response": f"Perfect! I have {formatted_date}. What time would you prefer for your appointment?",
                    "next_node": "collect_time"
                }
            except:
                return {
                    "response": "I'm having trouble understanding that date. Could you please specify the date more clearly? For example, 'tomorrow', 'next Monday', or 'June 28th'.",
                    "next_node": "collect_date"
                }
        else:
            return {
                "response": "I didn't catch a specific date. Could you tell me when you'd like to schedule your appointment? You can say 'tomorrow', 'next week', or give me a specific date.",
                "next_node": "collect_date"
            }
    
    async def _handle_collect_time(self, conversation: ConversationState, 
                                 user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect time information from user
        """
        extracted_info = intent_analysis.get("extracted_info", {})
        time = extracted_info.get("time")
        
        if time:
            # Time extracted, show availability
            return await self._handle_show_availability(conversation, user_message, intent_analysis)
        else:
            # Check if user mentioned time preference (morning, afternoon, etc.)
            time_pref = extracted_info.get("time_preference", "").lower()
            if time_pref in ["morning", "afternoon", "evening"]:
                return await self._handle_show_availability(conversation, user_message, intent_analysis)
            else:
                return {
                    "response": "What time would work best for you? You can be specific like '2:00 PM' or general like 'morning' or 'afternoon'.",
                    "next_node": "collect_time"
                }
    
    async def _handle_show_availability(self, conversation: ConversationState, 
                                      user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Show available time slots and handle booking
        """
        extracted_info = intent_analysis.get("extracted_info", {})
        
        # Get date from extracted info or conversation state
        date = extracted_info.get("date") or conversation.extracted_info.get("date")
        time = extracted_info.get("time") or conversation.extracted_info.get("time")
        duration = extracted_info.get("duration", 30)
        
        if not date:
            return {
                "response": "I need a date to check availability. What date would you like to schedule for?",
                "next_node": "collect_date"
            }
        
        try:
            # Get available slots
            available_slots = await calendar_service.get_availability(date, duration)
            
            if not available_slots:
                # No availability, suggest alternatives
                suggestions = await calendar_service.get_booking_suggestions(duration=duration)
                if suggestions:
                    suggestion_text = "\n".join([f"• {s['label']}" for s in suggestions[:3]])
                    return {
                        "response": f"I don't have any availability on {date}. Here are some alternative options:\n\n{suggestion_text}\n\nWould any of these work for you?",
                        "next_node": "intent_booking"
                    }
                else:
                    return {
                        "response": f"I don't have any availability on {date}. Would you like to try a different date?",
                        "next_node": "collect_date"
                    }
            
            # If specific time was requested, check if it's available
            if time:
                specific_slot = next((slot for slot in available_slots if slot.start_time == time), None)
                if specific_slot:
                    # Create and immediately book the appointment
                    booking = BookingRequest(
                        date=date,
                        time=time,
                        duration=duration,
                        title="Meeting"
                    )
                    
                    # Book the appointment
                    result = await calendar_service.book_appointment(booking)
                    date_obj = datetime.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%A, %B %d")
                    
                    if result["success"]:
                        return {
                            "response": f"Perfect! I've successfully booked your appointment for {formatted_date} at {time} for {duration} minutes. Your booking is confirmed!",
                            "next_node": "booking_complete",
                            "action": "booking_confirmed",
                            "booking_details": {
                                "date": date,
                                "time": time,
                                "duration": duration,
                                "title": "Meeting"
                            }
                        }
                    else:
                        return {
                            "response": f"I'm sorry, there was an issue booking that time slot. {result.get('error', 'Please try a different time.')}",
                            "next_node": "collect_time"
                        }
                else:
                    # Requested time not available, show alternatives
                    slot_text = "\n".join([f"• {slot.start_time} - {slot.end_time}" for slot in available_slots[:5]])
                    return {
                        "response": f"The time {time} isn't available on {date}. Here are some available options:\n\n{slot_text}\n\nWhich time would you prefer?",
                        "next_node": "collect_time"
                    }
            else:
                # Show available slots for user to choose
                slot_text = "\n".join([f"• {slot.start_time} - {slot.end_time}" for slot in available_slots[:5]])
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d")
                
                return {
                    "response": f"Here are the available time slots for {formatted_date}:\n\n{slot_text}\n\nWhich time would you prefer?",
                    "next_node": "collect_time"
                }
                
        except Exception as e:
            logger.error(f"Error showing availability: {str(e)}")
            return {
                "response": "I'm having trouble checking availability right now. Please try again in a moment.",
                "next_node": "intent_booking"
            }
    
    async def _handle_confirm_booking(self, conversation: ConversationState, 
                                    user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle booking confirmation
        """
        user_response = user_message.lower().strip()
        
        # Check for confirmation words
        if any(word in user_response for word in ["yes", "confirm", "book", "schedule", "ok", "sure", "please"]):
            return {
                "response": "Perfect! I'm booking your appointment now...",
                "next_node": "booking_complete",
                "action": "confirm_booking"
            }
        elif any(word in user_response for word in ["no", "cancel", "different", "change"]):
            conversation.pending_confirmation = None
            return {
                "response": "No problem! Let's find a different time that works better for you. What would you prefer?",
                "next_node": "collect_time"
            }
        else:
            return {
                "response": "Would you like me to confirm this appointment? Just let me know 'yes' to book it or 'no' if you'd like to choose a different time.",
                "next_node": "confirm_booking"
            }
    
    async def _handle_booking_complete(self, conversation: ConversationState, 
                                     user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle completed booking
        """
        return {
            "response": "Your appointment has been successfully booked! You should receive a confirmation shortly. Is there anything else I can help you with?",
            "next_node": "start"
        }
    
    async def _handle_general_query(self, conversation: ConversationState, 
                                   user_message: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle general queries and provide helpful responses
        """
        intent = intent_analysis.get("intent", "")
        
        if intent == "check_availability":
            return await self._handle_show_availability(conversation, user_message, intent_analysis)
        else:
            return {
                "response": "I'm here to help you with appointment scheduling. I can:\n\n• Book new appointments\n• Check availability\n• Find suitable time slots\n\nWhat would you like to do?",
                "next_node": "start"
            }
