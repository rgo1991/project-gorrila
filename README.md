# Dental Booking System with AI Voice Receptionist and Chatbot

A comprehensive dental practice booking system featuring:
- 🤖 **AI Voice Receptionist** - Handle phone calls with natural voice conversation
- 💬 **AI Booking Chatbot** - Web-based chat interface for appointment booking
- 📅 **Booking Management** - Complete CRUD operations for appointments
- 🔄 **Self-Annealing System** - Continuously learns and improves from errors
- 📊 **Health Monitoring** - Real-time system health and diagnostics

## Features

### AI Voice Receptionist
- Speech-to-text conversion using OpenAI Whisper
- Text-to-speech responses using OpenAI TTS
- Natural conversation handling for booking, rescheduling, and cancellation
- Multi-turn conversation support

### AI Booking Chatbot
- Web-based chat interface
- Real-time availability checking
- Appointment booking, rescheduling, and cancellation
- Multi-turn conversations with context awareness

### Self-Annealing System
- Automatic error analysis and pattern detection
- Improvement suggestions based on error patterns
- System health monitoring
- Learning from successful interactions

## Project Structure

```
project-gorrila/
├── directives/              # Layer 1: SOPs and instructions
│   ├── ai_booking_chatbot.md
│   └── ai_voice_booking_receptionist.md
├── execution/                # Layer 3: Deterministic Python scripts
│   ├── ai_chat_processor.py
│   ├── ai_voice_processor.py
│   ├── booking_manager.py
│   ├── chat_booking_handler.py
│   ├── voice_booking_handler.py
│   ├── self_annealing.py
│   └── web_app.py
├── .tmp/                     # Temporary files (gitignored)
├── .env                      # Environment variables (gitignored)
├── requirements.txt
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
OPENAI_TTS_MODEL=tts-1
OPENAI_WHISPER_MODEL=whisper-1
APPOINTMENT_DURATION_MINUTES=30
PORT=5000
FLASK_DEBUG=False
GENERATE_AUDIO_RESPONSES=false
```

### 3. Fix Dependencies (if needed)

If you encounter httpx compatibility issues, run:

```powershell
.\fix_httpx.ps1
```

Or manually:
```bash
pip uninstall httpx -y
pip install httpx==0.27.0
```

### 4. Run the Application

```bash
cd execution
python web_app.py
```

The application will be available at:
- **Chat Interface**: http://localhost:5000/
- **API Endpoints**: http://localhost:5000/api/

## API Endpoints

### Chat & Voice
- `POST /api/chat` - Send chat message
- `POST /api/voice` - Upload audio file for voice processing

### Bookings
- `GET /api/bookings?date=YYYY-MM-DD` - Get bookings for a date
- `GET /api/bookings?phone=XXX-XXX-XXXX` - Get bookings for a phone number
- `GET /api/availability?date=YYYY-MM-DD` - Get available slots for a date

### System Health & Self-Annealing
- `GET /health` - Health check with system metrics
- `GET /api/diagnostic` - Detailed system diagnostics
- `GET /api/annealing/analyze?days=7` - Analyze errors
- `GET /api/annealing/improvements` - Get improvement suggestions
- `POST /api/annealing/apply` - Apply improvements

## Architecture

This project follows a **3-layer architecture**:

1. **Layer 1: Directives** - Natural language instructions (SOPs)
2. **Layer 2: Orchestration** - AI agent decision-making
3. **Layer 3: Execution** - Deterministic Python scripts

This separation ensures reliability by pushing complexity into deterministic code while keeping AI focused on intelligent routing and decision-making.

## Self-Annealing Features

The system automatically:
- Logs all errors with full context
- Analyzes error patterns over time
- Suggests improvements based on common issues
- Tracks system health metrics
- Learns from successful bookings

Error logs are stored in `.tmp/error_log.jsonl` and can be analyzed via the API endpoints.

## Security Notes

- `.env` file is gitignored - never commit API keys
- Patient data is stored locally in `.tmp/bookings.json`
- For production, consider using a proper database
- Ensure HIPAA compliance for production use

## Requirements

- Python 3.9+
- OpenAI API key
- Flask 3.0.0
- OpenAI library 2.14.0
- httpx 0.27.0 (for compatibility)

## License

This project is part of the project-gorrila repository.

## Contributing

This is a private project. For issues or improvements, please contact the repository owner.

