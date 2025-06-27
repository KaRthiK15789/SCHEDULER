# AI Booking Agent

## Overview

This is an AI-powered booking agent application that enables natural language appointment scheduling. The system consists of a Streamlit frontend and a FastAPI backend, utilizing OpenAI's GPT models for intelligent conversation handling and appointment booking logic.

## System Architecture

The application follows a microservices architecture with clear separation between frontend and backend:

- **Frontend**: Streamlit web application providing the user interface
- **Backend**: FastAPI REST API handling business logic and AI processing
- **AI Integration**: OpenAI GPT-4o for natural language understanding and conversation management
- **Calendar Service**: Mock calendar service (designed for easy replacement with Google Calendar API)

## Key Components

### Frontend (app.py)
- **Technology**: Streamlit
- **Purpose**: Provides chat interface for users to interact with the AI booking agent
- **Features**: 
  - Real-time chat interface
  - Automatic backend startup
  - Session state management
  - Responsive design

### Backend Components

#### Main API (backend/main.py)
- **Technology**: FastAPI with CORS middleware
- **Endpoints**:
  - `GET /` - Root endpoint
  - `GET /health` - Health check
  - `POST /chat` - Main chat processing endpoint
- **Features**: Comprehensive error handling and logging

#### Booking Agent (backend/agent.py)
- **Purpose**: Core AI agent logic orchestrating the entire booking process
- **Features**:
  - OpenAI GPT-4o integration
  - Conversation state management
  - Intent analysis and response generation
  - Booking confirmation workflow

#### Conversation Graph (backend/conversation_graph.py)
- **Purpose**: Manages conversation flow using a graph-based approach
- **Architecture**: Node-based conversation flow similar to LangGraph
- **Nodes**:
  - `start` - Initial conversation entry point
  - `intent_booking` - Booking intent detection
  - `collect_date` - Date collection and validation
  - `collect_time` - Time preference collection
  - `show_availability` - Display available time slots
  - `confirm_booking` - Booking confirmation
  - `booking_complete` - Completion handling
  - `handle_query` - General query processing

#### Calendar Service (backend/calendar_service.py)
- **Current Implementation**: Mock service with hardcoded availability
- **Architecture**: Designed for easy replacement with Google Calendar API
- **Features**:
  - Business hours enforcement (9 AM - 5 PM)
  - Weekend exclusion
  - Conflict detection
  - Flexible slot duration support

#### Data Models (backend/models.py)
- **Technology**: Pydantic models for data validation
- **Models**:
  - `ChatRequest/ChatResponse` - API communication
  - `BookingRequest` - Booking details
  - `TimeSlot` - Calendar time slot representation
  - `ConversationState` - Conversation tracking

### Utilities

#### DateTime Utils (utils/datetime_utils.py)
- **Purpose**: Natural language date parsing
- **Features**:
  - Relative date parsing ("tomorrow", "next week")
  - Multiple date format support
  - Weekday name recognition

## Data Flow

1. **User Input**: User sends message through Streamlit interface
2. **API Request**: Frontend sends POST request to `/chat` endpoint
3. **Intent Analysis**: OpenAI processes message to understand user intent
4. **Conversation Flow**: ConversationGraph routes to appropriate node
5. **Calendar Integration**: Calendar service checks availability when needed
6. **Response Generation**: AI generates contextual response
7. **State Update**: Conversation state is updated and persisted
8. **Frontend Display**: Response is displayed to user in chat interface

## External Dependencies

### Required API Keys
- **OpenAI API Key**: Required for GPT-4o model access
- Set as `OPENAI_API_KEY` environment variable

### Python Packages
- **streamlit**: Frontend web application framework
- **fastapi**: Backend API framework
- **uvicorn**: ASGI server for FastAPI
- **openai**: OpenAI API client
- **pydantic**: Data validation and serialization
- **requests**: HTTP client for frontend-backend communication

### Future Integrations
- **Google Calendar API**: To replace mock calendar service
- **Database**: For persistent conversation and booking storage

## Deployment Strategy

### Current Setup
- **Development**: Local deployment with automatic backend startup
- **Backend Port**: 8000 (FastAPI)
- **Frontend**: Streamlit default port
- **Process Management**: Backend started as subprocess from frontend

### Production Considerations
- Separate deployment of frontend and backend services
- Environment variable management for API keys
- Database integration for state persistence
- Load balancing and scaling considerations
- Monitoring and logging infrastructure

## User Preferences

Preferred communication style: Simple, everyday language.

## Changelog

Changelog:
- June 27, 2025. Initial setup