from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, time
import logging
from .models import TimeSlot, BookingRequest

logger = logging.getLogger(__name__)

class MockCalendarService:
    """
    Mock calendar service that simulates Google Calendar functionality.
    This can be easily replaced with actual Google Calendar API integration.
    """
    
    def __init__(self):
        # Mock existing bookings for demonstration
        self.existing_bookings = {
            "2025-06-27": [
                {"start": "09:00", "end": "10:00", "title": "Team Meeting"},
                {"start": "14:00", "end": "15:30", "title": "Client Call"},
            ],
            "2025-06-28": [
                {"start": "11:00", "end": "12:00", "title": "Project Review"},
                {"start": "16:00", "end": "17:00", "title": "One-on-One"},
            ],
            "2025-06-30": [
                {"start": "10:00", "end": "11:00", "title": "Stand-up"},
                {"start": "15:00", "end": "16:00", "title": "Planning"},
            ]
        }
        
        # Business hours configuration
        self.business_start = time(9, 0)  # 9:00 AM
        self.business_end = time(17, 0)   # 5:00 PM
        self.slot_duration = 30  # 30 minutes default
    
    async def get_availability(self, date: str, duration: int = 30) -> List[TimeSlot]:
        """
        Get available time slots for a given date
        """
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            
            # Don't show availability for past dates
            if date_obj < datetime.now().date():
                return []
            
            # Skip weekends for simplicity
            if date_obj.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                return []
            
            existing_bookings = self.existing_bookings.get(date, [])
            available_slots = []
            
            # Generate time slots from business hours
            current_time = datetime.combine(date_obj, self.business_start)
            end_time = datetime.combine(date_obj, self.business_end)
            
            while current_time + timedelta(minutes=duration) <= end_time:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=duration)).time()
                
                # Check if this slot conflicts with existing bookings
                is_available = True
                for booking in existing_bookings:
                    booking_start = datetime.strptime(booking["start"], "%H:%M").time()
                    booking_end = datetime.strptime(booking["end"], "%H:%M").time()
                    
                    # Check for overlap
                    if (slot_start < booking_end and slot_end > booking_start):
                        is_available = False
                        break
                
                available_slots.append(TimeSlot(
                    start_time=slot_start.strftime("%H:%M"),
                    end_time=slot_end.strftime("%H:%M"),
                    available=is_available
                ))
                
                current_time += timedelta(minutes=self.slot_duration)
            
            # Return only available slots
            return [slot for slot in available_slots if slot.available]
            
        except Exception as e:
            logger.error(f"Error getting availability for {date}: {str(e)}")
            return []
    
    async def book_appointment(self, booking: BookingRequest) -> Dict[str, Any]:
        """
        Book an appointment
        """
        try:
            # Validate the booking request
            date_obj = datetime.strptime(booking.date, "%Y-%m-%d").date()
            time_obj = datetime.strptime(booking.time, "%H:%M").time()
            
            # Check if the date is in the future
            if date_obj < datetime.now().date():
                return {
                    "success": False,
                    "error": "Cannot book appointments in the past"
                }
            
            # Check if the time slot is available
            available_slots = await self.get_availability(booking.date, booking.duration)
            requested_slot = next(
                (slot for slot in available_slots if slot.start_time == booking.time),
                None
            )
            
            if not requested_slot:
                return {
                    "success": False,
                    "error": "The requested time slot is not available"
                }
            
            # Add the booking to our mock storage
            if booking.date not in self.existing_bookings:
                self.existing_bookings[booking.date] = []
            
            end_time = (datetime.combine(date_obj, time_obj) + 
                       timedelta(minutes=booking.duration)).time()
            
            self.existing_bookings[booking.date].append({
                "start": booking.time,
                "end": end_time.strftime("%H:%M"),
                "title": booking.title,
                "description": booking.description
            })
            
            logger.info(f"Booking confirmed for {booking.date} at {booking.time}")
            
            return {
                "success": True,
                "booking_id": f"book_{int(datetime.now().timestamp())}",
                "message": f"Appointment booked successfully for {booking.date} at {booking.time}"
            }
            
        except Exception as e:
            logger.error(f"Error booking appointment: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to book appointment: {str(e)}"
            }
    
    async def get_booking_suggestions(self, preferred_date: Optional[str] = None, 
                                    preferred_time: Optional[str] = None,
                                    duration: int = 30) -> List[Dict[str, Any]]:
        """
        Get booking suggestions based on preferences
        """
        suggestions = []
        
        # If no preferred date, suggest next 7 business days
        if not preferred_date:
            current_date = datetime.now().date()
            for i in range(1, 15):  # Look ahead 2 weeks
                check_date = current_date + timedelta(days=i)
                if check_date.weekday() < 5:  # Skip weekends
                    date_str = check_date.strftime("%Y-%m-%d")
                    available_slots = await self.get_availability(date_str, duration)
                    
                    if available_slots:
                        # Suggest morning, afternoon, and evening slots if available
                        morning_slots = [s for s in available_slots if s.start_time < "12:00"]
                        afternoon_slots = [s for s in available_slots if "12:00" <= s.start_time < "17:00"]
                        
                        if morning_slots:
                            suggestions.append({
                                "date": date_str,
                                "time": morning_slots[0].start_time,
                                "duration": duration,
                                "label": f"{check_date.strftime('%A, %B %d')} - Morning"
                            })
                        
                        if afternoon_slots:
                            suggestions.append({
                                "date": date_str,
                                "time": afternoon_slots[0].start_time,
                                "duration": duration,
                                "label": f"{check_date.strftime('%A, %B %d')} - Afternoon"
                            })
                    
                    if len(suggestions) >= 5:  # Limit suggestions
                        break
        else:
            # Get suggestions for specific date
            available_slots = await self.get_availability(preferred_date, duration)
            for slot in available_slots[:5]:  # Limit to first 5 slots
                date_obj = datetime.strptime(preferred_date, "%Y-%m-%d")
                suggestions.append({
                    "date": preferred_date,
                    "time": slot.start_time,
                    "duration": duration,
                    "label": f"{date_obj.strftime('%A, %B %d')} at {slot.start_time}"
                })
        
        return suggestions

# Initialize the calendar service
calendar_service = MockCalendarService()
