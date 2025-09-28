import os
import tempfile
import shutil
import uuid
from typing import Dict, Optional, Tuple
from supabase import create_client, Client as SupabaseClient
from fastapi import HTTPException
import fitz  # PyMuPDF

class DocumentService:
    def __init__(self, supabase: SupabaseClient):
        self.supabase = supabase
        self.workspace_dir = os.path.join(tempfile.gettempdir(), "documentgenie_workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    async def get_working_copy(self, document_id: str, user_id: str) -> Dict[str, str]:
        """
        Get or create a working copy of a document
        
        Args:
            document_id: The ID of the document in Supabase
            user_id: The ID of the user requesting the document
            
        Returns:
            Dict containing the working copy path and document metadata
        """
        try:
            # Get document metadata from Supabase
            response = self.supabase.table('documents').select('*').eq('id', document_id).eq('user_id', user_id).single().execute()
            if not response.data:
                raise HTTPException(status_code=404, detail="Document not found")
            
            document = response.data
            working_dir = os.path.join(self.workspace_dir, user_id, document_id)
            working_copy_path = os.path.join(working_dir, f"working_copy_{document_id}.pdf")
            
            # Create working directory if it doesn't exist
            os.makedirs(working_dir, exist_ok=True)
            
            # Download the file if working copy doesn't exist
            if not os.path.exists(working_copy_path):
                # Download the file from Supabase Storage
                file_path = document.get('file_path')
                if not file_path:
                    raise HTTPException(status_code=400, detail="Invalid document path")
                
                # Download file content
                bucket_name = file_path.split('/')[0] if '/' in file_path else 'documents'
                file_key = file_path.split('/', 1)[1] if '/' in file_path else file_path
                
                try:
                    file_content = self.supabase.storage.from_(bucket_name).download(file_key)
                    with open(working_copy_path, 'wb') as f:
                        f.write(file_content)
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")
            
            return {
                'working_copy_path': working_copy_path,
                'document': document
            }
            
        except Exception as e:
            if not isinstance(e, HTTPException):
                raise HTTPException(status_code=500, detail=f"Error getting working copy: {str(e)}")
            raise
    
    async def save_changes(self, working_copy_path: str, document_id: str, user_id: str) -> Dict[str, str]:
        """
        Save changes made to a working copy back to Supabase
        
        Args:
            working_copy_path: Path to the working copy of the document
            document_id: The ID of the document in Supabase
            user_id: The ID of the user saving the document
            
        Returns:
            Dict containing the updated document URL and metadata
        """
        try:
            # Verify the working copy exists
            if not os.path.exists(working_copy_path):
                raise HTTPException(status_code=404, detail="Working copy not found")
            
            # Get document metadata
            response = self.supabase.table('documents')\
                .select('*')\
                .eq('id', document_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
                
            if not response.data:
                raise HTTPException(status_code=404, detail="Document not found")
            
            document = response.data
            file_path = document.get('file_path')
            
            if not file_path:
                raise HTTPException(status_code=400, detail="Invalid document path")
            
            # Parse bucket and file key
            if '/' in file_path:
                bucket_name, file_key = file_path.split('/', 1)
            else:
                bucket_name = 'documents'
                file_key = file_path
            
            # Upload the updated file
            with open(working_copy_path, 'rb') as f:
                file_content = f.read()
                
            # Generate a new file key with a version timestamp
            file_ext = os.path.splitext(file_key)[1] or '.pdf'
            new_file_key = f"{os.path.splitext(file_key)[0]}_{int(datetime.utcnow().timestamp())}{file_ext}"
            
            # Upload the new version
            self.supabase.storage.from_(bucket_name).upload(
                new_file_key,
                file_content,
                {"content-type": "application/pdf"}
            )
            
            # Update document metadata with new path
            updated_doc = self.supabase.table('documents')\
                .update({
                    'file_path': f"{bucket_name}/{new_file_key}",
                    'updated_at': datetime.utcnow().isoformat() + 'Z'
                })\
                .eq('id', document_id)\
                .eq('user_id', user_id)\
                .execute()
            
            return {
                'success': True,
                'message': 'Document saved successfully',
                'document_id': document_id,
                'file_url': f"/api/documents/{document_id}/file"
            }
            
        except Exception as e:
            if not isinstance(e, HTTPException):
                raise HTTPException(status_code=500, detail=f"Error saving document: {str(e)}")
            raise
    
    def cleanup_working_copy(self, document_id: str, user_id: str) -> None:
        """
        Clean up working copy files for a document
        """
        try:
            working_dir = os.path.join(self.workspace_dir, user_id, document_id)
            if os.path.exists(working_dir):
                shutil.rmtree(working_dir, ignore_errors=True)
        except Exception:
            pass  # Ignore cleanup errors
