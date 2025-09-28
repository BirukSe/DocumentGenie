import tempfile
import os
import shutil
from typing import Dict, Optional
import time

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
    
    def update_session(self, document_id: str, new_file_path: str, modification: str):
        """Update session with new modification"""
        if document_id in self.sessions:
            # Replace working copy with modified version
            session = self.sessions[document_id]
            shutil.copy2(new_file_path, session["temp_file_path"])
            
            session["modifications"].append(modification)
            session["is_modified"] = True
    
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