from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import asyncio
from dotenv import load_dotenv

from models.schemas import ModificationRequest, ModificationResponse
from agents.document_agent import DocumentAgent
from services.websocket_service import manager
from utils.temp_storage import temp_storage
from services.supabase_service import supabase_service

load_dotenv()

app = FastAPI(title="DocumentGenie AI Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent with websocket manager
agent = DocumentAgent(websocket_manager=manager)

@app.get("/")
async def root():
    return {"message": "DocumentGenie AI Agent API"}

@app.post("/api/document/session/init")
async def init_session(request: dict):
    """Initialize a document modification session"""
    document_id = request["document_id"]
    original_url = request["original_url"]
    
    # Download document from Supabase
    local_file_path = await supabase_service.download_document(original_url)
    
    # Create temporary session
    temp_file_path = temp_storage.create_session(document_id, local_file_path)
    
    return {"status": "initialized", "temp_file_path": temp_file_path}

@app.post("/api/document/modify", response_model=ModificationResponse)
async def modify_document(request: ModificationRequest):
    """Process document modification request"""
    document_id = request.document_id
    command = request.command
    
    # Get session
    session = temp_storage.get_session(document_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Send progress update
    await manager.broadcast_to_document({
        "type": "progress",
        "progress": 10,
        "message": "Processing command..."
    }, document_id)
    
    try:
        # Process with agent (async with real-time updates)
        result = await agent.process_command_async(session["temp_file_path"], command, document_id)
        
        if result["success"]:
            # Update session
            temp_storage.update_session(document_id, result["result_path"], command)
            
            # Send completion update
            await manager.send_manipulation_complete(
                document_id, 
                "document_modification", 
                result["result_path"], 
                f"/api/temp-preview/{document_id}"
            )
            
            return ModificationResponse(
                status="success",
                preview_url=f"/api/temp-preview/{document_id}",
                progress=100,
                message="Modification completed",
                changes=[command]
            )
        else:
            await manager.send_error(document_id, result["error"], "document_modification")
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        await manager.send_error(document_id, f"Unexpected error: {str(e)}", "document_modification")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/temp-preview/{document_id}")
async def get_temp_preview(document_id: str):
    """Serve temporary modified PDF"""
    session = temp_storage.get_session(document_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return FileResponse(
        session["temp_file_path"],
        media_type="application/pdf",
        filename=f"preview_{document_id}.pdf"
    )

@app.post("/api/document/save")
async def save_modifications(request: dict):
    """Save modifications to Supabase"""
    document_id = request["document_id"]
    
    session = temp_storage.get_session(document_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session["is_modified"]:
        return {"status": "no_changes"}
    
    try:
        # Send progress update
        await manager.send_manipulation_progress(
            document_id, "saving_document", 25, "Uploading modified document to Supabase..."
        )
        
        # Upload modified file to Supabase
        new_url = await supabase_service.upload_document(session["temp_file_path"], document_id)
        
        await manager.send_manipulation_progress(
            document_id, "saving_document", 75, "Updating document record..."
        )
        
        # Update document record
        await supabase_service.update_document_record(document_id, new_url)
        
        # Send completion
        await manager.send_manipulation_complete(
            document_id, "saving_document", session["temp_file_path"], new_url
        )
        
        # Clean up session
        temp_storage.cleanup_session(document_id)
        
        return {"status": "saved", "new_url": new_url}
        
    except Exception as e:
        await manager.send_error(document_id, f"Failed to save: {str(e)}", "saving_document")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/document/discard")
async def discard_modifications(request: dict):
    """Discard modifications and clean up session"""
    document_id = request["document_id"]
    temp_storage.cleanup_session(document_id)
    return {"status": "discarded"}

@app.websocket("/ws/document/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, document_id)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            
            # Handle different message types from client
            try:
                import json
                message = json.loads(data)
                
                if message.get("type") == "heartbeat":
                    await manager.send_to_websocket({
                        "type": "heartbeat_response",
                        "timestamp": asyncio.get_event_loop().time()
                    }, websocket)
                elif message.get("type") == "get_session_status":
                    session_status = manager.get_document_session(document_id)
                    await manager.send_to_websocket({
                        "type": "session_status",
                        "status": session_status
                    }, websocket)
                else:
                    # Echo back unknown messages
                    await manager.send_to_websocket({
                        "type": "echo",
                        "data": data
                    }, websocket)
                    
            except json.JSONDecodeError:
                # Handle plain text messages as heartbeat
                await manager.send_to_websocket({
                    "type": "text_received",
                    "message": data
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
