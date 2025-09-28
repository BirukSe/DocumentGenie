import os
import requests
from typing import Optional
from supabase import create_client, Client
import tempfile

class SupabaseService:
    def __init__(self):
        self.url = None
        self.key = None
        self.client = None
    
    def _ensure_client(self):
        if self.client is None:
            self.url = os.getenv("SUPABASE_URL")
            self.key = os.getenv("SUPABASE_ANON_KEY")
            if not self.url or not self.key:
                raise Exception("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")
            self.client = create_client(self.url, self.key)
    
    async def download_document(self, document_url: str) -> str:
        """Download document from Supabase storage to local temp file"""
        self._ensure_client()
        try:
            # Extract file path from URL
            file_path = document_url.split('/')[-1]
            
            # Download file
            response = requests.get(document_url)
            response.raise_for_status()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(response.content)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            raise Exception(f"Failed to download document: {str(e)}")
    
    async def upload_document(self, file_path: str, document_id: str) -> str:
        """Upload modified document back to Supabase storage"""
        self._ensure_client()
        try:
            # Read file content
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # Upload to Supabase storage
            bucket_name = "documents"
            file_name = f"{document_id}_modified.pdf"
            
            result = self.client.storage.from_(bucket_name).upload(
                file_name, file_content, {"upsert": "true"}
            )
            
            if result.get("error"):
                raise Exception(f"Upload failed: {result['error']}")
            
            # Get public URL
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_name)
            return public_url
            
        except Exception as e:
            raise Exception(f"Failed to upload document: {str(e)}")
    
    async def update_document_record(self, document_id: str, new_url: str):
        """Update document record with new URL after modification"""
        self._ensure_client()
        try:
            result = self.client.table("documents").update({
                "file_url": new_url,
                "status": "modified",
                "updated_at": "now()"
            }).eq("id", document_id).execute()
            
            if result.get("error"):
                raise Exception(f"Database update failed: {result['error']}")
                
        except Exception as e:
            raise Exception(f"Failed to update document record: {str(e)}")

# Global instance
supabase_service = SupabaseService()