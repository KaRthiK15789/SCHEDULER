from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .models import ChatRequest, ChatResponse
from .agent import BookingAgent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Booking Agent API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the booking agent
booking_agent = BookingAgent()

@app.get("/")
async def root():
    return {"message": "AI Booking Agent API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": booking_agent.get_current_time()}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Handle chat requests and process them through the booking agent
    """
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")
        
        # Process the message through the booking agent
        result = await booking_agent.process_message(
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        return ChatResponse(
            response=result["response"],
            booking_confirmed=result.get("booking_confirmed", False),
            booking_details=result.get("booking_details", {}),
            conversation_id=request.conversation_id
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process request: {str(e)}"
        )

@app.get("/availability/{date}")
async def get_availability(date: str):
    """
    Get available time slots for a specific date
    """
    try:
        availability = await booking_agent.get_availability(date)
        return {"date": date, "available_slots": availability}
    except Exception as e:
        logger.error(f"Error getting availability: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get availability: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
