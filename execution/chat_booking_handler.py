"""
Chat Booking Handler - Main handler for chat-based appointment booking
Orchestrates chat interactions, AI processing, and booking management.
"""

import os
from typing import Dict, Optional, List
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from booking_manager import BookingManager
from ai_chat_processor import AIChatProcessor


class ChatBookingHandler:
    """Handles complete chat booking workflow."""
    
    def __init__(self):
        """Initialize chat booking handler."""
        self.booking_manager = BookingManager()
        self.ai_processor = AIChatProcessor()
        # Store conversation histories by session ID
        self.conversation_sessions = {}
    
    def process_message(
        self,
        user_message: str,
        session_id: str = "default"
    ) -> Dict:
        """
        Process chat message and return response.
        
        Args:
            user_message: User's chat message
            session_id: Session ID for conversation continuity
        
        Returns:
            Dictionary with:
            - text_response: Text response to send to user
            - booking_status: Status of booking (pending, confirmed, etc.)
            - booking_info: Booking details if confirmed
            - available_slots: Available time slots (if relevant)
        """
        # Get or create conversation history for this session
        if session_id not in self.conversation_sessions:
            self.conversation_sessions[session_id] = []
        
        conversation_history = self.conversation_sessions[session_id]
        
        # Extract booking intent
        extracted = self.ai_processor.extract_booking_intent(user_message)
        intent = extracted.get("intent", "unknown")
        
        # Get context for AI response
        context = self._build_context(extracted)
        
        # Process conversation
        try:
            ai_response = self.ai_processor.process_message(
                user_message=user_message,
                conversation_history=conversation_history,
                context=context
            )
        except Exception as e:
            # Log error for debugging and self-annealing
            import traceback
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "user_message": user_message[:100],  # First 100 chars
                "timestamp": datetime.now().isoformat()
            }
            self._log_error(error_details)
            return {
                "text_response": "I'm sorry, I'm experiencing technical difficulties. Please try again in a moment.",
                "error": str(e)
            }
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Handle booking actions
        booking_info = None
        booking_status = None
        available_slots = None
        
        if intent == "book" and self._has_complete_booking_info(extracted):
            booking_info = self._create_booking(extracted)
            if booking_info:
                booking_status = "confirmed"
                ai_response += f"\n\n✅ Your appointment is confirmed! Confirmation number: **{booking_info['confirmation_number']}**"
                ai_response += f"\n📅 Date: {booking_info['appointment_datetime']}"
        
        elif intent == "reschedule" and extracted.get("confirmation_number"):
            booking_info = self._reschedule_booking(extracted)
            if booking_info:
                booking_status = "rescheduled"
                ai_response = f"✅ Your appointment has been rescheduled to {booking_info['appointment_datetime']}. Confirmation number: {booking_info['confirmation_number']}"
        
        elif intent == "cancel" and extracted.get("confirmation_number"):
            success = self._cancel_booking(extracted.get("confirmation_number"))
            if success:
                booking_status = "cancelled"
                ai_response = "✅ Your appointment has been cancelled. Is there anything else I can help you with?"
        
        # If user is asking about availability, provide slots
        if intent == "book" and extracted.get("date") and not booking_info:
            available_slots = self.booking_manager.get_available_slots(extracted["date"])
            if available_slots:
                slots_text = ", ".join(available_slots[:10])  # Show first 10 slots
                ai_response += f"\n\nAvailable times on {extracted['date']}: {slots_text}"
        
        return {
            "text_response": ai_response,
            "booking_status": booking_status,
            "booking_info": booking_info,
            "available_slots": available_slots,
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
    
    def reset_session(self, session_id: str):
        """Reset conversation history for a session."""
        if session_id in self.conversation_sessions:
            del self.conversation_sessions[session_id]
    
    def _log_error(self, error_details: Dict):
        """Log errors for self-annealing analysis."""
        import json
        from pathlib import Path
        
        error_log_path = Path(".tmp/error_log.jsonl")
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(error_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_details) + '\n')
        except Exception:
            pass  # Don't fail if logging fails


if __name__ == "__main__":
    # Example usage
    handler = ChatBookingHandler()
    
    # Simulate a conversation
    response1 = handler.process_message("Hi, I'd like to book an appointment", "session123")
    print(f"Bot: {response1['text_response']}")
    
    response2 = handler.process_message("Tomorrow at 2pm for John Doe, phone 555-1234", "session123")
    print(f"Bot: {response2['text_response']}")

