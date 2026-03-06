"""
Chat Router - WebSocket and REST endpoints for chat functionality.
"""

import json
import time
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models.schemas import ChatRequest, ChatResponse, WebSocketMessage
from ..services.chat_service import chat_service
from ..services.session_manager import session_manager

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """
    Send a chat message and get a response.
    
    This is the main REST endpoint for chat interactions.
    """
    try:
        response = await chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            history=request.history
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    Supports streaming responses and typing indicators.
    """
    await websocket.accept()
    session_id: Optional[str] = None
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get('message', '')
            session_id = message_data.get('session_id')
            
            # Send typing indicator
            await websocket.send_json({
                'type': 'typing',
                'data': {'status': 'started'},
                'timestamp': time.time()
            })
            
            # Process message
            response = await chat_service.process_message(
                message=user_message,
                session_id=session_id
            )
            
            # Send typing stopped
            await websocket.send_json({
                'type': 'typing',
                'data': {'status': 'stopped'},
                'timestamp': time.time()
            })
            
            # Send response
            await websocket.send_json({
                'type': 'message',
                'data': response,
                'timestamp': time.time()
            })
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.send_json({
            'type': 'error',
            'data': {'message': str(e)},
            'timestamp': time.time()
        })


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    history = chat_service.get_session_history(session_id)
    return {"session_id": session_id, "history": history}


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session"""
    chat_service.clear_session(session_id)
    return {"message": "Session cleared", "session_id": session_id}
