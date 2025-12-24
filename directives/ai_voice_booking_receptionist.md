# AI Voice Booking Receptionist Directive

## Goal
Provide an AI-powered voice receptionist system that can handle phone calls for a dental practice, allowing patients to book, reschedule, or cancel appointments through natural voice conversation.

## Inputs
- Incoming phone call (via Twilio, Vonage, or similar telephony service)
- Patient's voice input
- Current appointment availability data
- Patient records (if available)

## Tools/Scripts
- `execution/voice_booking_handler.py` - Main handler for voice interactions
- `execution/booking_manager.py` - Manages appointment CRUD operations
- `execution/ai_voice_processor.py` - Processes voice input/output with AI service

## Outputs
- Confirmed appointment booking
- Appointment modification (reschedule/cancel)
- Voice response to patient
- Appointment data stored in booking system

## Process Flow

1. **Call Reception**
   - Answer incoming call
   - Greet caller with professional dental office greeting
   - Identify if caller is new or existing patient

2. **Intent Recognition**
   - Determine caller's intent: book, reschedule, cancel, or inquiry
   - Extract key information: preferred date/time, patient name, phone number, reason for visit

3. **Availability Check**
   - Query available appointment slots
   - Consider office hours, existing bookings, and provider schedules
   - Suggest alternative times if preferred slot unavailable

4. **Appointment Confirmation**
   - Confirm appointment details with patient
   - Collect/verify patient information
   - Provide confirmation number and appointment details

5. **Call Completion**
   - Thank patient
   - Offer additional assistance
   - End call gracefully

## Edge Cases
- Patient wants to speak to human receptionist → transfer option
- Unclear intent → ask clarifying questions
- No availability in requested timeframe → suggest alternatives
- Patient provides incomplete information → request missing details
- Technical issues → graceful error handling and retry
- Multiple appointment requests → handle sequentially
- Appointment conflicts → detect and resolve

## AI Service Integration
- Use OpenAI Whisper for speech-to-text
- Use OpenAI TTS (text-to-speech) for voice responses
- Use GPT-4 or similar for conversation management and intent extraction
- Maintain conversation context throughout call

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

## Security & Privacy
- HIPAA compliance considerations
- Secure storage of patient information
- Encrypted voice data transmission
- Access controls for appointment data

