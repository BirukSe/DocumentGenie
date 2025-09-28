from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.document_sessions: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, document_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)
        
        # Initialize document session if not exists
        if document_id not in self.document_sessions:
            self.document_sessions[document_id] = {
                "status": "connected",
                "current_operation": None,
                "progress": 0,
                "modifications": []
            }
        
        # Send initial connection status
        await self.send_to_websocket({
            "type": "connection_established",
            "document_id": document_id,
            "message": "Connected to document session"
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, document_id: str):
        if document_id in self.active_connections:
            try:
                self.active_connections[document_id].remove(websocket)
                if not self.active_connections[document_id]:
                    del self.active_connections[document_id]
                    # Clean up session if no active connections
                    if document_id in self.document_sessions:
                        del self.document_sessions[document_id]
            except ValueError:
                pass  # WebSocket already removed
    
    async def send_to_websocket(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to websocket: {e}")
    
    async def broadcast_to_document(self, message: dict, document_id: str):
        """Broadcast message to all connections for a specific document"""
        if document_id in self.active_connections:
            # Update session state
            if document_id in self.document_sessions:
                session = self.document_sessions[document_id]
                session["progress"] = message.get("progress", session["progress"])
                session["current_operation"] = message.get("type", session["current_operation"])
                
                # Track modifications
                if message.get("type") == "modification_complete":
                    session["modifications"].append({
                        "timestamp": message.get("timestamp"),
                        "operation": message.get("operation"),
                        "details": message.get("details")
                    })
            
            # Broadcast to all connected clients
            disconnected = []
            for connection in self.active_connections[document_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to broadcast to connection: {e}")
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                try:
                    self.active_connections[document_id].remove(conn)
                except ValueError:
                    pass
    
    async def send_manipulation_progress(self, document_id: str, operation: str, 
                                       progress: int, message: str, details: Optional[dict] = None):
        """Send real-time PDF manipulation progress updates"""
        await self.broadcast_to_document({
            "type": "manipulation_progress",
            "operation": operation,
            "progress": progress,
            "message": message,
            "details": details or {},
            "timestamp": asyncio.get_event_loop().time()
        }, document_id)
    
    async def send_manipulation_complete(self, document_id: str, operation: str, 
                                       result_path: str, preview_url: str):
        """Send manipulation completion notification"""
        await self.broadcast_to_document({
            "type": "manipulation_complete",
            "operation": operation,
            "progress": 100,
            "message": f"{operation} completed successfully",
            "result_path": result_path,
            "preview_url": preview_url,
            "timestamp": asyncio.get_event_loop().time()
        }, document_id)
    
    async def send_error(self, document_id: str, error_message: str, operation: Optional[str] = None):
        """Send error notification"""
        await self.broadcast_to_document({
            "type": "error",
            "operation": operation,
            "progress": 0,
            "message": error_message,
            "timestamp": asyncio.get_event_loop().time()
        }, document_id)
    
    def get_document_session(self, document_id: str) -> Optional[dict]:
        """Get current session state for a document"""
        return self.document_sessions.get(document_id)
    
    def get_active_documents(self) -> List[str]:
        """Get list of documents with active connections"""
        return list(self.active_connections.keys())

manager = ConnectionManager()