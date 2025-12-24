"""
Voice Booking Handler - Main handler for voice-based appointment booking
Orchestrates voice interactions, AI processing, and booking management.
"""

import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from booking_manager import BookingManager
from ai_voice_processor import AIVoiceProcessor


class VoiceBookingHandler:
    """Handles complete voice booking workflow."""
    
    def __init__(self):
        """Initialize voice booking handler."""
        self.booking_manager = BookingManager()
        self.ai_processor = AIVoiceProcessor()
        self.conversation_history = []
    
    def process_voice_input(
        self,
        audio_file_path: str,
        session_id: Optional[str] = None
    ) -> Dict:
        """
        Process voice input and return response.
        
        Args:
            audio_file_path: Path to audio file with user's speech
            session_id: Optional session ID for conversation continuity
        
        Returns:
            Dictionary with:
            - text_response: Text response to speak to user
            - audio_file_path: Path to generated audio file (optional)
            - booking_status: Status of booking (pending, confirmed, etc.)
            - booking_info: Booking details if confirmed
        """
        # Convert speech to text
        try:
            user_message = self.ai_processor.speech_to_text(audio_file_path)
        except Exception as e:
            return {
                "text_response": "I'm sorry, I had trouble understanding you. Could you please repeat that?",
                "error": str(e)
            }
        
        # Extract booking intent
        extracted = self.ai_processor.extract_booking_intent(user_message)
        intent = extracted.get("intent", "unknown")
        
        # Get context for AI response
        context = self._build_context(extracted)
        
        # Process conversation
        try:
            ai_response = self.ai_processor.process_conversation(
                user_message=user_message,
                conversation_history=self.conversation_history,
                context=context
            )
        except Exception as e:
            return {
                "text_response": "I'm sorry, I'm experiencing technical difficulties. Please try again in a moment.",
                "error": str(e)
            }
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Handle booking actions
        booking_info = None
        booking_status = None
        
        if intent == "book" and self._has_complete_booking_info(extracted):
            booking_info = self._create_booking(extracted)
            if booking_info:
                booking_status = "confirmed"
                ai_response += f" Your confirmation number is {booking_info['confirmation_number']}."
        
        elif intent == "reschedule" and extracted.get("confirmation_number"):
            booking_info = self._reschedule_booking(extracted)
            if booking_info:
                booking_status = "rescheduled"
        
        elif intent == "cancel" and extracted.get("confirmation_number"):
            success = self._cancel_booking(extracted.get("confirmation_number"))
            if success:
                booking_status = "cancelled"
                ai_response = "Your appointment has been cancelled. Is there anything else I can help you with?"
        
        # Generate audio response (optional - can be done by telephony service)
        audio_file_path = None
        if os.getenv("GENERATE_AUDIO_RESPONSES", "false").lower() == "true":
            try:
                audio_file_path = f".tmp/voice_response_{session_id or 'default'}.mp3"
                self.ai_processor.text_to_speech(ai_response, audio_file_path)
            except Exception as e:
                # Audio generation is optional, continue without it
                pass
        
        return {
            "text_response": ai_response,
            "audio_file_path": audio_file_path,
            "booking_status": booking_status,
            "booking_info": booking_info,
            "extracted_intent": extracted
        }
    
    def _build_context(self, extracted: Dict) -> Dict:
        """Build context dictionary for AI processing."""
        context = {}
        
        # Add available slots if date is mentioned
        if extracted.get("date"):
            slots = self.booking_manager.get_available_slots(extracted["date"])
            context["available_slots"] = slots
            context["requested_date"] = extracted["date"]
        
        # Add existing bookings if phone number is mentioned
        if extracted.get("phone"):
            existing_bookings = self.booking_manager.get_booking_by_phone(extracted["phone"])
            context["existing_bookings"] = [
                {
                    "confirmation_number": b["confirmation_number"],
                    "datetime": b["appointment_datetime"],
                    "status": b["status"]
                }
                for b in existing_bookings
            ]
        
        return context
    
    def _has_complete_booking_info(self, extracted: Dict) -> bool:
        """Check if extracted info has enough data to create booking."""
        required_fields = ["patient_name", "phone", "date", "time"]
        return all(extracted.get(field) for field in required_fields)
    
    def _create_booking(self, extracted: Dict) -> Optional[Dict]:
        """Create booking from extracted information."""
        try:
            appointment_datetime = f"{extracted['date']} {extracted['time']}"
            booking = self.booking_manager.create_booking(
                patient_name=extracted["patient_name"],
                phone=extracted["phone"],
                email=extracted.get("email"),
                appointment_datetime=appointment_datetime,
                reason=extracted.get("reason")
            )
            return booking
        except Exception as e:
            return None
    
    def _reschedule_booking(self, extracted: Dict) -> Optional[Dict]:
        """Reschedule booking from extracted information."""
        try:
            if not extracted.get("date") or not extracted.get("time"):
                return None
            
            appointment_datetime = f"{extracted['date']} {extracted['time']}"
            booking = self.booking_manager.update_booking(
                confirmation_number=extracted["confirmation_number"],
                appointment_datetime=appointment_datetime
            )
            return booking
        except Exception as e:
            return None
    
    def _cancel_booking(self, confirmation_number: str) -> bool:
        """Cancel booking."""
        return self.booking_manager.cancel_booking(confirmation_number)
    
    def reset_conversation(self):
        """Reset conversation history for new session."""
        self.conversation_history = []


if __name__ == "__main__":
    # Example usage
    handler = VoiceBookingHandler()
    
    # Note: This requires an actual audio file for testing
    # In production, this would be called by a telephony service (Twilio, etc.)
    print("Voice booking handler initialized. Ready to process voice calls.")

