# Phase 6: Chat Application

Mutual Fund RAG Chatbot - Full-stack chat application with FastAPI backend and React frontend.

## Architecture

```
phase6_chat_app/
├── backend/           # FastAPI Backend
│   ├── app/
│   │   ├── models/    # Pydantic schemas
│   │   ├── routers/   # API endpoints
│   │   └── services/  # Business logic
│   └── main.py        # Entry point
└── frontend/          # React Frontend
    ├── src/
    │   ├── pages/     # Page components
    │   ├── store/     # Zustand state management
    │   └── styles.css # Global styles
    └── public/
```

## Backend

### Features
- **REST API**: `/chat` endpoint for chat messages
- **WebSocket**: `/chat/ws` for real-time chat
- **Fund API**: `/funds` for fund data access
- **Health Check**: `/health` for system status
- **Session Management**: In-memory session storage
- **RAG Integration**: Connects to Phase 3 & 4 components

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Running

```bash
# Development
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/chat` | POST | Send chat message |
| `/chat/ws` | WebSocket | Real-time chat |
| `/chat/history/{session_id}` | GET | Get chat history |
| `/funds` | GET | List all funds |
| `/funds/search` | GET | Search funds |
| `/health` | GET | Health check |

## Frontend

### Features
- **Chat Interface**: Matching the reference image design
- **Message Bubbles**: User (blue) and Assistant (white) styling
- **Typing Indicator**: Animated dots while waiting
- **Suggestion Chips**: Quick query suggestions
- **Source Citations**: Links to Groww pages
- **Responsive Design**: Works on mobile and desktop

### Installation

```bash
cd frontend
npm install
```

### Running

```bash
# Development
npm start

# Build for production
npm run build
```

### Access

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## UI Design

The chat interface replicates the reference image with:

- **Header**: Avatar, name, status, action buttons (phone, video, more)
- **Messages**: 
  - User messages: Blue gradient, right-aligned
  - Assistant messages: White with border, left-aligned
  - Timestamps and avatars
- **Input Area**: 
  - Attachment, image, emoji buttons
  - Text input with placeholder
  - Voice, camera, send buttons
- **Suggestions**: Quick-action chips for common queries

## Integration with Previous Phases

- **Phase 1**: Uses `extracted_funds.json` for fund data
- **Phase 3**: Connects to Hybrid Retriever for document retrieval
- **Phase 4**: Uses GroqClient for LLM responses and Guardrails for safety
- **Phase 5**: Can be tested with the test suite

## Environment Variables

Create a `.env` file in the backend directory:

```env
GROQ_API_KEY=your_groq_api_key
```

## Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## Deployment

### Backend
```bash
cd backend
docker build -t mf-chatbot-backend .
docker run -p 8000:8000 mf-chatbot-backend
```

### Frontend
```bash
cd frontend
npm run build
# Serve build/ directory with nginx or similar
```
