# DocumentGenie AI Agent Implementation Guide
## FastAPI + LangGraph + Real-time PDF Modification

This guide provides step-by-step instructions to build an agentic AI system that can modify PDF documents in real-time using natural language commands.

## 🏗️ Architecture Overview

```
User Command → FastAPI → LangGraph Agent → PDF Processor → WebSocket → Frontend
```

## 📋 Prerequisites

1. **Python 3.8+**
2. **FastAPI** - Web framework
3. **LangGraph** - Agent orchestration
4. **OpenAI API** or **Local LLM** - Language model
5. **PDF Processing Libraries** - PyPDF2, reportlab, fitz
6. **WebSocket** - Real-time communication

## 🚀 Step-by-Step Implementation

### Step 1: Install Dependencies

```bash
cd backend
pip install fastapi uvicorn websockets
pip install langgraph langchain langchain-openai
pip install PyPDF2 reportlab pymupdf
pip install python-multipart aiofiles
pip install supabase python-dotenv
pip install nltk spacy pillow opencv-python
pip install pdfplumber tabula-py camelot-py
pip install fuzzywuzzy python-levenshtein
pip install beautifulsoup4 lxml
```

Update `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
langgraph==0.0.40
langchain==0.1.0
langchain-openai==0.0.5
PyPDF2==3.0.1
reportlab==4.0.7
pymupdf==1.23.8
python-multipart==0.0.6
aiofiles==23.2.1
supabase==2.0.2
python-dotenv==1.0.0
nltk==3.8.1
spacy==3.7.2
pillow==10.0.1
opencv-python==4.8.1
pdfplumber==0.10.3
tabula-py==2.8.2
camelot-py==0.11.0
fuzzywuzzy==0.18.0
python-levenshtein==0.21.1
beautifulsoup4==4.12.2
lxml==4.9.3
```

### Step 2: Environment Setup

Create `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Step 3: Project Structure

```
backend/
├── main.py                 # FastAPI app
├── agents/
│   ├── __init__.py
│   ├── document_agent.py   # LangGraph agent
│   └── tools.py           # PDF processing tools
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic models
├── services/
│   ├── __init__.py
│   ├── pdf_service.py     # PDF operations
│   ├── websocket_service.py # Real-time updates
│   └── supabase_service.py # Database operations
├── utils/
│   ├── __init__.py
│   └── temp_storage.py    # Temporary file management
└── requirements.txt
```

### Step 4: Create Pydantic Models

**`models/schemas.py`**
```python
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
    user_id: str

class ModificationResponse(BaseModel):
    status: str
    preview_url: Optional[str] = None
    progress: int = 0
    message: str
    changes: List[str] = []

class DocumentSession(BaseModel):
    document_id: str
    user_id: str
    original_url: str
    temp_file_path: Optional[str] = None
    modifications: List[str] = []
    is_modified: bool = False

class AgentAction(BaseModel):
    action_type: CommandType
    parameters: Dict[str, Any]
    description: str
```

### Step 5: Comprehensive PDF Processing Service

**`services/pdf_service.py`**
```python
import PyPDF2
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import tempfile
import os
import re
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import json
import pdfplumber
import cv2
import numpy as np
from fuzzywuzzy import fuzz, process

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class ComprehensivePDFProcessor:
    """
    A comprehensive PDF processor that can handle ANY type of PDF manipulation request.
    This includes text modifications, paragraph operations, bullet point changes,
    content insertion/deletion, formatting, and structural changes.
    """
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.styles = getSampleStyleSheet()
    
    def load_pdf(self, file_path: str) -> fitz.Document:
        """Load PDF document"""
        return fitz.open(file_path)
    
    def save_pdf(self, doc: fitz.Document, output_path: str) -> str:
        """Save PDF document"""
        doc.save(output_path)
        return output_path
    
    def analyze_pdf_structure(self, pdf_path: str) -> Dict[str, Any]:
        """Comprehensive PDF analysis to understand document structure"""
        doc = fitz.open(pdf_path)
        analysis = {
            "page_count": len(doc),
            "metadata": doc.metadata,
            "size": os.path.getsize(pdf_path),
            "pages": [],
            "text_blocks": [],
            "images": [],
            "fonts": set(),
            "paragraphs": [],
            "bullet_points": [],
            "headings": [],
            "tables": []
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_info = {
                "page_number": page_num,
                "width": page.rect.width,
                "height": page.rect.height,
                "text_blocks": [],
                "images": [],
                "annotations": []
            }
            
            # Extract text blocks with positioning
            blocks = page.get_text("dict")
            for block in blocks["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_block = {
                                "text": span["text"],
                                "bbox": span["bbox"],
                                "font": span["font"],
                                "size": span["size"],
                                "flags": span["flags"]
                            }
                            page_info["text_blocks"].append(text_block)
                            analysis["fonts"].add(span["font"])
            
            # Extract images
            image_list = page.get_images()
            for img in image_list:
                page_info["images"].append({
                    "xref": img[0],
                    "bbox": page.get_image_bbox(img[0]) if hasattr(page, 'get_image_bbox') else None
                })
            
            analysis["pages"].append(page_info)
        
        # Analyze text structure
        full_text = self.extract_text(pdf_path)
        analysis["paragraphs"] = self._identify_paragraphs(full_text["full_text"])
        analysis["bullet_points"] = self._identify_bullet_points(full_text["full_text"])
        analysis["headings"] = self._identify_headings(analysis["pages"])
        analysis["tables"] = self._extract_tables(pdf_path)
        
        doc.close()
        analysis["fonts"] = list(analysis["fonts"])
        return analysis
    
    def extract_text(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> Dict[str, Any]:
        """Extract text with detailed structure and formatting information"""
        doc = fitz.open(pdf_path)
        text_data = {
            "full_text": "",
            "pages": {},
            "paragraphs": [],
            "sentences": [],
            "words": [],
            "formatting_map": {}  # Maps text to its formatting properties
        }
        
        pages_to_process = page_numbers if page_numbers else range(len(doc))
        
        for page_num in pages_to_process:
            if page_num < len(doc):
                page = doc[page_num]
                page_text = page.get_text()
                
                # Extract text with formatting information
                blocks = page.get_text("dict")
                formatting_info = self._extract_formatting_info(blocks)
                
                text_data["pages"][page_num] = {
                    "text": page_text,
                    "paragraphs": page_text.split('\n\n'),
                    "lines": page_text.split('\n'),
                    "formatting": formatting_info
                }
                text_data["full_text"] += page_text + "\n"
                
                # Store formatting map for each text segment
                for text_segment, format_info in formatting_info.items():
                    text_data["formatting_map"][text_segment] = format_info
        
        # Tokenize text
        text_data["sentences"] = sent_tokenize(text_data["full_text"])
        text_data["words"] = word_tokenize(text_data["full_text"])
        text_data["paragraphs"] = [p.strip() for p in text_data["full_text"].split('\n\n') if p.strip()]
        
        doc.close()
        return text_data
    
    def _extract_formatting_info(self, blocks: Dict) -> Dict[str, Dict]:
        """Extract formatting information for each text segment"""
        formatting_map = {}
        
        for block in blocks.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            formatting_map[text] = {
                                "font": span.get("font", ""),
                                "size": span.get("size", 12),
                                "flags": span.get("flags", 0),
                                "color": span.get("color", 0),
                                "bbox": span.get("bbox", []),
                                "is_bold": bool(span.get("flags", 0) & 2**4),
                                "is_italic": bool(span.get("flags", 0) & 2**1),
                                "is_superscript": bool(span.get("flags", 0) & 2**0),
                                "is_subscript": bool(span.get("flags", 0) & 2**2)
                            }
        
        return formatting_map
    
    def _get_text_formatting(self, pdf_path: str, text: str) -> Dict[str, Any]:
        """Get formatting properties for specific text"""
        doc = fitz.open(pdf_path)
        formatting = {
            "font": "helv",
            "size": 12,
            "color": 0,
            "flags": 0
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_instances = page.search_for(text)
            
            if text_instances:
                # Get the formatting of the first instance
                blocks = page.get_text("dict")
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                if text in span["text"]:
                                    formatting = {
                                        "font": span.get("font", "helv"),
                                        "size": span.get("size", 12),
                                        "color": span.get("color", 0),
                                        "flags": span.get("flags", 0)
                                    }
                                    doc.close()
                                    return formatting
        
        doc.close()
        return formatting
    
    # COMPREHENSIVE TEXT MANIPULATION METHODS WITH FONT PRESERVATION
    def replace_text(self, pdf_path: str, old_text: str, new_text: str, page_numbers: Optional[List[int]] = None, preserve_formatting: bool = True) -> str:
        """Advanced text replacement with font style preservation and fuzzy matching"""
        doc = fitz.open(pdf_path)
        pages_to_process = page_numbers if page_numbers else range(len(doc))
        
        for page_num in pages_to_process:
            if page_num < len(doc):
                page = doc[page_num]
                
                # Get original formatting if preservation is enabled
                original_formatting = None
                if preserve_formatting:
                    original_formatting = self._get_text_formatting(pdf_path, old_text)
                
                # Direct text search
                text_instances = page.search_for(old_text, quads=True)
                
                # Fuzzy matching for similar text
                page_text = page.get_text()
                words = page_text.split()
                matches = process.extract(old_text, words, scorer=fuzz.ratio, limit=5)
                
                for match, score in matches:
                    if score > 80:  # High similarity threshold
                        fuzzy_instances = page.search_for(match, quads=True)
                        text_instances.extend(fuzzy_instances)
                
                # Replace all instances with preserved formatting
                for inst in text_instances:
                    if preserve_formatting and original_formatting:
                        # Use original formatting for replacement
                        self._replace_text_with_formatting(page, inst, new_text, original_formatting)
                    else:
                        # Standard replacement without formatting preservation
                        page.add_redact_annot(inst, new_text)
                
                page.apply_redactions()
        
        temp_path = os.path.join(self.temp_dir, f"text_replaced_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        return temp_path
    
    def _replace_text_with_formatting(self, page: fitz.Page, text_rect: fitz.Rect, new_text: str, formatting: Dict[str, Any]):
        """Replace text while preserving original font style and formatting"""
        # Remove the old text
        page.add_redact_annot(text_rect, "")
        page.apply_redactions()
        
        # Insert new text with preserved formatting
        font_name = formatting.get("font", "helv")
        font_size = formatting.get("size", 12)
        color = formatting.get("color", 0)
        flags = formatting.get("flags", 0)
        
        # Convert color from int to RGB if needed
        if isinstance(color, int):
            color = self._int_to_rgb(color)
        
        # Insert text with preserved formatting
        try:
            page.insert_text(
                (text_rect.x0, text_rect.y1 - 2),  # Position slightly above bottom of rect
                new_text,
                fontname=font_name,
                fontsize=font_size,
                color=color
            )
        except:
            # Fallback to default formatting if font issues occur
            page.insert_text(
                (text_rect.x0, text_rect.y1 - 2),
                new_text,
                fontsize=font_size
            )
    
    def _int_to_rgb(self, color_int: int) -> Tuple[float, float, float]:
        """Convert integer color to RGB tuple"""
        if color_int == 0:
            return (0, 0, 0)  # Black
        
        # Extract RGB components from integer
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        
        # Normalize to 0-1 range
        return (r/255.0, g/255.0, b/255.0)
    
    def modify_paragraph(self, pdf_path: str, paragraph_identifier: str, new_content: str, operation: str = "replace", preserve_formatting: bool = True) -> str:
        """Modify specific paragraphs with font style preservation"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            paragraphs = page_text.split('\n\n')
            
            for paragraph in paragraphs:
                if self._paragraph_matches(paragraph, paragraph_identifier):
                    # Get original paragraph formatting
                    original_formatting = None
                    if preserve_formatting:
                        original_formatting = self._get_paragraph_formatting(pdf_path, paragraph)
                    
                    if operation == "replace":
                        self._replace_paragraph_with_formatting(page, paragraph, new_content, original_formatting)
                    elif operation == "delete":
                        self._replace_paragraph_with_formatting(page, paragraph, "", original_formatting)
                    elif operation == "modify":
                        modified_content = self._modify_paragraph_content(paragraph, new_content)
                        self._replace_paragraph_with_formatting(page, paragraph, modified_content, original_formatting)
        
        temp_path = os.path.join(self.temp_dir, f"paragraph_modified_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        return temp_path
    
    def _get_paragraph_formatting(self, pdf_path: str, paragraph: str) -> Dict[str, Any]:
        """Get formatting properties for a paragraph (uses first sentence formatting)"""
        sentences = sent_tokenize(paragraph)
        if sentences:
            return self._get_text_formatting(pdf_path, sentences[0][:50])  # Use first 50 chars of first sentence
        return self._get_text_formatting(pdf_path, paragraph[:50])
    
    def _replace_paragraph_with_formatting(self, page: fitz.Page, old_paragraph: str, new_paragraph: str, formatting: Optional[Dict[str, Any]]):
        """Replace paragraph while preserving original formatting"""
        # Find paragraph instances
        paragraph_words = old_paragraph.split()[:5]  # Use first 5 words to find paragraph
        search_text = " ".join(paragraph_words)
        text_instances = page.search_for(search_text)
        
        for inst in text_instances:
            if formatting:
                self._replace_text_with_formatting(page, inst, new_paragraph, formatting)
            else:
                page.add_redact_annot(inst, new_paragraph)
    
    def modify_sentence(self, pdf_path: str, sentence_identifier: str, new_sentence: str, operation: str = "replace", preserve_formatting: bool = True) -> str:
        """Modify specific sentences with font style preservation"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            sentences = sent_tokenize(page_text)
            
            for sentence in sentences:
                if self._sentence_matches(sentence, sentence_identifier):
                    # Get original sentence formatting
                    original_formatting = None
                    if preserve_formatting:
                        original_formatting = self._get_text_formatting(pdf_path, sentence[:50])
                    
                    if operation == "replace":
                        self._replace_sentence_with_formatting(page, sentence, new_sentence, original_formatting)
                    elif operation == "delete":
                        self._replace_sentence_with_formatting(page, sentence, "", original_formatting)
                    elif operation == "modify":
                        modified_sentence = self._modify_sentence_content(sentence, new_sentence)
                        self._replace_sentence_with_formatting(page, sentence, modified_sentence, original_formatting)
        
        temp_path = os.path.join(self.temp_dir, f"sentence_modified_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        return temp_path
    
    def _replace_sentence_with_formatting(self, page: fitz.Page, old_sentence: str, new_sentence: str, formatting: Optional[Dict[str, Any]]):
        """Replace sentence while preserving original formatting"""
        # Find sentence instances using first few words
        sentence_words = old_sentence.split()[:3]  # Use first 3 words to find sentence
        search_text = " ".join(sentence_words)
        text_instances = page.search_for(search_text)
        
        for inst in text_instances:
            if formatting:
                self._replace_text_with_formatting(page, inst, new_sentence, formatting)
            else:
                page.add_redact_annot(inst, new_sentence)
    
    def modify_bullet_points(self, pdf_path: str, operation: str, **kwargs) -> str:
        """Comprehensive bullet point manipulation"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            if operation == "convert_to_numbered":
                modified_text = self._convert_bullets_to_numbers(page_text)
                self._replace_page_content(page, modified_text)
            elif operation == "convert_to_bullets":
                modified_text = self._convert_numbers_to_bullets(page_text)
                self._replace_page_content(page, modified_text)
            elif operation == "add_bullet":
                bullet_text = kwargs.get("bullet_text", "")
                position = kwargs.get("position", "end")
                modified_text = self._add_bullet_point(page_text, bullet_text, position)
                self._replace_page_content(page, modified_text)
            elif operation == "remove_bullet":
                bullet_identifier = kwargs.get("bullet_identifier", "")
                modified_text = self._remove_bullet_point(page_text, bullet_identifier)
                self._replace_page_content(page, modified_text)
            elif operation == "modify_bullet":
                old_bullet = kwargs.get("old_bullet", "")
                new_bullet = kwargs.get("new_bullet", "")
                modified_text = self._modify_bullet_point(page_text, old_bullet, new_bullet)
                self._replace_page_content(page, modified_text)
            elif operation == "reorder_bullets":
                new_order = kwargs.get("new_order", [])
                modified_text = self._reorder_bullet_points(page_text, new_order)
                self._replace_page_content(page, modified_text)
        
        temp_path = os.path.join(self.temp_dir, f"bullets_modified_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        return temp_path
    
    def add_content(self, pdf_path: str, content: str, location: str, preserve_formatting: bool = True, **kwargs) -> str:
        """Add content at specific locations with font style matching"""
        doc = fitz.open(pdf_path)
        
        # Get surrounding text formatting for context-aware insertion
        surrounding_formatting = None
        if preserve_formatting:
            surrounding_formatting = self._get_surrounding_formatting(doc, location, **kwargs)
        
        if location == "beginning":
            self._add_content_at_beginning(doc, content, surrounding_formatting)
        elif location == "end":
            self._add_content_at_end(doc, content, surrounding_formatting)
        elif location == "after_paragraph":
            paragraph_id = kwargs.get("paragraph_id", "")
            self._add_content_after_paragraph(doc, content, paragraph_id, surrounding_formatting)
        elif location == "before_paragraph":
            paragraph_id = kwargs.get("paragraph_id", "")
            self._add_content_before_paragraph(doc, content, paragraph_id, surrounding_formatting)
        elif location == "page":
            page_num = kwargs.get("page_number", 0)
            x = kwargs.get("x", 100)
            y = kwargs.get("y", 100)
            self._add_content_to_page(doc, content, page_num, x, y, surrounding_formatting)
        elif location == "after_heading":
            heading_text = kwargs.get("heading_text", "")
            self._add_content_after_heading(doc, content, heading_text, surrounding_formatting)
        
        temp_path = os.path.join(self.temp_dir, f"content_added_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        return temp_path
    
    def _get_surrounding_formatting(self, doc: fitz.Document, location: str, **kwargs) -> Dict[str, Any]:
        """Get formatting from surrounding text for context-aware insertion"""
        default_formatting = {
            "font": "helv",
            "size": 12,
            "color": 0,
            "flags": 0
        }
        
        try:
            if location == "after_paragraph" or location == "before_paragraph":
                paragraph_id = kwargs.get("paragraph_id", "")
                if paragraph_id:
                    # Get formatting from the target paragraph
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        page_text = page.get_text()
                        if paragraph_id.lower() in page_text.lower():
                            return self._get_text_formatting_from_page(page, paragraph_id)
            
            elif location == "after_heading":
                heading_text = kwargs.get("heading_text", "")
                if heading_text:
                    # Get formatting from the heading
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        page_text = page.get_text()
                        if heading_text.lower() in page_text.lower():
                            return self._get_text_formatting_from_page(page, heading_text)
            
            elif location == "beginning" or location == "end":
                # Use formatting from first/last paragraph
                page_num = 0 if location == "beginning" else len(doc) - 1
                if page_num < len(doc):
                    page = doc[page_num]
                    page_text = page.get_text()
                    paragraphs = page_text.split('\n\n')
                    if paragraphs:
                        target_paragraph = paragraphs[0] if location == "beginning" else paragraphs[-1]
                        return self._get_text_formatting_from_page(page, target_paragraph[:50])
        
        except Exception:
            pass
        
        return default_formatting
    
    def _get_text_formatting_from_page(self, page: fitz.Page, text: str) -> Dict[str, Any]:
        """Get formatting from specific text on a page"""
        blocks = page.get_text("dict")
        for block in blocks.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if text.lower() in span["text"].lower():
                            return {
                                "font": span.get("font", "helv"),
                                "size": span.get("size", 12),
                                "color": span.get("color", 0),
                                "flags": span.get("flags", 0)
                            }
        
        return {
            "font": "helv",
            "size": 12,
            "color": 0,
            "flags": 0
        }
    
    def delete_content(self, pdf_path: str, content_identifier: str, deletion_type: str = "exact") -> str:
        """Delete content with various identification methods"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            if deletion_type == "exact":
                text_instances = page.search_for(content_identifier)
                for inst in text_instances:
                    page.add_redact_annot(inst, "")
            elif deletion_type == "paragraph":
                page_text = page.get_text()
                paragraphs = page_text.split('\n\n')
                for paragraph in paragraphs:
                    if content_identifier.lower() in paragraph.lower():
                        self._replace_paragraph_in_page(page, paragraph, "")
            elif deletion_type == "sentence":
                page_text = page.get_text()
                sentences = sent_tokenize(page_text)
                for sentence in sentences:
                    if content_identifier.lower() in sentence.lower():
                        self._replace_text_in_page(page, sentence, "")
            elif deletion_type == "section":
                self._delete_section(page, content_identifier)
            elif deletion_type == "line":
                self._delete_line_containing(page, content_identifier)
            
            page.apply_redactions()
        
        temp_path = os.path.join(self.temp_dir, f"content_deleted_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        return temp_path
    
    # HELPER METHODS FOR COMPREHENSIVE PDF MANIPULATION
    def _identify_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """Identify and analyze paragraphs"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        result = []
        for i, para in enumerate(paragraphs):
            result.append({
                "index": i,
                "text": para,
                "word_count": len(para.split()),
                "sentence_count": len(sent_tokenize(para)),
                "is_heading": self._is_heading(para),
                "has_bullets": self._has_bullet_points(para)
            })
        return result
    
    def _identify_bullet_points(self, text: str) -> List[Dict[str, Any]]:
        """Identify bullet points and lists"""
        lines = text.split('\n')
        bullet_points = []
        
        bullet_patterns = [
            r'^\s*[•·▪▫‣⁃]\s+',  # Unicode bullets
            r'^\s*[-*]\s+',       # Dash/asterisk bullets
            r'^\s*\d+\.\s+',      # Numbered lists
            r'^\s*[a-zA-Z]\.\s+', # Lettered lists
            r'^\s*[ivxlcdm]+\.\s+' # Roman numerals
        ]
        
        for i, line in enumerate(lines):
            for pattern in bullet_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    bullet_points.append({
                        "line_number": i,
                        "text": line.strip(),
                        "type": self._get_bullet_type(line),
                        "level": len(line) - len(line.lstrip())
                    })
                    break
        
        return bullet_points
    
    def _identify_headings(self, pages: List[Dict]) -> List[Dict[str, Any]]:
        """Identify headings based on font size and formatting"""
        headings = []
        
        for page in pages:
            for block in page.get("text_blocks", []):
                if block.get("size", 0) > 14 or block.get("flags", 0) & 2**4:
                    text = block.get("text", "").strip()
                    if text and len(text) < 100:
                        headings.append({
                            "text": text,
                            "page": page.get("page_number", 0),
                            "font_size": block.get("size", 0),
                            "is_bold": bool(block.get("flags", 0) & 2**4)
                        })
        
        return headings
    
    def _extract_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF using pdfplumber"""
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table_num, table in enumerate(page_tables):
                        tables.append({
                            "page": page_num,
                            "table_index": table_num,
                            "data": table,
                            "bbox": page.within_bbox(page.bbox).extract_tables()[table_num] if page.extract_tables() else None
                        })
        except Exception as e:
            print(f"Error extracting tables: {e}")
        
        return tables
```

### Step 6: LangGraph Agent Implementation

**`agents/tools.py`**
```python
from langchain.tools import BaseTool
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from services.pdf_service import PDFProcessor
import json

# Input schemas for all tools
class AnalyzePDFInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file to analyze")

class ExtractTextInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page_numbers: Optional[List[int]] = Field(default=None, description="Specific pages to extract text from (optional)")

class ReplaceTextInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    old_text: str = Field(description="Text to replace")
    new_text: str = Field(description="New text to insert")
    page_numbers: Optional[List[int]] = Field(default=None, description="Specific pages to modify (optional)")

class AddTextInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    text: str = Field(description="Text to add")
    page_number: int = Field(description="Page number to add text to")
    x: float = Field(description="X coordinate for text placement")
    y: float = Field(description="Y coordinate for text placement")
    font_size: Optional[int] = Field(default=12, description="Font size")

class RemoveTextInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    text_to_remove: str = Field(description="Text to remove from the document")
    page_numbers: Optional[List[int]] = Field(default=None, description="Specific pages to modify (optional)")

class ChangeTitleInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    new_title: str = Field(description="New title for the document")

class SwapPagesInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page1: int = Field(description="First page number (0-indexed)")
    page2: int = Field(description="Second page number (0-indexed)")

class ResizeImagesInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    scale_factor: float = Field(description="Scale factor for resizing (e.g., 0.5 for 50%, 2.0 for 200%)")

class ExtractPagesInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page_numbers: List[int] = Field(description="List of page numbers to extract (0-indexed)")

class RotatePagesInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page_numbers: List[int] = Field(description="List of page numbers to rotate (0-indexed)")
    rotation: int = Field(description="Rotation angle in degrees (90, 180, 270)")

class AddAnnotationInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page_number: int = Field(description="Page number to add annotation to")
    annotation_text: str = Field(description="Text of the annotation")
    x: float = Field(description="X coordinate for annotation")
    y: float = Field(description="Y coordinate for annotation")

class HighlightTextInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    text_to_highlight: str = Field(description="Text to highlight")
    page_numbers: Optional[List[int]] = Field(default=None, description="Specific pages to search (optional)")

class AddWatermarkInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    watermark_text: str = Field(description="Text for the watermark")
    opacity: Optional[float] = Field(default=0.3, description="Watermark opacity (0.0 to 1.0)")

class RemovePagesInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page_numbers: List[int] = Field(description="List of page numbers to remove (0-indexed)")

class SplitPDFInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    split_points: List[int] = Field(description="Page numbers where to split the document")

class MergePDFsInput(BaseModel):
    pdf_paths: List[str] = Field(description="List of PDF file paths to merge")
    output_name: Optional[str] = Field(default="merged_document.pdf", description="Name for the merged document")

# Comprehensive PDF Tools
class AnalyzePDFTool(BaseTool):
    name = "analyze_pdf"
    description = "Analyze PDF structure, content, and metadata to understand the document"
    args_schema: Type[BaseModel] = AnalyzePDFInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str) -> str:
        analysis = self.pdf_processor.analyze_pdf_structure(pdf_path)
        return json.dumps(analysis, indent=2)

class ExtractTextTool(BaseTool):
    name = "extract_text"
    description = "Extract text content from PDF pages"
    args_schema: Type[BaseModel] = ExtractTextInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> str:
        text_content = self.pdf_processor.extract_text(pdf_path, page_numbers)
        return json.dumps(text_content, indent=2)

class ReplaceTextTool(BaseTool):
    name = "replace_text"
    description = "Replace specific text in the PDF document"
    args_schema: Type[BaseModel] = ReplaceTextInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, old_text: str, new_text: str, page_numbers: Optional[List[int]] = None) -> str:
        return self.pdf_processor.replace_text(pdf_path, old_text, new_text, page_numbers)

class AddTextTool(BaseTool):
    name = "add_text"
    description = "Add new text to specific locations in the PDF"
    args_schema: Type[BaseModel] = AddTextInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, text: str, page_number: int, x: float, y: float, font_size: int = 12) -> str:
        return self.pdf_processor.add_text(pdf_path, text, page_number, x, y, font_size)

class RemoveTextTool(BaseTool):
    name = "remove_text"
    description = "Remove specific text from the PDF document"
    args_schema: Type[BaseModel] = RemoveTextInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, text_to_remove: str, page_numbers: Optional[List[int]] = None) -> str:
        return self.pdf_processor.remove_text(pdf_path, text_to_remove, page_numbers)

class ChangeTitleTool(BaseTool):
    name = "change_title"
    description = "Change the title of the PDF document"
    args_schema: Type[BaseModel] = ChangeTitleInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, new_title: str) -> str:
        return self.pdf_processor.change_title(pdf_path, new_title)

class SwapPagesTool(BaseTool):
    name = "swap_pages"
    description = "Swap the positions of two pages in the PDF"
    args_schema: Type[BaseModel] = SwapPagesInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, page1: int, page2: int) -> str:
        return self.pdf_processor.swap_pages(pdf_path, page1, page2)

class ResizeImagesTool(BaseTool):
    name = "resize_images"
    description = "Resize all images in the PDF by a scale factor"
    args_schema: Type[BaseModel] = ResizeImagesInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, scale_factor: float) -> str:
        return self.pdf_processor.resize_images(pdf_path, scale_factor)

class ExtractPagesTool(BaseTool):
    name = "extract_pages"
    description = "Extract specific pages to create a new PDF"
    args_schema: Type[BaseModel] = ExtractPagesInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, page_numbers: List[int]) -> str:
        return self.pdf_processor.extract_pages(pdf_path, page_numbers)

class RotatePagesTool(BaseTool):
    name = "rotate_pages"
    description = "Rotate specific pages by a given angle"
    args_schema: Type[BaseModel] = RotatePagesInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, page_numbers: List[int], rotation: int) -> str:
        return self.pdf_processor.rotate_pages(pdf_path, page_numbers, rotation)

class AddAnnotationTool(BaseTool):
    name = "add_annotation"
    description = "Add text annotations to specific locations in the PDF"
    args_schema: Type[BaseModel] = AddAnnotationInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, page_number: int, annotation_text: str, x: float, y: float) -> str:
        return self.pdf_processor.add_annotation(pdf_path, page_number, annotation_text, x, y)

class HighlightTextTool(BaseTool):
    name = "highlight_text"
    description = "Highlight specific text in the PDF document"
    args_schema: Type[BaseModel] = HighlightTextInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, text_to_highlight: str, page_numbers: Optional[List[int]] = None) -> str:
        return self.pdf_processor.highlight_text(pdf_path, text_to_highlight, page_numbers)

class AddWatermarkTool(BaseTool):
    name = "add_watermark"
    description = "Add a watermark to all pages of the PDF"
    args_schema: Type[BaseModel] = AddWatermarkInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, watermark_text: str, opacity: float = 0.3) -> str:
        return self.pdf_processor.add_watermark(pdf_path, watermark_text, opacity)

class RemovePagesTool(BaseTool):
    name = "remove_pages"
    description = "Remove specific pages from the PDF document"
    args_schema: Type[BaseModel] = RemovePagesInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, page_numbers: List[int]) -> str:
        return self.pdf_processor.remove_pages(pdf_path, page_numbers)

class SplitPDFTool(BaseTool):
    name = "split_pdf"
    description = "Split PDF into multiple documents at specified page numbers"
    args_schema: Type[BaseModel] = SplitPDFInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, split_points: List[int]) -> str:
        return self.pdf_processor.split_pdf(pdf_path, split_points)

class MergePDFsTool(BaseTool):
    name = "merge_pdfs"
    description = "Merge multiple PDF documents into one"
    args_schema: Type[BaseModel] = MergePDFsInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_paths: List[str], output_name: str = "merged_document.pdf") -> str:
        return self.pdf_processor.merge_pdfs(pdf_paths, output_name)
```

**`agents/document_agent.py`**
```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Any, Optional
import json
import re
from agents.tools import (
    AnalyzePDFTool, ExtractTextTool, ReplaceTextTool, ChangeTitleTool,
    SwapPagesTool, ResizeImagesTool, ExtractPagesTool, AddTextTool,
    RemoveTextTool, HighlightTextTool, AddAnnotationTool, RotatePagesTool,
    MergePDFsTool, SplitPDFTool, AddWatermarkTool, RemovePagesTool
)

class DocumentAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0.1
        )
        
        # Initialize comprehensive PDF tools
        self.tools = [
            AnalyzePDFTool(),
            ExtractTextTool(),
            ReplaceTextTool(),
            ChangeTitleTool(),
            SwapPagesTool(),
            ResizeImagesTool(),
            ExtractPagesTool(),
            AddTextTool(),
            RemoveTextTool(),
            HighlightTextTool(),
            AddAnnotationTool(),
            RotatePagesTool(),
            MergePDFsTool(),
            SplitPDFTool(),
            AddWatermarkTool(),
            RemovePagesTool()
        ]
        
        # Create ReAct agent
        self.agent = self._create_react_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=20,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    def _create_react_agent(self):
        """Create ReAct agent with comprehensive PDF modification capabilities"""
        
        react_prompt = PromptTemplate.from_template("""
You are an expert PDF document modification agent capable of handling ANY user request for PDF manipulation. You can understand natural language commands and execute complex document modifications.

Your comprehensive capabilities include:

TEXT MANIPULATION:
- Replace any text, word, phrase, sentence, or paragraph
- Modify specific sentences within paragraphs
- Delete any text content (words, sentences, paragraphs, sections)
- Add new text at any location in the document
- Change text formatting (bold, italic, font size, color)
- Fix typos and grammar errors

PARAGRAPH OPERATIONS:
- Add new paragraphs anywhere in the document
- Delete specific paragraphs by content or position
- Move paragraphs to different locations
- Split long paragraphs into multiple parts
- Merge multiple paragraphs into one
- Rewrite paragraph content completely

BULLET POINT & LIST MANAGEMENT:
- Convert bullet points to numbered lists and vice versa
- Add new bullet points at any position
- Remove specific bullet points
- Modify existing bullet point text
- Reorder bullet points
- Change bullet point styles and formatting
- Convert lists to regular paragraphs

CONTENT RESTRUCTURING:
- Reorder sections and content blocks
- Move content between pages
- Group related content together
- Split sections into multiple parts
- Reorganize document flow and structure

DOCUMENT STRUCTURE:
- Change document title and metadata
- Add, modify, or remove headings
- Create new sections with headings
- Restructure document hierarchy

PAGE OPERATIONS:
- Add, remove, or reorder pages
- Rotate pages in any direction
- Extract specific pages to new documents
- Merge content from multiple pages

ADVANCED FEATURES:
- Add watermarks, annotations, and highlights
- Insert images and resize existing ones
- Merge multiple documents
- Split documents at specific points
- Apply consistent formatting across the document

NATURAL LANGUAGE UNDERSTANDING:
The agent can interpret requests like:
- "Change this line to say something different"
- "Delete the third paragraph on page 2"
- "Add a bullet point about customer service"
- "Move the conclusion before the recommendations"
- "Make all headings bold and larger"
- "Convert the numbered list to bullet points"
- "Add a new section about pricing"
- "Remove all mentions of the old company name"

IMPORTANT INSTRUCTIONS:
1. ALWAYS start by analyzing the PDF structure to understand the content
2. Break complex requests into logical steps
3. Use multiple tools sequentially for complex modifications
4. Verify changes by re-analyzing the document
5. Handle ambiguous requests by making reasonable assumptions
6. Be thorough and precise in executing user commands
7. Can handle ANY modification request - no matter how complex or specific

Available tools: {tools}

Use the following format:

Question: the input question/command you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Examples of complex modifications you can handle:
- "Change this line to say [new content]" → Find specific line, replace with new text
- "Delete the paragraph about pricing" → Locate paragraph by content, remove entirely
- "Add a bullet point about customer support" → Find bullet list, insert new point
- "Move the conclusion before the introduction" → Extract sections, reorder content
- "Convert all bullet points to numbered lists" → Find bullets, convert to numbers
- "Make the title bigger and bold" → Locate title, apply formatting
- "Remove all mentions of 'old company name'" → Search and delete all instances
- "Split this long paragraph into two shorter ones" → Break paragraph at logical point
- "Add a new section called 'Benefits'" → Insert heading and content
- "Change every instance of 'client' to 'customer'" → Global text replacement
- "Delete the third sentence in the first paragraph" → Precise sentence removal
- "Add 'Important:' before the warning text" → Insert text at specific location
- "Reorder the bullet points alphabetically" → Sort list items
- "Merge the two short paragraphs into one" → Combine paragraph content

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")
        
        return create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_prompt
        )
    
    def process_command(self, pdf_path: str, user_command: str, progress_callback=None) -> dict:
        """Process a user command using ReAct agent"""
        try:
            # Prepare input with PDF path context
            agent_input = f"""
PDF File Path: {pdf_path}
User Request: {user_command}

Please analyze the PDF and perform the requested modifications. Use as many tools as needed to complete the task thoroughly.
"""
            
            # Execute agent
            result = self.agent_executor.invoke({
                "input": agent_input,
                "pdf_path": pdf_path
            })
            
            # Extract intermediate steps for progress tracking
            steps = result.get("intermediate_steps", [])
            
            return {
                "success": True,
                "result_path": self._extract_final_pdf_path(steps),
                "progress": 100,
                "error": None,
                "messages": [result["output"]],
                "steps": [{"action": step[0].tool, "input": step[0].tool_input, "output": step[1]} for step in steps],
                "reasoning": result["output"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "result_path": None,
                "progress": 0,
                "error": str(e),
                "messages": [f"Agent execution failed: {str(e)}"],
                "steps": [],
                "reasoning": None
            }
    
    def _extract_final_pdf_path(self, steps: List) -> Optional[str]:
        """Extract the final modified PDF path from agent steps"""
        # Look for the last tool that returned a file path
        for step in reversed(steps):
            if len(step) >= 2:
                output = step[1]
                if isinstance(output, str) and output.endswith('.pdf'):
                    return output
        return None
    
    async def process_command_streaming(self, pdf_path: str, user_command: str, progress_callback=None):
        """Process command with streaming progress updates"""
        try:
            agent_input = f"""
PDF File Path: {pdf_path}
User Request: {user_command}

Please analyze the PDF and perform the requested modifications step by step.
"""
            
            # Stream agent execution
            step_count = 0
            async for step in self.agent_executor.astream({"input": agent_input, "pdf_path": pdf_path}):
                step_count += 1
                
                if progress_callback:
                    progress = min(90, step_count * 10)  # Cap at 90% until completion
                    await progress_callback({
                        "type": "progress",
                        "progress": progress,
                        "message": f"Executing step {step_count}...",
                        "step": step
                    })
            
            if progress_callback:
                await progress_callback({
                    "type": "complete",
                    "progress": 100,
                    "message": "Document modification completed successfully"
                })
                
        except Exception as e:
            if progress_callback:
                await progress_callback({
                    "type": "error",
                    "progress": 0,
                    "message": f"Error: {str(e)}"
                })
```

### Step 7: WebSocket Service for Real-time Updates

**`services/websocket_service.py`**
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, document_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, document_id: str):
        if document_id in self.active_connections:
            self.active_connections[document_id].remove(websocket)
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_document(self, message: dict, document_id: str):
        if document_id in self.active_connections:
            for connection in self.active_connections[document_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # Remove broken connections
                    self.active_connections[document_id].remove(connection)

manager = ConnectionManager()
```

### Step 8: Temporary Storage Management

**`utils/temp_storage.py`**
```python
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
```

### Step 9: Updated FastAPI Main Application

**`main.py`**
```python
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
from services.supabase_service import download_document_from_supabase

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

# Initialize agent
agent = DocumentAgent(openai_api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
async def root():
    return {"message": "DocumentGenie AI Agent API"}

@app.post("/api/document/session/init")
async def init_session(request: dict):
    """Initialize a document modification session"""
    document_id = request["document_id"]
    original_url = request["original_url"]
    
    # Download document from Supabase
    local_file_path = await download_document_from_supabase(original_url)
    
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
        # Process with agent
        result = agent.process_command(session["temp_file_path"], command)
        
        if result["success"]:
            # Update session
            temp_storage.update_session(document_id, result["result_path"], command)
            
            # Send completion update
            await manager.broadcast_to_document({
                "type": "modification_complete",
                "progress": 100,
                "preview_url": f"/api/temp-preview/{document_id}",
                "message": "Modification completed successfully"
            }, document_id)
            
            return ModificationResponse(
                status="success",
                preview_url=f"/api/temp-preview/{document_id}",
                progress=100,
                message="Modification completed",
                changes=[command]
            )
        else:
            await manager.broadcast_to_document({
                "type": "error",
                "progress": 0,
                "message": f"Error: {result['error']}"
            }, document_id)
            
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        await manager.broadcast_to_document({
            "type": "error",
            "progress": 0,
            "message": f"Unexpected error: {str(e)}"
        }, document_id)
        
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
    
    # Upload modified file to Supabase (replace original)
    # Implementation depends on your Supabase setup
    
    # Clean up session
    temp_storage.cleanup_session(document_id)
    
    return {"status": "saved"}

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
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await manager.send_personal_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

### Step 10: Frontend Integration

Update your frontend to connect to the WebSocket and handle real-time updates:

```javascript
// In your document viewer component
useEffect(() => {
    // WebSocket connection
    const ws = new WebSocket(`ws://localhost:8000/ws/document/${params.id}`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
            case 'progress':
                setModificationProgress(data.progress);
                break;
            case 'modification_complete':
                setPreviewPdfUrl(data.preview_url + `?t=${Date.now()}`);
                setIsModified(true);
                setModificationProgress(0);
                break;
            case 'error':
                console.error('Modification error:', data.message);
                setModificationProgress(0);
                break;
        }
    };
    
    return () => ws.close();
}, [params.id]);
```

### Step 11: Run the Application

```bash
# Terminal 1: Start FastAPI backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Next.js frontend
cd frontend
npm run dev
```

## 🎯 Testing the Agent

1. **Upload a PDF** through your frontend
2. **Open document viewer** 
3. **Send commands** like:
   - "Change the title to 'My New Document'"
   - "Swap page 1 and page 3"
   - "Replace 'old text' with 'new text'"
4. **Watch real-time updates** in the PDF viewer
5. **Save or discard** changes

## 🔧 Advanced Features to Add

1. **Multi-step operations**: "Extract pages 1-3, then change title"
2. **Image processing**: "Resize all images to 50%"
3. **OCR integration**: "Extract text from images"
4. **Batch operations**: "Apply same changes to multiple documents"
5. **Undo/Redo**: Track modification history
6. **Collaboration**: Multiple users editing same document

## 🚨 Error Handling & Monitoring

- Add comprehensive logging
- Implement retry mechanisms
- Monitor agent performance
- Add rate limiting
- Implement user authentication

This implementation provides a solid foundation for your AI-powered document modification system with real-time updates!
