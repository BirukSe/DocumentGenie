import tempfile
import os
import shutil
from typing import Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class TempStorageManager:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, document_id: str, original_file_path: str) -> str:
        """Create a temporary session for document modification"""
        session_dir = os.path.join(self.temp_dir, document_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Copy original file to session directory
        temp_file_path = os.path.join(session_dir, "working_copy.pdf")
        shutil.copy2(original_file_path, temp_file_path)
        
        self.sessions[document_id] = {
            "temp_file_path": temp_file_path,
            "original_file_path": original_file_path,
            "created_at": time.time(),
            "modifications": [],
            "is_modified": False
        }
        
        return temp_file_path
    
    def get_session(self, document_id: str) -> Optional[dict]:
        """Get session information"""
        return self.sessions.get(document_id)
    
    def update_session(self, document_id: str, new_file_path: str, operation: str):
        """Update session with new file path and copy file to session directory"""
        if document_id not in self.sessions:
            return False
        
        session = self.sessions[document_id]
        session_dir = os.path.dirname(session["temp_file_path"])
        
        # Copy the new file to the session directory with expected name
        session_file_path = os.path.join(session_dir, "working_copy.pdf")
        
        try:
            # Check if source and destination are the same file
            if os.path.exists(new_file_path):
                if os.path.samefile(new_file_path, session_file_path):
                    # Files are the same, no need to copy, just update session info
                    logger.info(f"Source and destination are the same file: {new_file_path}")
                else:
                    # Files are different, copy the new file
                    shutil.copy2(new_file_path, session_file_path)
                    logger.info(f"Copied {new_file_path} to {session_file_path}")
                
                # Update session info
                session["temp_file_path"] = session_file_path
                session["is_modified"] = True
                session["last_operation"] = operation
                session["modifications"].append({
                    "operation": operation,
                    "timestamp": time.time(),
                    "file_path": session_file_path
                })
                
                return True
        except Exception as e:
            print(f"Error updating session: {e}")
            return False
        
        return False
    
    def cleanup_session(self, document_id: str):
        """Clean up temporary files for a session"""
        if document_id in self.sessions:
            session_dir = os.path.dirname(self.sessions[document_id]["temp_file_path"])
            shutil.rmtree(session_dir, ignore_errors=True)
            del self.sessions[document_id]
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up sessions older than specified hours"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        expired_sessions = []
        for doc_id, session in self.sessions.items():
            if current_time - session["created_at"] > max_age_seconds:
                expired_sessions.append(doc_id)
        
        for doc_id in expired_sessions:
            self.cleanup_session(doc_id)

temp_storage = TempStorageManager()