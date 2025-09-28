from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
class CommandType(str, Enum):
    # Text Operations
    REPLACE_TEXT = "replace_text"
    MODIFY_PARAGRAPH = "modify_paragraph"
    MODIFY_SENTENCE = "modify_sentence"
    DELETE_TEXT = "delete_text"
    ADD_TEXT = "add_text"
    FORMAT_TEXT = "format_text"
    
    # Bullet Point Operations
    CONVERT_BULLETS_TO_NUMBERS = "convert_bullets_to_numbers"
    ADD_BULLET_POINT = "add_bullet_point"
    REMOVE_BULLET_POINT = "remove_bullet_point"
    MODIFY_BULLET_POINT = "modify_bullet_point"
    REORDER_BULLET_POINTS = "reorder_bullet_points"
    
    # Content Operations
    ADD_PARAGRAPH = "add_paragraph"
    DELETE_PARAGRAPH = "delete_paragraph"
    MOVE_PARAGRAPH = "move_paragraph"
    SPLIT_PARAGRAPH = "split_paragraph"
    MERGE_PARAGRAPHS = "merge_paragraphs"
    
    # Document Structure
    CHANGE_TITLE = "change_title"
    ADD_HEADING = "add_heading"
    MODIFY_HEADING = "modify_heading"
    RESTRUCTURE_CONTENT = "restructure_content"
    
    # Page Operations
    SWAP_PAGES = "swap_pages"
    EXTRACT_PAGES = "extract_pages"
    REMOVE_PAGES = "remove_pages"
    ROTATE_PAGES = "rotate_pages"
    
    # Image Operations
    RESIZE_IMAGES = "resize_images"
    ADD_IMAGE = "add_image"
    REMOVE_IMAGE = "remove_image"
    
    # Advanced Operations
    MERGE_DOCUMENTS = "merge_documents"
    SPLIT_DOCUMENT = "split_document"
    ADD_WATERMARK = "add_watermark"
    HIGHLIGHT_TEXT = "highlight_text"
    ADD_ANNOTATION = "add_annotation"
class ModificationRequest(BaseModel):
    document_id: str
    command: str
    user_id: Optional[str] = None

class ModificationResponse(BaseModel):
    status: str
    preview_url: Optional[str] = None
    progress: int = 0
    message: str
    changes: List[str] = []

class DocumentSession(BaseModel):
    document_id: str
    user_id: Optional[str] = None
    original_url: str
    temp_file_path: Optional[str] = None
    modifications: List[str] = []
    is_modified: bool = False

class DocumentModification(BaseModel):
    action_type: CommandType
    parameters: Dict[str, Any]
    description: str
    timestamp: Optional[str] = None
    status: str = "pending"

class AgentAction(BaseModel):
    action_type: CommandType
    parameters: Dict[str, Any]
    description: str