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

import time
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@app.get("/api/temp-preview/{document_id}")
async def get_temp_preview(document_id: str):
    """Serve temporary modified PDF with enhanced debugging and proper headers"""
    logger.info(f"=== PDF Preview Request for document: {document_id} ===")
    
    session = temp_storage.get_session(document_id)
    if not session:
        logger.error(f"Session not found for preview: {document_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    file_path = session["temp_file_path"]
    logger.info(f"Preview file path: {file_path}")
    logger.info(f"Preview file exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        logger.error(f"Preview file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Preview file not found")
    
    file_size = os.path.getsize(file_path)
    file_mtime = os.path.getmtime(file_path)
    logger.info(f"Preview file size: {file_size} bytes")
    logger.info(f"Preview file modified time: {file_mtime}")
    
    if file_size == 0:
        logger.error(f"Preview file is empty: {file_path}")
        raise HTTPException(status_code=404, detail="Preview file is empty")
    
    # Check if file was recently modified
    import time
    current_time = time.time()
    time_since_modification = current_time - file_mtime
    logger.info(f"Time since last modification: {time_since_modification:.2f} seconds")
    
    from fastapi.responses import FileResponse
    
    # Enhanced headers to prevent caching and ensure fresh content
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Content-Length": str(file_size),
        "X-File-Size": str(file_size),
        "X-Last-Modified": str(int(file_mtime)),
        "X-Time-Since-Mod": f"{time_since_modification:.2f}s",
        "X-Document-ID": document_id,
        "Content-Disposition": f"inline; filename=preview_{document_id}.pdf"
    }
    
    response = FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"preview_{document_id}.pdf",
        headers=headers
    )
    
    logger.info(f"Serving preview file: {file_size} bytes with headers: {headers}")
    return response
@app.post("/api/document/session/init")
async def init_session(request: dict):
    """Initialize a document modification session with enhanced debugging"""
    document_id = request["document_id"]
    original_url = request["original_url"]
    
    logger.info(f"Initializing session for document: {document_id}")
    logger.info(f"Original URL: {original_url}")
    
    try:
        # Download document from Supabase
        local_file_path = await supabase_service.download_document(original_url)
        logger.info(f"Downloaded file to: {local_file_path}")
        
        # Verify downloaded file
        if not os.path.exists(local_file_path):
            raise Exception(f"Downloaded file not found: {local_file_path}")
        
        file_size = os.path.getsize(local_file_path)
        logger.info(f"Downloaded file size: {file_size} bytes")
        
        if file_size == 0:
            raise Exception("Downloaded file is empty")
        
        # Create temporary session
        temp_file_path = temp_storage.create_session(document_id, local_file_path)
        logger.info(f"Created session file: {temp_file_path}")
        
        # Verify session file
        if not os.path.exists(temp_file_path):
            raise Exception(f"Session file not created: {temp_file_path}")
        
        session_file_size = os.path.getsize(temp_file_path)
        logger.info(f"Session file size: {session_file_size} bytes")
        
        return {
            "status": "initialized", 
            "temp_file_path": temp_file_path,
            "file_size": session_file_size
        }
        
    except Exception as e:
        logger.error(f"Session initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session initialization failed: {str(e)}")

@app.post("/api/document/modify", response_model=ModificationResponse)
async def modify_document(request: ModificationRequest):
    """Process document modification request with enhanced debugging"""
    document_id = request.document_id
    command = request.command
    
    logger.info(f"Processing modification request for document: {document_id}")
    logger.info(f"Command: {command}")
    
    # Get session
    session = temp_storage.get_session(document_id)
    if not session:
        logger.error(f"Session not found for document: {document_id}")
        # Try to reinitialize session if it was lost
        try:
            # This is a fallback - in production, the frontend should handle session management
            logger.warning(f"Attempting to reinitialize session for document: {document_id}")
            raise HTTPException(status_code=404, detail="Session not found. Please refresh the page and try again.")
        except Exception as e:
            logger.error(f"Failed to reinitialize session: {e}")
            raise HTTPException(status_code=404, detail="Session not found. Please refresh the page and try again.")
    
    session_file = session["temp_file_path"]
    logger.info(f"Session file path: {session_file}")
    logger.info(f"Session file exists: {os.path.exists(session_file)}")
    
    if os.path.exists(session_file):
        logger.info(f"Session file size: {os.path.getsize(session_file)} bytes")
    
    # Send progress update
    await manager.broadcast_to_document({
        "type": "manipulation_progress",
        "operation": "processing_command",
        "progress": 10,
        "message": "Processing command..."
    }, document_id)
    
    try:
        # Process with agent (async with real-time updates)
        logger.info("Starting agent processing...")
        result = await agent.process_command_async(session_file, command, document_id)
        
        logger.info(f"Agent processing result: {result.get('success', False)}")
        
        if result["success"]:
            result_path = result.get("result_path", session_file)
            logger.info(f"Result path: {result_path}")
            logger.info(f"Result file exists: {os.path.exists(result_path)}")
            
            if os.path.exists(result_path):
                logger.info(f"Result file size: {os.path.getsize(result_path)} bytes")
            
            # Update session
            temp_storage.update_session(document_id, result_path, command)
            
            # Create cache-busting preview URL
            preview_url = f"/api/temp-preview/{document_id}?t={int(time.time() * 1000)}"
            
            # Send completion update
            await manager.send_manipulation_complete(
                document_id=document_id,
                operation="document_modification",
                result_path=result_path,
                preview_url=preview_url
            )
            
            return ModificationResponse(
                status="success",
                preview_url=preview_url,
                progress=100,
                message="Modification completed",
                changes=[command]
            )
        else:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Agent processing failed: {error_msg}")
            await manager.send_error(document_id, error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
            
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Modification failed: {error_msg}", exc_info=True)
        await manager.send_error(document_id, error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# @app.post("/api/document/modify", response_model=ModificationResponse)
# async def modify_document(request: ModificationRequest):
#     """Process document modification request"""
#     document_id = request.document_id
#     command = request.command
    
#     # Get session
#     session = temp_storage.get_session(document_id)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found")
    
#     # Send progress update
#     await manager.broadcast_to_document({
#         "type": "progress",
#         "progress": 10,
#         "message": "Processing command..."
#     }, document_id)
    
#     try:
#         # Process with agent (async with real-time updates)
#         result = await agent.process_command_async(session["temp_file_path"], command, document_id)
        
#         if result["success"]:
#             # Update session
#             temp_storage.update_session(document_id, result["result_path"], command)
            
#             # Send completion update
#             await manager.send_manipulation_complete(
#                 document_id, 
#                 "document_modification", 
#                 result["result_path"], 
#                 f"/api/temp-preview/{document_id}"
#             )
            
#             return ModificationResponse(
#                 status="success",
#                 preview_url=f"/api/temp-preview/{document_id}",
#                 progress=100,
#                 message="Modification completed",
#                 changes=[command]
#             )
#         else:
#             await manager.send_error(document_id, result["error"], "document_modification")
#             raise HTTPException(status_code=400, detail=result["error"])
            
#     except Exception as e:
#         await manager.send_error(document_id, f"Unexpected error: {str(e)}", "document_modification")
#         raise HTTPException(status_code=500, detail=str(e))


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
    """Discard modifications and reset to original document"""
    document_id = request["document_id"]
    
    try:
        # Get current session
        session = temp_storage.get_session(document_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Reset to original document instead of cleaning up session
        original_file_path = session["original_file_path"]
        temp_file_path = session["temp_file_path"]
        
        # Copy original file back to working copy
        import shutil
        shutil.copy2(original_file_path, temp_file_path)
        
        # Reset session state
        session["modifications"] = []
        session["is_modified"] = False
        
        logger.info(f"Reset document {document_id} to original state")
        
        # Send reset notification
        await manager.broadcast_to_document({
            "type": "document_reset",
            "message": "Document reset to original state",
            "preview_url": f"/api/temp-preview/{document_id}?t={int(time.time() * 1000)}"
        }, document_id)
        
        return {"status": "discarded", "message": "Modifications discarded, document reset to original"}
        
    except Exception as e:
        await manager.send_error(document_id, f"Failed to discard: {str(e)}", "discarding_document")
        raise HTTPException(status_code=500, detail=str(e))

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
