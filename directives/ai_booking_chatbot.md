# AI Booking Chatbot Directive

## Goal
Provide an AI-powered chatbot interface for a dental practice website that allows patients to book, reschedule, or cancel appointments through text-based conversation.

## Inputs
- User text messages (via web chat interface)
- Current appointment availability data
- Patient records (if available)
- Chat conversation history

## Tools/Scripts
- `execution/chat_booking_handler.py` - Main handler for chat interactions
- `execution/booking_manager.py` - Manages appointment CRUD operations
- `execution/ai_chat_processor.py` - Processes chat messages with AI service

## Outputs
- Confirmed appointment booking
- Appointment modification (reschedule/cancel)
- Text response to user
- Appointment data stored in booking system

## Process Flow

1. **Chat Initiation**
   - Greet user with friendly dental office welcome message
   - Offer assistance with booking, rescheduling, or inquiries
   - Identify if user is new or returning patient

2. **Intent Recognition**
   - Analyze user message to determine intent: book, reschedule, cancel, or inquiry
   - Extract key information: preferred date/time, patient name, contact info, reason for visit
   - Handle multi-turn conversations to gather all required information

3. **Availability Check**
   - Query available appointment slots
   - Consider office hours, existing bookings, and provider schedules
   - Display available times in user-friendly format
   - Suggest alternatives if preferred slot unavailable

4. **Appointment Confirmation**
   - Present appointment details for user confirmation
   - Collect/verify patient information
   - Provide confirmation number and appointment summary
   - Send confirmation via email/SMS (optional)

5. **Chat Completion**
   - Thank user
   - Offer additional assistance or resources
   - Provide option to speak with human if needed

## Edge Cases
- User wants to speak to human → provide contact information or transfer option
- Unclear intent → ask clarifying questions
- No availability in requested timeframe → suggest alternatives
- User provides incomplete information → request missing details in friendly manner
- Technical issues → graceful error handling and retry
- Multiple appointment requests → handle sequentially
- Appointment conflicts → detect and resolve
- User abandons conversation → save partial booking state (optional)

## AI Service Integration
- Use GPT-4 or similar for conversation management and intent extraction
- Maintain conversation context throughout chat session
- Support natural language understanding for flexible user input
- Handle typos and informal language gracefully

## User Interface
- Web-based chat widget (can be embedded in website)
- Mobile-responsive design
- Typing indicators
- Quick reply buttons for common actions (optional)
- Appointment calendar picker integration

## Data Requirements
- Office hours and availability
- Provider schedules
- Existing appointments
- Patient database (optional but recommended)

## Error Handling
- Network failures → retry with exponential backoff
- API rate limits → queue requests
- Invalid inputs → request clarification
- Database errors → log and provide fallback response
- Session timeouts → save state and allow resume

## Security & Privacy
- HIPAA compliance considerations
- Secure storage of patient information
- Encrypted chat data transmission
- Access controls for appointment data
- Session management and timeout handling

