"""
AI Voice Processor - Handles voice input/output processing with AI services
Processes speech-to-text, text-to-speech, and conversation management.
"""

import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()


class AIVoiceProcessor:
    """Processes voice interactions using AI services."""
    
    def __init__(self):
        """Initialize AI voice processor with API keys from environment."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client (for version 1.0+)
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.tts_model = os.getenv("OPENAI_TTS_MODEL", "tts-1")
        self.whisper_model = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
    
    def speech_to_text(self, audio_file_path: str) -> str:
        """
        Convert speech audio to text using Whisper.
        
        Args:
            audio_file_path: Path to audio file
        
        Returns:
            Transcribed text
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio_file
                )
                return transcript.text
        except Exception as e:
            raise Exception(f"Speech-to-text conversion failed: {str(e)}")
    
    def text_to_speech(self, text: str, output_path: str, voice: str = "alloy") -> str:
        """
        Convert text to speech audio using OpenAI TTS.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        
        Returns:
            Path to generated audio file
        """
        try:
            response = self.client.audio.speech.create(
                model=self.tts_model,
                voice=voice,
                input=text
            )
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            return output_path
        except Exception as e:
            raise Exception(f"Text-to-speech conversion failed: {str(e)}")
    
    def process_conversation(
        self,
        user_message: str,
        conversation_history: Optional[list] = None,
        system_prompt: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        Process conversation with AI model.
        
        Args:
            user_message: User's message/transcription
            conversation_history: Previous conversation messages
            system_prompt: System prompt for AI behavior
            context: Additional context (e.g., available slots, booking info)
        
        Returns:
            AI response text
        """
        if conversation_history is None:
            conversation_history = []
        
        if system_prompt is None:
            system_prompt = """You are a friendly and professional AI receptionist for a dental practice. 
            Your role is to help patients book, reschedule, or cancel appointments. 
            Be warm, clear, and efficient. Always confirm appointment details before finalizing.
            If you need information you don't have (like available slots), ask the user to wait while you check."""
        
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
            raise Exception(f"AI conversation processing failed: {str(e)}")
    
    def extract_booking_intent(self, user_message: str) -> Dict:
        """
        Extract booking intent and information from user message.
        
        Args:
            user_message: User's message
        
        Returns:
            Dictionary with extracted information (intent, date, time, name, phone, etc.)
        """
        system_prompt = """Extract booking information from the user's message. 
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
            response = self.process_conversation(
                user_message=user_message,
                system_prompt=system_prompt
            )
            
            # Try to parse JSON from response
            # Sometimes the model wraps JSON in markdown code blocks
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
            elif any(word in message_lower for word in ["cancel", "cancel"]):
                intent = "cancel"
            
            return {"intent": intent}
        except Exception as e:
            return {"intent": "unknown", "error": str(e)}


if __name__ == "__main__":
    # Example usage (requires OPENAI_API_KEY in environment)
    processor = AIVoiceProcessor()
    
    # Test conversation
    response = processor.process_conversation(
        user_message="I'd like to book an appointment for tomorrow at 2pm",
        context={"available_slots": ["14:00", "14:30", "15:00"]}
    )
    print(f"AI Response: {response}")
    
    # Test intent extraction
    intent = processor.extract_booking_intent("I need to reschedule my appointment from December 23rd to December 24th")
    print(f"Extracted Intent: {intent}")

