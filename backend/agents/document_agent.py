import os
from typing import Dict, Any, List, Optional
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_groq import ChatGroq
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.base import BaseCallbackHandler
from dotenv import load_dotenv
from services.pdf_service import PDFProcessor
from services.supabase_service import supabase_service
from utils.temp_storage import temp_storage
from langchain_google_genai import ChatGoogleGenerativeAI
from models.schemas import CommandType, DocumentModification
from agents.tools import get_all_pdf_tools, get_tool_categories, get_tool_descriptions
load_dotenv()
class DocumentAgent:
    def __init__(self, websocket_manager=None):
        self.pdf_processor = PDFProcessor()
        self.websocket_manager = websocket_manager
        # Initialize Groq with the latest Llama 4 model
        self.llm = ChatGroq(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1
        )
        # Use comprehensive tool collection with all 23 PDF manipulation tools
        self.tools = get_all_pdf_tools()
        self.tool_categories = get_tool_categories()
        self.tool_descriptions = get_tool_descriptions()
        self.agent = self._create_react_agent()
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get information about all available tools"""
        return {
            "total_tools": len(self.tools),
            "categories": self.tool_categories,
            "descriptions": self.tool_descriptions,
            "tool_names": [tool.name for tool in self.tools]
        }
        
    async def process_command_async(self, document_path: str, command: str, document_id: str) -> Dict[str, Any]:
        """
        Process a document modification command asynchronously.
        
        Args:
            document_path: Path to the document to modify
            command: The modification command from the user
            document_id: ID of the document being modified
            
        Returns:
            Dictionary with the result of the operation
        """
        try:
            # Notify client that processing has started
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_document({
                    "type": "progress",
                    "progress": 20,
                    "message": f"Processing command: {command}"
                }, document_id)
            
            # Process the command using the agent
            result = await self.agent.ainvoke({
                "input": f"Document: {document_path}\nCommand: {command}",
                "document_id": document_id
            })
            
            # Notify client of completion
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_document({
                    "type": "progress",
                    "progress": 90,
                    "message": "Finalizing changes..."
                }, document_id)
            
            # Extract result path from the agent's output if available
            result_output = result.get("output", {})
            if isinstance(result_output, str):
                # If output is a string, use it as the message
                result_message = result_output
                result_path = document_path  # Fallback to original path
            else:
                # If output is a dict, extract message and path
                result_message = result_output.get("message", "Command processed successfully")
                result_path = result_output.get("result_path", result_output.get("modified_file", document_path))
            
            return {
                "success": True,
                "result": result_message,
                "result_path": result_path,
                "document_path": document_path
            }
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_document({
                    "type": "error",
                    "message": error_msg
                }, document_id)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _create_react_agent(self):
        """Create ReAct agent with comprehensive PDF manipulation capabilities"""
        
        # Get tool names for the prompt
        tool_names = [tool.name for tool in self.tools]
        
        react_prompt = PromptTemplate.from_template("""
You are an expert PDF document modification agent with access to 23 comprehensive PDF manipulation tools. You can handle ANY user request for PDF manipulation with precise font style preservation, advanced text processing, and complete document restructuring.

AVAILABLE TOOL CATEGORIES:
• Text Manipulation: replace_text, add_text, remove_text, modify_paragraph, modify_sentence, add_content
• Font Preservation: All text tools preserve formatting by default, get_text_formatting, font_analysis
• Document Analysis: analyze_pdf, extract_text, fuzzy_search, font_analysis
• Page Operations: swap_pages, extract_pages, rotate_pages, remove_pages, split_pdf, merge_pdfs
• Visual Enhancements: resize_images, add_annotation, highlight_text, add_watermark
• Advanced Operations: batch_operation, fuzzy_search, font_analysis

KEY CAPABILITIES:
- Text replacement with exact font style preservation and fuzzy matching
- Paragraph/sentence-level modifications with formatting retention
- Content insertion with automatic font matching to surrounding text
- Comprehensive document analysis (structure, fonts, colors, formatting)
- Batch operations for complex multi-step modifications
- Page manipulation (rotate, extract, merge, split, swap)
- Visual enhancements (annotations, highlights, watermarks)
- Advanced search with fuzzy matching for flexible text identification

FONT PRESERVATION PROTOCOL:
1. ALWAYS preserve original font styles unless explicitly instructed otherwise
2. Use preserve_formatting=true by default for ALL text operations
3. Analyze document formatting FIRST using analyze_pdf tool
4. Match surrounding text formatting when adding new content
5. Use get_text_formatting tool to inspect specific text properties
6. Maintain visual consistency throughout all modifications

WORKFLOW BEST PRACTICES:
1. Start with analyze_pdf to understand document structure and formatting
2. Use extract_text to understand content context when needed
3. Use fuzzy_search for flexible text identification
4. Perform modifications using appropriate tools with font preservation
5. Use batch_operation for complex multi-step processes
6. Always provide clear feedback about modifications made

EXAMPLE COMMANDS YOU CAN HANDLE:
- "Replace all instances of 'ABC Corp' with 'XYZ Industries' keeping original fonts"
- "Add a confidentiality notice at the top of each page matching header font"
- "Convert bullet points in section 3 to numbered list"
- "Merge pages 1-3 from document A with pages 5-7 from document B"
- "Rotate all landscape pages to portrait orientation"
- "Add watermark 'DRAFT' with 30% opacity to all pages"
- "Extract financial data from pages 10-15 and create new document"
- "Highlight all mentions of 'revenue' in yellow"
- "Swap pages 2 and 5, then add page numbers"

{tools}

Use the following format:
Question: the input question/command you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}
""")
        
        # Create the ReAct agent with proper prompt variables
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=react_prompt.partial(
                tools="\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                tool_names=", ".join([tool.name for tool in self.tools])
            )
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
    
    async def process_modification_request(self, request: str, document_path: str, document_id: str) -> Dict[str, Any]:
        """Process natural language PDF modification request with real-time updates"""
        try:
            # Send initial progress update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_document({
                    "type": "agent_thinking",
                    "progress": 20,
                    "message": "Analyzing your request..."
                }, document_id)
            
            # Prepare input for the agent
            agent_input = f"Document path: {document_path}\nDocument ID: {document_id}\nUser request: {request}"
            
            # Send processing update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_document({
                    "type": "agent_processing",
                    "progress": 40,
                    "message": "Processing document modifications..."
                }, document_id)
            
            # Execute the agent
            result = self.agent.invoke({"input": agent_input})
            
            # Extract the result path from the agent's output
            output = result["output"]
            result_path = None
            
            # Try to find the result path in the output
            if isinstance(output, dict):
                result_path = output.get('result_path') or output.get('modified_file')
            elif isinstance(output, str):
                # Try to extract path from string output
                import re
                path_match = re.search(r'saved to:?\s*([^\s\n]+)', output, re.IGNORECASE)
                if path_match and os.path.exists(path_match.group(1)):
                    result_path = path_match.group(1)
            
            # If we have a result path, use it; otherwise use the original document path
            final_path = result_path if result_path and os.path.exists(result_path) else document_path
            
            # Send completion update
            if self.websocket_manager:
                await self.websocket_manager.send_manipulation_complete(
                    document_id=document_id,
                    operation="document_modification",
                    result_path=final_path,
                    preview_url=f"/api/temp-preview/{document_id}"
                )
            
            return {
                "success": True,
                "result": output,
                "result_path": final_path,
                "agent_steps": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            # Send error update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_document({
                    "type": "agent_error",
                    "progress": 0,
                    "message": f"Error: {str(e)}"
                }, document_id)
            
            return {
                "success": False,
                "error": str(e),
                "result": f"Failed to process modification request: {str(e)}"
            }
    
    def get_modification_suggestions(self, document_path: str) -> List[str]:
        """Get intelligent suggestions for document modifications based on analysis"""
        try:
            analysis = self.pdf_processor.analyze_document(document_path)
            
            suggestions = []
            
            # Suggest based on document structure
            if analysis["headings"]:
                suggestions.extend([
                    "Modify heading styles or add new sections",
                    "Restructure document hierarchy",
                    "Add table of contents based on headings"
                ])
            
            if analysis["bullet_points"]:
                suggestions.extend([
                    "Convert bullet points to numbered lists or vice versa",
                    "Reorder bullet points for better flow",
                    "Add sub-bullets for detailed information"
                ])
            
            if len(analysis["fonts_used"]) > 2:
                suggestions.append("Standardize fonts throughout the document for consistency")
            
            if analysis["pages"] > 1:
                suggestions.extend([
                    "Add page numbers or headers/footers",
                    "Insert page breaks for better organization",
                    "Add watermarks to all pages"
                ])
            
            if analysis["has_images"]:
                suggestions.extend([
                    "Resize images for consistent appearance",
                    "Add captions to images",
                    "Optimize image placement"
                ])
            
            # General suggestions based on tool capabilities
            suggestions.extend([
                "Replace company names or contact information with font preservation",
                "Add confidentiality notices matching document style", 
                "Insert new paragraphs or sections with proper formatting",
                "Highlight important terms or phrases",
                "Add annotations for review comments",
                "Extract specific pages to create focused documents",
                "Merge with other related documents",
                "Add digital signatures or form fields",
                "Perform batch text replacements",
                "Analyze and improve font consistency"
            ])
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            return [f"Error generating suggestions: {str(e)}"]
    
    def get_tool_by_category(self, category: str) -> List[str]:
        """Get tools filtered by category"""
        return self.tool_categories.get(category, [])
    
    def execute_batch_operation(self, document_path: str, operations: List[Dict[str, Any]], 
                               document_id: str) -> Dict[str, Any]:
        """Execute multiple operations in sequence with comprehensive error handling"""
        try:
            # Use the batch_operation tool for complex multi-step processes
            batch_request = f"""
            Execute the following batch operations on document: {document_path}
            Operations: {operations}
            Document ID: {document_id}
            
            Please use the batch_operation tool to perform these operations in sequence while preserving formatting consistency.
            """
            
            result = self.agent.invoke({"input": batch_request})
            
            return {
                "success": True,
                "result": result["output"],
                "operations_count": len(operations),
                "agent_steps": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": f"Failed to execute batch operations: {str(e)}"
            }
    
    def analyze_document_comprehensive(self, document_path: str) -> Dict[str, Any]:
        """Perform comprehensive document analysis using multiple tools"""
        try:
            # Use the analyze_pdf tool through the agent
            analysis_request = f"""
            Perform comprehensive analysis of document: {document_path}
            
            Please use the analyze_pdf tool to get detailed information about:
            - Document structure and formatting
            - Font usage and consistency
            - Page layout and content organization
            - Suggestions for improvements
            
            Also use font_analysis tool with analysis_type='style_consistency' for additional insights.
            """
            
            result = self.agent.invoke({"input": analysis_request})
            
            return {
                "success": True,
                "analysis": result["output"],
                "agent_steps": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": f"Failed to analyze document: {str(e)}"
            }
    
    def search_and_replace_advanced(self, document_path: str, search_patterns: List[str], 
                                   replacements: List[str], document_id: str, 
                                   use_fuzzy: bool = True) -> Dict[str, Any]:
        """Advanced search and replace with fuzzy matching and font preservation"""
        try:
            if len(search_patterns) != len(replacements):
                return {
                    "success": False,
                    "error": "Number of search patterns must match number of replacements"
                }
            
            # Create batch operations for multiple replacements
            operations = []
            for search, replace in zip(search_patterns, replacements):
                operations.append({
                    "type": "replace_text",
                    "old_text": search,
                    "new_text": replace,
                    "fuzzy_match": use_fuzzy
                })
            
            return self.execute_batch_operation(document_path, operations, document_id)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": f"Failed to perform advanced search and replace: {str(e)}"
            }