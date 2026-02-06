"""
FastAPI Backend Server for Azure Doc Agent

Provides REST API endpoints for the React frontend
"""

import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv

from .azure_doc_agent import AzureDocAgent

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("LOG_FILE", "logs/agent.log")

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Configure logging with TimedRotatingFileHandler (daily rotation)
file_handler = TimedRotatingFileHandler(
    log_file,
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)
file_handler.suffix = "%Y-%m-%d"
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logging.basicConfig(
    level=getattr(logging, log_level),
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Azure Doc Agent API",
    description="REST API for Azure Documentation Agent",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: Optional[AzureDocAgent] = None
active_threads: Dict[str, List[Dict[str, Any]]] = {}


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    timestamp: str


class SkillInfo(BaseModel):
    name: str
    description: str
    tags: List[str]


class ThreadInfo(BaseModel):
    thread_id: str
    message_count: int
    last_updated: str


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent
    
    try:
        logger.info("Initializing Azure Doc Agent...")
        
        agent = AzureDocAgent(
            azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_openai_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            mcp_server_url=os.getenv("MCP_SERVER_URL", "https://learn.microsoft.com/api/mcp"),
            skills_directory=os.getenv("SKILLS_DIRECTORY", "skills")
        )
        
        await agent.initialize()
        logger.info("Azure Doc Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent
    
    if agent:
        await agent.close()
        logger.info("Azure Doc Agent shut down")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Azure Doc Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_initialized": agent is not None
    }


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Send a chat message to the agent with streaming response (SSE)
    
    Args:
        request: ChatRequest with message and optional thread_id
        
    Returns:
        Server-Sent Events stream with real-time response
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    async def event_generator():
        try:
            # Create thread if not exists
            thread_id = request.thread_id
            if not thread_id:
                thread_id = agent.create_thread()
            elif thread_id not in agent.threads:
                agent.create_thread(thread_id)
            
            # Send thread_id first
            yield f"data: {json.dumps({'type': 'thread_id', 'thread_id': thread_id})}\n\n"
            
            # Stream thinking/progress updates
            async for chunk in agent.chat_stream_with_thinking(request.message, thread_id=thread_id):
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Chat streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a chat message to the agent (non-streaming, for backward compatibility)
    
    Args:
        request: ChatRequest with message and optional thread_id
        
    Returns:
        ChatResponse with agent's reply
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Create thread if not exists
        thread_id = request.thread_id
        if not thread_id:
            thread_id = agent.create_thread()
        elif thread_id not in agent.threads:
            agent.create_thread(thread_id)
        
        # Get response from agent (using stream internally but collecting full response)
        response = await agent.chat(request.message, thread_id=thread_id, stream=True)
        
        # Update active threads
        if thread_id not in active_threads:
            active_threads[thread_id] = []
        
        active_threads[thread_id].append({
            "user": request.message,
            "assistant": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            response=response,
            thread_id=thread_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/skills", response_model=List[SkillInfo])
async def list_skills():
    """
    List all available skills
    
    Returns:
        List of skills with metadata
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        skills = agent.registry.list_skills()
        return [
            SkillInfo(
                name=skill.name,
                description=skill.description,
                tags=skill.tags
            )
            for skill in skills
        ]
    except Exception as e:
        logger.error(f"Error listing skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads", response_model=List[ThreadInfo])
async def list_threads():
    """
    List all active conversation threads
    
    Returns:
        List of threads with metadata
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        threads = []
        for thread_id, messages in agent.threads.items():
            threads.append(ThreadInfo(
                thread_id=thread_id,
                message_count=len(messages),
                last_updated=messages[-1]["timestamp"] if messages else datetime.now().isoformat()
            ))
        
        return threads
    except Exception as e:
        logger.error(f"Error listing threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str):
    """
    Get conversation history for a specific thread
    
    Args:
        thread_id: Thread identifier
        
    Returns:
        List of messages in the thread
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        history = agent.get_thread_history(thread_id)
        if history is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {"thread_id": thread_id, "messages": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thread history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/threads/new")
async def create_thread(thread_id: Optional[str] = None):
    """
    Create a new conversation thread
    
    Args:
        thread_id: Optional custom thread ID
        
    Returns:
        Created thread information
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        new_thread_id = agent.create_thread(thread_id)
        return {
            "thread_id": new_thread_id,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """
    Delete a conversation thread
    
    Args:
        thread_id: Thread to delete
        
    Returns:
        Success message
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if thread_id in agent.threads:
            del agent.threads[thread_id]
            if thread_id in active_threads:
                del active_threads[thread_id]
            return {"message": f"Thread {thread_id} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Thread not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """
    WebSocket endpoint for real-time chat
    
    Args:
        websocket: WebSocket connection
        thread_id: Thread identifier
    """
    await websocket.accept()
    
    if not agent:
        await websocket.send_json({"error": "Agent not initialized"})
        await websocket.close()
        return
    
    # Create thread if not exists
    if thread_id not in agent.threads:
        agent.create_thread(thread_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            if not message:
                continue
            
            # Get response from agent
            response = await agent.chat(message, thread_id=thread_id)
            
            # Send response
            await websocket.send_json({
                "response": response,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for thread {thread_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
