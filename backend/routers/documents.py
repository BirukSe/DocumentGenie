from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, Dict, Any
import os
import tempfile
from datetime import datetime
import uuid
import shutil

from ..services.document_service import DocumentService
from ..dependencies import get_supabase_client
from supabase import Client as SupabaseClient

router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{document_id}/file")
async def get_document_file(
    document_id: str,
    user_id: str = Depends(get_current_user_id),  # You'll need to implement this dependency
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Get the file content of a document"""
    try:
        doc_service = DocumentService(supabase)
        result = await doc_service.get_working_copy(document_id, user_id)
        
        # Return the file directly
        return FileResponse(
            result['working_copy_path'],
            media_type='application/pdf',
            filename=os.path.basename(result['document']['file_path'])
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            e = HTTPException(status_code=500, detail=str(e))
        raise e

@router.post("/{document_id}/save")
async def save_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Save changes made to a working copy back to storage"""
    try:
        doc_service = DocumentService(supabase)
        
        # Get the working copy path
        working_copy = await doc_service.get_working_copy(document_id, user_id)
        working_copy_path = working_copy['working_copy_path']
        
        # Save changes back to storage
        result = await doc_service.save_changes(working_copy_path, document_id, user_id)
        
        # Clean up the working copy after saving
        doc_service.cleanup_working_copy(document_id, user_id)
        
        return result
        
    except Exception as e:
        if not isinstance(e, HTTPException):
            e = HTTPException(status_code=500, detail=str(e))
        raise e

@router.delete("/{document_id}/discard")
async def discard_changes(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Discard changes made to a working copy"""
    try:
        doc_service = DocumentService(supabase)
        doc_service.cleanup_working_copy(document_id, user_id)
        return {"status": "success", "message": "Changes discarded"}
    except Exception as e:
        if not isinstance(e, HTTPException):
            e = HTTPException(status_code=500, detail=str(e))
        raise e

# WebSocket endpoint for real-time updates
@router.websocket("/ws/{document_id}")
async def document_websocket(
    websocket: WebSocket,
    document_id: str,
    user_id: str = Depends(get_websocket_user_id)  # You'll need to implement this
):
    """WebSocket endpoint for real-time document updates"""
    await websocket.accept()
    supabase = get_supabase_client()
    doc_service = DocumentService(supabase)
    
    try:
        # Get or create working copy when client connects
        result = await doc_service.get_working_copy(document_id, user_id)
        working_copy_path = result['working_copy_path']
        
        # Send initial document state
        await websocket.send_json({
            "type": "document_ready",
            "document_id": document_id,
            "file_url": f"/api/documents/{document_id}/file"
        })
        
        while True:
            # Handle incoming messages (e.g., save requests)
            data = await websocket.receive_json()
            
            if data.get('type') == 'save':
                # Save changes
                result = await doc_service.save_changes(working_copy_path, document_id, user_id)
                await websocket.send_json({
                    "type": "saved",
                    "success": True,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        # Clean up on disconnect if needed
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass
    finally:
        # Clean up resources
        doc_service.cleanup_working_copy(document_id, user_id)
        await websocket.close()

# Helper functions for authentication (you'll need to implement these based on your auth system)
async def get_current_user_id() -> str:
    """Get the current user ID from the request"""
    # Implement your authentication logic here
    # This is a placeholder - replace with your actual auth logic
    return "user123"

async def get_websocket_user_id(websocket: WebSocket) -> str:
    """Get the user ID from WebSocket connection"""
    # Implement your WebSocket authentication logic here
    # This is a placeholder - replace with your actual auth logic
    return "user123"
