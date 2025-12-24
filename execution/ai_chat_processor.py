"""
AI Chat Processor - Handles chat message processing with AI services
Processes text-based conversations for booking chatbot.
"""

import os
import json
from typing import Dict, Optional, List
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()


class AIChatProcessor:
    """Processes chat interactions using AI services."""
    
    def __init__(self):
        """Initialize AI chat processor with API keys from environment."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client (for version 1.0+)
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    def process_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process chat message with AI model.
        
        Args:
            user_message: User's chat message
            conversation_history: Previous conversation messages in format [{"role": "user/assistant", "content": "..."}]
            system_prompt: System prompt for AI behavior
            context: Additional context (e.g., available slots, booking info)
        
        Returns:
            AI response text
        """
        if conversation_history is None:
            conversation_history = []
        
        if system_prompt is None:
            system_prompt = """You are a friendly and helpful AI chatbot for a dental practice. 
            Your role is to assist patients with booking, rescheduling, or canceling appointments through text chat.
            Be warm, professional, and concise. Use emojis sparingly but appropriately.
            Always confirm appointment details before finalizing.
            If you need information you don't have (like available slots), let the user know you're checking."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add context if provided
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({
                "role": "system",
                "content": f"Additional context: {context_str}"
            })
        
        # Add conversation history
        messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            # Enhanced error handling with retry logic
            error_msg = str(e)
            
            # Check for specific error types
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("API authentication failed. Please check your OpenAI API key.")
            elif "rate_limit" in error_msg.lower() or "429" in error_msg:
                raise Exception("Rate limit exceeded. Please wait a moment and try again.")
            elif "invalid" in error_msg.lower() and "model" in error_msg.lower():
                raise Exception(f"Invalid model: {self.model}. Please check your model configuration.")
            else:
                raise Exception(f"AI chat processing failed: {error_msg}")
    
    def extract_booking_intent(self, user_message: str) -> Dict:
        """
        Extract booking intent and information from user message.
        
        Args:
            user_message: User's chat message
        
        Returns:
            Dictionary with extracted information (intent, date, time, name, phone, etc.)
        """
        system_prompt = """Extract booking information from the user's chat message. 
        Return a JSON object with the following fields:
        - intent: "book", "reschedule", "cancel", "inquiry", or "unknown"
        - date: requested date in YYYY-MM-DD format (if mentioned)
        - time: requested time in HH:MM format (if mentioned)
        - patient_name: patient's name (if mentioned)
        - phone: phone number (if mentioned)
        - email: email address (if mentioned)
        - reason: reason for visit (if mentioned)
        - confirmation_number: confirmation number (if mentioned, for reschedule/cancel)
        
        Only include fields that are explicitly mentioned. Return valid JSON only."""
        
        try:
            response = self.process_message(
                user_message=user_message,
                system_prompt=system_prompt
            )
            
            # Try to parse JSON from response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
                response = response.strip()
            
            extracted = json.loads(response)
            return extracted
        except json.JSONDecodeError:
            # Fallback: return basic intent detection
            message_lower = user_message.lower()
            intent = "unknown"
            if any(word in message_lower for word in ["book", "schedule", "appointment", "make an appointment"]):
                intent = "book"
            elif any(word in message_lower for word in ["reschedule", "change", "move"]):
                intent = "reschedule"
            elif any(word in message_lower for word in ["cancel"]):
                intent = "cancel"
            
            return {"intent": intent}
        except Exception as e:
            return {"intent": "unknown", "error": str(e)}


if __name__ == "__main__":
    # Example usage (requires OPENAI_API_KEY in environment)
    processor = AIChatProcessor()
    
    # Test conversation
    response = processor.process_message(
        user_message="Hi, I'd like to book an appointment",
        context={"available_slots": ["14:00", "14:30", "15:00"]}
    )
    print(f"AI Response: {response}")
    
    # Test intent extraction
    intent = processor.extract_booking_intent("I need to book a cleaning for next Tuesday at 2pm")
    print(f"Extracted Intent: {intent}")

