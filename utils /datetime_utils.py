from datetime import datetime, timedelta
from typing import Optional, Tuple
import re

def parse_relative_date(text: str, base_date: Optional[datetime] = None) -> Optional[str]:
    """
    Parse relative date expressions like 'tomorrow', 'next week', etc.
    Returns date in YYYY-MM-DD format or None if not parseable
    """
    if base_date is None:
        base_date = datetime.now()
    
    text = text.lower().strip()
    
    # Today/tomorrow/yesterday
    if "today" in text:
        return base_date.strftime("%Y-%m-%d")
    elif "tomorrow" in text:
        return (base_date + timedelta(days=1)).strftime("%Y-%m-%d")
    elif "yesterday" in text:
        return (base_date - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Next week/this week
    elif "next week" in text:
        days_ahead = 7 - base_date.weekday()  # Days to next Monday
        return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    elif "this week" in text:
        days_ahead = 1 if base_date.weekday() == 6 else 0  # If Sunday, go to Monday
        return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # Specific weekdays
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(weekdays):
        if day in text:
            days_ahead = i - base_date.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            return (base_date + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # Try to parse specific dates (e.g., "June 28", "6/28", "28/6")
    date_patterns = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",  # MM/DD/YYYY or DD/MM/YYYY
        r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                parts = match.groups()
                if len(parts[2]) == 2:  # Convert 2-digit year to 4-digit
                    year = int(parts[2]) + 2000
                else:
                    year = int(parts[2])
                
                # Assume MM/DD format for ambiguous cases
                month, day = int(parts[0]), int(parts[1])
                
                parsed_date = datetime(year, month, day)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
    
    return None

def parse_time_expression(text: str) -> Optional[str]:
    """
    Parse time expressions and return in HH:MM format
    """
    text = text.lower().strip()
    
    # Direct time patterns
    time_patterns = [
        r"(\d{1,2}):(\d{2})\s*([ap]m)?",  # 2:30 PM, 14:30
        r"(\d{1,2})\s*([ap]m)",  # 2 PM, 2PM, 9am
        r"(\d{1,2})\.(\d{2})",  # 2.30
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            hour = int(match.group(1))
            
            # Handle different group structures
            if pattern == r"(\d{1,2})\s*([ap]m)":
                minute = 0
                am_pm = match.group(2).lower() if len(match.groups()) > 1 else None
            else:
                minute = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) and match.group(2).isdigit() else 0
                am_pm = match.group(3).lower() if len(match.groups()) > 2 and match.group(3) else None
            
            # Handle AM/PM
            if am_pm:
                if am_pm == "pm" and hour != 12:
                    hour += 12
                elif am_pm == "am" and hour == 12:
                    hour = 0
            
            # Validate time
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
    
    # Relative time expressions
    time_mappings = {
        "morning": "09:00",
        "afternoon": "14:00",
        "evening": "18:00",
        "noon": "12:00",
        "midnight": "00:00"
    }
    
    for keyword, time_str in time_mappings.items():
        if keyword in text:
            return time_str
    
    return None

def get_time_preference_range(preference: str) -> Tuple[str, str]:
    """
    Get time range for preferences like 'morning', 'afternoon'
    Returns (start_time, end_time) in HH:MM format
    """
    ranges = {
        "morning": ("09:00", "12:00"),
        "afternoon": ("12:00", "17:00"),
        "evening": ("17:00", "20:00"),
        "late morning": ("10:00", "12:00"),
        "early afternoon": ("12:00", "15:00"),
        "late afternoon": ("15:00", "17:00")
    }
    
    return ranges.get(preference.lower(), ("09:00", "17:00"))

def format_duration(minutes: int) -> str:
    """
    Format duration in a human-readable way
    """
    if minutes < 60:
        return f"{minutes} minutes"
    else:
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours > 1 else ''} and {remaining_minutes} minutes"

def is_business_day(date_str: str) -> bool:
    """
    Check if a date is a business day (Monday-Friday)
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.weekday() < 5  # 0-4 are Monday-Friday
    except ValueError:
        return False

def get_next_business_day(date_str: str) -> str:
    """
    Get the next business day after the given date
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        while True:
            date_obj += timedelta(days=1)
            if date_obj.weekday() < 5:  # Monday-Friday
                return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d")
