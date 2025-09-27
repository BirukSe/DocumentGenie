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
    CHANGE_TITLE = "change_title"
    SWAP_PAGES = "swap_pages"
    RESIZE_IMAGES = "resize_images"
    REPLACE_TEXT = "replace_text"
    EXTRACT_PAGES = "extract_pages"
    MERGE_DOCUMENTS = "merge_documents"

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

### Step 5: PDF Processing Service

**`services/pdf_service.py`**
```python
import PyPDF2
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import tempfile
import os
from typing import Optional, List, Dict, Any

class PDFProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def load_pdf(self, file_path: str) -> fitz.Document:
        """Load PDF document"""
        return fitz.open(file_path)
    
    def save_pdf(self, doc: fitz.Document, output_path: str) -> str:
        """Save PDF document"""
        doc.save(output_path)
        return output_path
    
    def change_title(self, pdf_path: str, new_title: str) -> str:
        """Change PDF title in metadata and first page"""
        doc = fitz.open(pdf_path)
        
        # Update metadata
        metadata = doc.metadata
        metadata['title'] = new_title
        doc.set_metadata(metadata)
        
        # Update first page title (if text exists)
        page = doc[0]
        text_instances = page.search_for("title", quads=True)
        
        for inst in text_instances:
            # Replace text (simplified - you'd need more sophisticated text replacement)
            page.add_redact_annot(inst)
            page.apply_redactions()
        
        # Save to temporary file
        temp_path = os.path.join(self.temp_dir, f"modified_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        
        return temp_path
    
    def swap_pages(self, pdf_path: str, page1: int, page2: int) -> str:
        """Swap two pages in PDF"""
        doc = fitz.open(pdf_path)
        
        if page1 < len(doc) and page2 < len(doc):
            # Create new document with swapped pages
            new_doc = fitz.open()
            
            for i in range(len(doc)):
                if i == page1:
                    new_doc.insert_pdf(doc, from_page=page2, to_page=page2)
                elif i == page2:
                    new_doc.insert_pdf(doc, from_page=page1, to_page=page1)
                else:
                    new_doc.insert_pdf(doc, from_page=i, to_page=i)
            
            temp_path = os.path.join(self.temp_dir, f"swapped_{os.path.basename(pdf_path)}")
            new_doc.save(temp_path)
            new_doc.close()
            doc.close()
            
            return temp_path
        
        return pdf_path
    
    def resize_images(self, pdf_path: str, scale_factor: float) -> str:
        """Resize all images in PDF"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                # Get image
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Process image (resize)
                # This is simplified - you'd use PIL/Pillow for actual resizing
                
        temp_path = os.path.join(self.temp_dir, f"resized_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        
        return temp_path
    
    def replace_text(self, pdf_path: str, old_text: str, new_text: str) -> str:
        """Replace text in PDF"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_instances = page.search_for(old_text)
            
            for inst in text_instances:
                # Add redaction annotation
                page.add_redact_annot(inst, new_text)
            
            # Apply redactions
            page.apply_redactions()
        
        temp_path = os.path.join(self.temp_dir, f"text_replaced_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        
        return temp_path
    
    def extract_pages(self, pdf_path: str, page_numbers: List[int]) -> str:
        """Extract specific pages"""
        doc = fitz.open(pdf_path)
        new_doc = fitz.open()
        
        for page_num in page_numbers:
            if page_num < len(doc):
                new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        temp_path = os.path.join(self.temp_dir, f"extracted_{os.path.basename(pdf_path)}")
        new_doc.save(temp_path)
        new_doc.close()
        doc.close()
        
        return temp_path
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """Get PDF information"""
        doc = fitz.open(pdf_path)
        info = {
            "page_count": len(doc),
            "metadata": doc.metadata,
            "size": os.path.getsize(pdf_path)
        }
        doc.close()
        return info
```

### Step 6: LangGraph Agent Implementation

**`agents/tools.py`**
```python
from langchain.tools import BaseTool
from typing import Type, Optional, List
from pydantic import BaseModel, Field
from services.pdf_service import PDFProcessor

class ChangeTitleInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    new_title: str = Field(description="New title for the document")

class SwapPagesInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page1: int = Field(description="First page number (0-indexed)")
    page2: int = Field(description="Second page number (0-indexed)")

class ReplaceTextInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    old_text: str = Field(description="Text to replace")
    new_text: str = Field(description="New text")

class ChangeTitleTool(BaseTool):
    name = "change_title"
    description = "Change the title of a PDF document"
    args_schema: Type[BaseModel] = ChangeTitleInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, new_title: str) -> str:
        return self.pdf_processor.change_title(pdf_path, new_title)

class SwapPagesTool(BaseTool):
    name = "swap_pages"
    description = "Swap two pages in a PDF document"
    args_schema: Type[BaseModel] = SwapPagesInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, page1: int, page2: int) -> str:
        return self.pdf_processor.swap_pages(pdf_path, page1, page2)

class ReplaceTextTool(BaseTool):
    name = "replace_text"
    description = "Replace text in a PDF document"
    args_schema: Type[BaseModel] = ReplaceTextInput
    
    def __init__(self):
        super().__init__()
        self.pdf_processor = PDFProcessor()
    
    def _run(self, pdf_path: str, old_text: str, new_text: str) -> str:
        return self.pdf_processor.replace_text(pdf_path, old_text, new_text)
```

**`agents/document_agent.py`**
```python
from langgraph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from typing import TypedDict, List, Optional
import json
import re
from agents.tools import ChangeTitleTool, SwapPagesTool, ReplaceTextTool

class AgentState(TypedDict):
    messages: List[str]
    current_pdf_path: str
    user_command: str
    parsed_intent: Optional[dict]
    tool_result: Optional[str]
    progress: int
    error: Optional[str]

class DocumentAgent:
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0
        )
        
        # Initialize tools
        self.tools = {
            "change_title": ChangeTitleTool(),
            "swap_pages": SwapPagesTool(),
            "replace_text": ReplaceTextTool()
        }
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_intent", self._parse_intent)
        workflow.add_node("execute_tool", self._execute_tool)
        workflow.add_node("validate_result", self._validate_result)
        
        # Add edges
        workflow.add_edge("parse_intent", "execute_tool")
        workflow.add_edge("execute_tool", "validate_result")
        workflow.add_edge("validate_result", END)
        
        # Set entry point
        workflow.set_entry_point("parse_intent")
        
        return workflow.compile()
    
    def _parse_intent(self, state: AgentState) -> AgentState:
        """Parse user command and extract intent"""
        system_prompt = """
        You are a PDF document modification assistant. Parse the user command and extract:
        1. Action type (change_title, swap_pages, replace_text, etc.)
        2. Parameters needed for the action
        
        Respond with JSON format:
        {
            "action": "action_name",
            "parameters": {"param1": "value1", "param2": "value2"},
            "confidence": 0.95
        }
        
        Examples:
        - "Change the title to 'New Document'" -> {"action": "change_title", "parameters": {"new_title": "New Document"}}
        - "Swap page 1 and page 3" -> {"action": "swap_pages", "parameters": {"page1": 0, "page2": 2}}
        - "Replace 'old text' with 'new text'" -> {"action": "replace_text", "parameters": {"old_text": "old text", "new_text": "new text"}}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["user_command"])
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            parsed_intent = json.loads(response.content)
            state["parsed_intent"] = parsed_intent
            state["progress"] = 25
        except json.JSONDecodeError:
            state["error"] = "Failed to parse user command"
            state["progress"] = 0
        
        return state
    
    def _execute_tool(self, state: AgentState) -> AgentState:
        """Execute the appropriate tool based on parsed intent"""
        if state.get("error"):
            return state
        
        intent = state["parsed_intent"]
        action = intent["action"]
        parameters = intent["parameters"]
        
        if action not in self.tools:
            state["error"] = f"Unknown action: {action}"
            return state
        
        try:
            tool = self.tools[action]
            # Add pdf_path to parameters
            parameters["pdf_path"] = state["current_pdf_path"]
            
            result = tool._run(**parameters)
            state["tool_result"] = result
            state["progress"] = 75
            
        except Exception as e:
            state["error"] = f"Tool execution failed: {str(e)}"
            state["progress"] = 0
        
        return state
    
    def _validate_result(self, state: AgentState) -> AgentState:
        """Validate the tool result"""
        if state.get("error"):
            return state
        
        if state["tool_result"]:
            state["progress"] = 100
            state["messages"].append(f"Successfully modified document: {state['tool_result']}")
        else:
            state["error"] = "Tool execution produced no result"
            state["progress"] = 0
        
        return state
    
    def process_command(self, pdf_path: str, user_command: str) -> dict:
        """Process a user command"""
        initial_state = AgentState(
            messages=[],
            current_pdf_path=pdf_path,
            user_command=user_command,
            parsed_intent=None,
            tool_result=None,
            progress=0,
            error=None
        )
        
        # Run workflow
        result = self.workflow.invoke(initial_state)
        
        return {
            "success": result["error"] is None,
            "result_path": result.get("tool_result"),
            "progress": result["progress"],
            "error": result.get("error"),
            "messages": result["messages"]
        }
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
