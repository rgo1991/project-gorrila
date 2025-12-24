"""
Web Application - Flask app serving voice and chat booking interfaces
Provides REST API endpoints and web UI for dental booking system.
"""

import os
import uuid
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    # Handle encoding issues - try UTF-8 first, fallback to system default
    try:
        load_dotenv(dotenv_path=env_path, encoding='utf-8')
    except UnicodeDecodeError:
        # If UTF-8 fails, try reading and converting
        with open(env_path, 'r', encoding='utf-16') as f:
            content = f.read()
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        load_dotenv(dotenv_path=env_path, encoding='utf-8')

# Check and fix httpx compatibility issue
try:
    import httpx
    httpx_version = tuple(map(int, httpx.__version__.split('.')[:2]))
    if httpx_version >= (0, 28):
        print("=" * 60)
        print("ERROR: Incompatible httpx version detected!")
        print(f"Current version: {httpx.__version__}")
        print("\nFIXING: Attempting to install compatible version...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "httpx", "-y", "--quiet"])
            subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx==0.27.0", "--quiet"])
            print("SUCCESS: Installed httpx 0.27.0")
            print("Please restart the application.")
            print("=" * 60)
            sys.exit(0)
        except Exception as e:
            print(f"FAILED: Could not auto-fix. Error: {e}")
            print("\nPlease manually run:")
            print("  pip uninstall httpx -y")
            print("  pip install httpx==0.27.0")
            print("=" * 60)
            sys.exit(1)
except Exception:
    pass

from chat_booking_handler import ChatBookingHandler
from voice_booking_handler import VoiceBookingHandler
from self_annealing import SelfAnnealingSystem
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for API endpoints

# Initialize handlers
chat_handler = ChatBookingHandler()
voice_handler = VoiceBookingHandler()

# Initialize self-annealing system
annealing_system = SelfAnnealingSystem()

# Helper functions for logging
def _log_error_for_learning(error_data):
    """Log errors for self-annealing."""
    try:
        annealing_system._log_learning({
            "type": "error",
            **error_data
        })
    except Exception:
        pass

def _log_successful_booking(booking_data):
    """Log successful bookings for learning."""
    try:
        annealing_system._log_learning({
            "type": "successful_booking",
            "data": booking_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception:
        pass

# HTML template for chat interface
CHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dental Booking Chatbot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .chat-container {
            width: 90%;
            max-width: 500px;
            height: 80vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        .chat-header p {
            font-size: 14px;
            opacity: 0.9;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message.user {
            justify-content: flex-end;
        }
        .message.bot {
            justify-content: flex-start;
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .message.bot .message-content {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        .chat-input-form {
            display: flex;
            gap: 10px;
        }
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input:focus {
            border-color: #667eea;
        }
        .send-button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s;
        }
        .send-button:hover {
            transform: scale(1.05);
        }
        .send-button:active {
            transform: scale(0.95);
        }
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border-radius: 18px;
            max-width: 70px;
        }
        .typing-indicator.active {
            display: block;
        }
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        .typing-dot {
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🦷 Dental Booking Assistant</h1>
            <p>I can help you book, reschedule, or cancel appointments</p>
        </div>
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div class="message-content">
                    Hello! 👋 I'm your AI booking assistant. How can I help you today?
                </div>
            </div>
        </div>
        <div class="chat-input-container">
            <form class="chat-input-form" id="chatForm">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="messageInput" 
                    placeholder="Type your message..." 
                    autocomplete="off"
                />
                <button type="submit" class="send-button">Send</button>
            </form>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        const sessionId = 'session_' + Math.random().toString(36).substr(2, 9);

        function addMessage(text, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
            messageDiv.innerHTML = `<div class="message-content">${text}</div>`;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTypingIndicator() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot';
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = `
                <div class="message-content typing-indicator active">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            `;
            chatMessages.appendChild(typingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideTypingIndicator() {
            const typingIndicator = document.getElementById('typingIndicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage(message, true);
            messageInput.value = '';
            showTypingIndicator();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId
                    })
                });

                const data = await response.json();
                hideTypingIndicator();
                addMessage(data.text_response, false);
            } catch (error) {
                hideTypingIndicator();
                addMessage('Sorry, I encountered an error. Please try again.', false);
                console.error('Error:', error);
            }
        });

        // Allow Enter key to send (but Shift+Enter for new line)
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve chat interface."""
    return render_template_string(CHAT_HTML)


@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """Handle chat messages."""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        response = chat_handler.process_message(message, session_id)
        
        # Log successful interactions for learning
        if response.get('booking_status') == 'confirmed':
            _log_successful_booking(response)
        
        return jsonify(response)
    
    except Exception as e:
        # Log the error for debugging and self-annealing
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in chat endpoint: {str(e)}")
        print(error_trace)
        
        # Log for self-annealing
        _log_error_for_learning({
            "endpoint": "/api/chat",
            "error": str(e),
            "traceback": error_trace,
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({'error': str(e), 'text_response': 'Sorry, I encountered an error. Please try again.'}), 500


@app.route('/api/voice', methods=['POST'])
def voice_endpoint():
    """Handle voice input (requires audio file upload)."""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', str(uuid.uuid4()))
        
        # Save uploaded file temporarily
        audio_path = f".tmp/voice_input_{session_id}.mp3"
        os.makedirs('.tmp', exist_ok=True)
        audio_file.save(audio_path)
        
        response = voice_handler.process_voice_input(audio_path, session_id)
        
        # Clean up temporary file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e), 'text_response': 'Sorry, I encountered an error processing your voice input.'}), 500


@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get bookings for a date or phone number."""
    try:
        date = request.args.get('date')
        phone = request.args.get('phone')
        
        if date:
            bookings = chat_handler.booking_manager.get_bookings_by_date(date)
        elif phone:
            bookings = chat_handler.booking_manager.get_booking_by_phone(phone)
        else:
            return jsonify({'error': 'date or phone parameter required'}), 400
        
        return jsonify({'bookings': bookings})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/availability', methods=['GET'])
def get_availability():
    """Get available appointment slots for a date."""
    try:
        date = request.args.get('date')
        if not date:
            return jsonify({'error': 'date parameter required'}), 400
        
        slots = chat_handler.booking_manager.get_available_slots(date)
        return jsonify({'date': date, 'available_slots': slots})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        system_health = annealing_system.get_system_health()
        return jsonify({
            'status': 'healthy',
            'service': 'dental-booking-system',
            'system_health': system_health
        })
    except Exception:
        return jsonify({'status': 'healthy', 'service': 'dental-booking-system'})

@app.route('/api/annealing/analyze', methods=['GET'])
def analyze_errors():
    """Analyze errors for self-improvement."""
    try:
        days = int(request.args.get('days', 7))
        analysis = annealing_system.analyze_errors(days=days)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/annealing/improvements', methods=['GET'])
def get_improvements():
    """Get improvement suggestions."""
    try:
        improvements = annealing_system.generate_improvements()
        return jsonify({'improvements': improvements})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/annealing/apply', methods=['POST'])
def apply_improvements():
    """Apply improvements (auto-apply safe ones)."""
    try:
        auto_apply = request.json.get('auto_apply', False) if request.json else False
        result = annealing_system.apply_improvements(auto_apply=auto_apply)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diagnostic', methods=['GET'])
def diagnostic():
    """Diagnostic endpoint to check system status."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    diagnostics = {
        "api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "api_key_length": len(os.getenv("OPENAI_API_KEY", "")) if os.getenv("OPENAI_API_KEY") else 0,
        "api_key_prefix": os.getenv("OPENAI_API_KEY", "")[:7] if os.getenv("OPENAI_API_KEY") else "N/A",
        "model": os.getenv("OPENAI_MODEL", "gpt-4"),
    }
    
    # Test OpenAI connection
    try:
        from ai_chat_processor import AIChatProcessor
        processor = AIChatProcessor()
        test_response = processor.process_message("test", system_prompt="Reply with 'OK'")
        diagnostics["openai_connection"] = "working"
        diagnostics["test_response"] = test_response[:50]
    except Exception as e:
        diagnostics["openai_connection"] = "failed"
        diagnostics["openai_error"] = str(e)
        diagnostics["error_type"] = type(e).__name__
    
    return jsonify(diagnostics)


if __name__ == '__main__':
    # Create .tmp directory if it doesn't exist
    os.makedirs('.tmp', exist_ok=True)
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Dental Booking System on port {port}")
    print(f"Chat interface: http://localhost:{port}/")
    print(f"API endpoints: http://localhost:{port}/api/")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

