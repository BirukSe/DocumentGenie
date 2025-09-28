from langchain.tools import BaseTool
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from services.pdf_service import PDFProcessor
import fitz  # PyMuPDF
import io
import json
import os
from reportlab.pdfgen import canvas

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
    preserve_formatting: Optional[bool] = Field(default=True, description="Whether to preserve original font formatting")
    fuzzy_match: Optional[bool] = Field(default=True, description="Whether to use fuzzy matching for text identification")
    page_numbers: Optional[List[int]] = Field(default=None, description="Specific pages to modify (optional)")

class ModifyParagraphInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    paragraph_identifier: str = Field(description="Text to identify the paragraph to modify")
    new_content: str = Field(description="New content for the paragraph")
    operation: Optional[str] = Field(default="replace", description="Operation: replace, delete, or modify")
    preserve_formatting: Optional[bool] = Field(default=True, description="Whether to preserve original font formatting")

class AddContentInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    content: str = Field(description="Content to add")
    location: str = Field(description="Location: beginning, end, after_paragraph, page")
    preserve_formatting: Optional[bool] = Field(default=True, description="Whether to match surrounding font formatting")
    paragraph_id: Optional[str] = Field(default=None, description="Paragraph identifier for after_paragraph location")
    page_number: Optional[int] = Field(default=None, description="Page number for page location")
    x: Optional[float] = Field(default=None, description="X coordinate for page location")
    y: Optional[float] = Field(default=None, description="Y coordinate for page location")

class GetTextFormattingInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    text_sample: str = Field(description="Sample text to analyze formatting for")

class ModifySentenceInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    sentence_identifier: str = Field(description="Text to identify the sentence to modify")
    new_sentence: str = Field(description="New sentence content")
    operation: Optional[str] = Field(default="replace", description="Operation: replace, delete, or modify")
    preserve_formatting: Optional[bool] = Field(default=True, description="Whether to preserve original font formatting")

class BulletPointInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    operation: str = Field(description="Operation: convert_to_numbered, convert_to_bullets, add_bullet, remove_bullet, reorder_bullets")
    bullet_text: Optional[str] = Field(default=None, description="Text for add/remove operations")
    new_order: Optional[List[str]] = Field(default=None, description="New order for reorder operation")

class DocumentStructureInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    operation: str = Field(description="Operation: add_heading, modify_heading, add_section, restructure")
    content: Optional[str] = Field(default=None, description="Content for the operation")
    heading_level: Optional[int] = Field(default=1, description="Heading level (1-6)")
    location: Optional[str] = Field(default=None, description="Location for insertion")

class FontAnalysisInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    analysis_type: str = Field(description="Type: font_usage, color_analysis, size_distribution, style_consistency")

class FuzzySearchInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    search_text: str = Field(description="Text to search for with fuzzy matching")
    threshold: Optional[int] = Field(default=80, description="Fuzzy match threshold (0-100)")

class BatchOperationInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    operations: List[Dict[str, Any]] = Field(description="List of operations to perform in batch")
    preserve_formatting: Optional[bool] = Field(default=True, description="Whether to preserve formatting across operations")

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
    current_title: str = Field(description="Current title text to be replaced")
    new_title: str = Field(description="New title text to replace with")
    pdf_path: Optional[str] = Field(default=None, description="Path to the PDF file (optional)")
    
    @classmethod
    def parse_raw(cls, raw: str, **kwargs):
        # If input is already a dict (from JSON), use it directly
        if isinstance(raw, dict):
            return cls(**raw)
            
        # Clean the input string
        raw = raw.strip()
        
        # Try to parse as JSON first
        if raw.startswith('{') and raw.endswith('}'):
            try:
                import json
                data = json.loads(raw)
                return cls(**data)
            except json.JSONDecodeError:
                pass
        
        # Handle quoted strings with various separators
        import re
        
        # Try to find quoted strings first
        quoted_matches = re.findall(r'["\'](.*?)["\']', raw)
        if len(quoted_matches) >= 2:
            return cls(
                current_title=quoted_matches[0].strip(),
                new_title=quoted_matches[1].strip()
            )
            
        # Try to split by common separators
        for sep in [',', ' to ', ' -> ']:
            if sep in raw:
                parts = [p.strip('\'" ') for p in raw.split(sep, 1)]
                if len(parts) == 2:
                    return cls(
                        current_title=parts[0],
                        new_title=parts[1]
                    )
        
        # If we get here, try to split by whitespace
        parts = raw.split()
        if len(parts) >= 2:
            return cls(
                current_title=parts[0],
                new_title=' '.join(parts[1:])
            )
            
        # If we still can't parse, raise a validation error
        raise ValueError(
            "Could not parse input. Please use one of these formats:\n"
            "1. change_title \"current\" \"new\"\n"
            "2. change_title 'current' to 'new'\n"
            "3. change_title 'current', 'new'\n"
            "4. change_title 'current' -> 'new'\n"
            '5. change_title {\"current_title\":\"current\",\"new_title\":\"new\"}'
        )

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
    watermark_text: str = Field(default="DOCUMENT", description="Text for the watermark (default: 'DOCUMENT')")
    opacity: Optional[float] = Field(default=0.3, description="Watermark opacity (0.0 to 1.0)")

class RemovePagesInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    page_numbers: List[int] = Field(description="List of page numbers to remove (0-indexed)")

class SplitPDFInput(BaseModel):
    pdf_path: str = Field(description="Path to the PDF file")
    split_points: List[int] = Field(description="Page numbers where to split the document")

class ChangeBackgroundColorInput(BaseModel):
    file_path: str = Field(default=None, description="Path to the PDF file")
    pdf_path: str = Field(default=None, description="[Deprecated] Use file_path instead. Path to the PDF file")
    color: str = Field(default="yellow", 
                     description="Background color in hex format (e.g., '#FFFF00' for yellow) or color name (e.g., 'yellow')")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0, 
                         description="Opacity of the background color (0.0 to 1.0, default: 1.0)")
    
    class Config:
        extra = "allow"  # Allow extra fields to be passed

class ChangeBackgroundColorTool(BaseTool):
    name: str = "change_background_color"
    description: str = "Change the background color of all pages in the PDF"
    args_schema: Type[BaseModel] = ChangeBackgroundColorInput
    
    def _run(self, *args, **kwargs) -> str:
        """
        Change the background color of all pages in the PDF.
        
        Args:
            pdf_path: Path to the PDF file (deprecated, use file_path instead)
            file_path: Path to the PDF file
            color: Background color in hex format (e.g., '#FFFF00' for yellow) or color name (e.g., 'yellow')
            opacity: Opacity of the background color (0.0 to 1.0, default: 0.3)
            
        Returns:
            str: Path to the modified PDF file or error message
        """
        try:
            # Handle JSON string input (common from API calls)
            if len(args) == 1 and isinstance(args[0], str) and args[0].startswith('{') and args[0].endswith('}'):
                import json
                try:
                    input_data = json.loads(args[0])
                    kwargs.update(input_data)
                    args = []
                except json.JSONDecodeError:
                    pass
            
            # Handle both direct arguments and dictionary input
            if len(args) == 1 and isinstance(args[0], str):
                # If a single string is provided, treat it as the file path
                input_path = args[0]
                color = 'yellow'  # Default color
                opacity = 0.3     # Default opacity
            elif len(args) > 1:
                # If multiple args, assume they're in order: file_path, color, opacity
                input_path = args[0]
                color = args[1] if len(args) > 1 else 'yellow'
                try:
                    opacity = float(args[2]) if len(args) > 2 else 0.3
                except (ValueError, TypeError):
                    opacity = 0.3
            else:
                # Use kwargs
                input_path = kwargs.get('file_path') or kwargs.get('pdf_path')
                color = kwargs.get('color', 'yellow')
                try:
                    opacity = float(kwargs.get('opacity', 0.3))
                except (ValueError, TypeError):
                    opacity = 0.3
            
            if not input_path:
                return "Error: No file path provided. Please provide either file_path or pdf_path."
                
            # If input_path is a dict (from JSON input), extract the path
            if isinstance(input_path, dict):
                input_path = input_path.get('file_path') or input_path.get('pdf_path')
                if not input_path:
                    return "Error: Invalid input format. Expected file_path or pdf_path in the input."
            
            # Clean up the input path if it's wrapped in quotes or has extra spaces
            input_path = str(input_path).strip('"\'').strip()
            
            # Ensure the file exists
            if not os.path.exists(input_path):
                return f"Error: File not found: {input_path}"
                
            # Validate color format
            if not color.startswith('#'):
                # Try to convert color name to hex
                try:
                    import webcolors
                    color = webcolors.name_to_hex(color)
                except (ValueError, AttributeError):
                    # If not a named color, assume it's a hex code without #
                    if not color.startswith('#'):
                        color = f"#{color}"
            
            # Ensure opacity is between 0 and 1
            try:
                opacity = float(opacity)
                opacity = max(0.0, min(1.0, opacity))
            except (ValueError, TypeError):
                opacity = 0.3
            
            # Create output path in the same directory as the input file
            input_dir = os.path.dirname(input_path)
            input_filename = os.path.basename(input_path)
            output_filename = f"bg_{input_filename}"
            output_path = os.path.join(input_dir, output_filename)
            
            try:
                # Use the PDFProcessor to handle the background color change
                pdf_processor = PDFProcessor()
                result_path = pdf_processor.change_background_color(
                    input_path=input_path,
                    color=color,
                    opacity=opacity
                )
                
                # Verify the result
                if not result_path or not os.path.exists(result_path):
                    return {
                        "success": False,
                        "error": f"Failed to generate output file at {result_path}",
                        "result_path": None
                    }
                
                # If the result_path is different from our expected output_path, rename it
                if result_path != output_path:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(result_path, output_path)
                    result_path = output_path
                
                return {
                    "success": True,
                    "message": f"Successfully changed background color to {color} with {opacity*100}% opacity",
                    "result_path": result_path,
                    "modified_file": result_path
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Error changing background color: {str(e)}",
                    "result_path": None
                }
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"Error changing background color: {str(e)}\n\nDetails:\n{error_details}"

class MergePDFsInput(BaseModel):
    pdf_paths: List[str] = Field(description="List of PDF file paths to merge")
    output_name: Optional[str] = Field(default="merged_document.pdf", description="Name for the merged document")

# Enhanced PDF Tools with Font Preservation
class AnalyzePDFTool(BaseTool):
    name: str = "analyze_pdf"
    description: str = "Comprehensive PDF analysis including structure, fonts, formatting, and content"
    args_schema: Type[BaseModel] = AnalyzePDFInput
    
    def _run(self, *args, **kwargs) -> str:
        try:
            # Handle both direct arguments and dictionary input
            if len(args) == 1 and isinstance(args[0], str):
                # If a single string is provided, treat it as the file path
                pdf_path = args[0]
            elif len(args) > 1:
                # If multiple args, assume they're in order: pdf_path
                pdf_path = args[0]
            else:
                # Use kwargs
                pdf_path = kwargs.get('pdf_path')
            
            if not pdf_path:
                return "Error: No PDF path provided. Please provide a valid path to the PDF file."
                
            if isinstance(pdf_path, dict):
                # Handle case where input is a JSON string that was parsed to dict
                pdf_path = pdf_path.get('pdf_path')
                if not pdf_path:
                    return "Error: Invalid input format. Expected 'pdf_path' in the input."
            
            # Clean up the input path if it's wrapped in quotes or has extra spaces
            pdf_path = str(pdf_path).strip('\'"').strip()
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                return f"Error: File not found: {pdf_path}"
            
            # Process the PDF
            pdf_processor = PDFProcessor()
            analysis = pdf_processor.analyze_document(pdf_path)
            
            # Format the output for better readability
            formatted_analysis = {
                "page_count": analysis.get("pages", 0),
                "fonts_used": analysis.get("fonts_used", []),
                "colors_used": analysis.get("colors_used", []),
                "has_images": analysis.get("has_images", False),
                "has_tables": analysis.get("has_tables", False),
                "headings": [
                    {
                        "text": h.get("text", "")[:100] + ("..." if len(h.get("text", "")) > 100 else ""),
                        "page": h.get("page", 0),
                        "font_size": h.get("size", 0)
                    }
                    for h in analysis.get("headings", [])[:10]  # Limit to first 10 headings
                ]
            }
            
            return json.dumps(formatted_analysis, indent=2)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return f"Error analyzing PDF: {str(e)}\n\nDetails:\n{error_details}"

class ExtractTextTool(BaseTool):
    name: str = "extract_text"
    description: str = "Extract text content from PDF pages with formatting analysis"
    args_schema: Type[BaseModel] = ExtractTextInput
    
    def _run(self, pdf_path: str, page_numbers: Optional[List[int]] = None) -> str:
        try:
            pdf_processor = PDFProcessor()
            doc = pdf_processor.load_pdf(pdf_path)
            
            if page_numbers is None:
                text = ""
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text += f"--- Page {page_num + 1} ---\n"
                    text += page.get_text() + "\n\n"
            else:
                text = ""
                for page_num in page_numbers:
                    if 0 <= page_num - 1 < len(doc):
                        page = doc[page_num - 1]
                        text += f"--- Page {page_num} ---\n"
                        text += page.get_text() + "\n\n"
            
            doc.close()
            return f"Extracted text:\n{text[:2000]}..." if len(text) > 2000 else f"Extracted text:\n{text}"
        except Exception as e:
            return f"Error extracting text: {str(e)}"

class ReplaceTextTool(BaseTool):
    name: str = "replace_text"
    description: str = "Replace specific text in the PDF document with font style preservation and fuzzy matching"
    args_schema: Type[BaseModel] = ReplaceTextInput
    
    def _run(self, pdf_path: str, old_text: str, new_text: str, preserve_formatting: bool = True, 
             fuzzy_match: bool = True, page_numbers: Optional[List[int]] = None) -> str:
        try:
            pdf_processor = PDFProcessor()
            result_path = pdf_processor.replace_text_with_formatting(
                pdf_path, old_text, new_text, preserve_formatting, fuzzy_match
            )
            return f"Text replacement completed with font preservation. Modified document: {result_path}"
        except Exception as e:
            return f"Error replacing text: {str(e)}"

class AddTextTool(BaseTool):
    name: str = "add_text"
    description: str = "Add new text to specific locations in the PDF"
    args_schema: Type[BaseModel] = AddTextInput
    
    def _run(self, pdf_path: str, text: str, page_number: int, x: float, y: float, font_size: int = 12) -> str:
        try:
            pdf_processor = PDFProcessor()
            result_path = pdf_processor.add_content(
                pdf_path, text, "page", preserve_formatting=True,
                page_number=page_number-1, x=x, y=y
            )
            return f"Text added successfully. Modified document: {result_path}"
        except Exception as e:
            return f"Error adding text: {str(e)}"

class RemoveTextTool(BaseTool):
    name: str = "remove_text"
    description: str = "Remove specific text from the PDF document"
    args_schema: Type[BaseModel] = RemoveTextInput
    
    def _run(self, pdf_path: str, text_to_remove: str, page_numbers: Optional[List[int]] = None) -> str:
        try:
            pdf_processor = PDFProcessor()
            result_path = pdf_processor.replace_text_with_formatting(
                pdf_path, text_to_remove, "", preserve_formatting=True, fuzzy_match=True
            )
            return f"Text removed successfully. Modified document: {result_path}"
        except Exception as e:
            return f"Error removing text: {str(e)}"

class ChangeTitleTool(BaseTool):
    name: str = "change_title"
    description: str = "Change the visible title text in the document's header"
    args_schema: Type[BaseModel] = ChangeTitleInput
    
    def _run(self, *args, **kwargs) -> str:
        doc = None
        try:
            # Handle different input formats
            if len(args) >= 2:
                current_title = str(args[0])
                new_title = str(args[1])
                pdf_path = kwargs.get('pdf_path')
            elif 'input' in kwargs:
                input_str = str(kwargs['input']).strip()
                try:
                    if input_str.startswith('{') and input_str.endswith('}'):
                        import json
                        data = json.loads(input_str)
                        current_title = str(data.get('current_title', '')).strip('\'" ')
                        new_title = str(data.get('new_title', '')).strip('\'" ')
                        pdf_path = data.get('pdf_path') or kwargs.get('pdf_path')
                    else:
                        parsed = self.args_schema.parse_raw(f'"{input_str}"')
                        current_title = parsed.current_title
                        new_title = parsed.new_title
                        pdf_path = parsed.pdf_path or kwargs.get('pdf_path')
                except Exception as e:
                    error_msg = (
                        f"Error parsing input: {str(e)}\n"
                        "Please use one of these formats:\n"
                        "1. change_title \"current\" \"new\"\n"
                        "2. change_title 'current' to 'new'\n"
                        "3. change_title 'current', 'new'\n"
                        "4. change_title 'current' -> 'new'\n"
                        '5. change_title {\"current_title\":\"current\",\"new_title\":\"new\"}'
                    )
                    return error_msg
            else:
                return "Error: Please provide both current and new titles"
            
            # Validate inputs
            current_title = current_title.strip('\'" ')
            new_title = new_title.strip('\'" ')
            
            if not current_title or not new_title:
                return "Error: Both current title and new title are required"
                
            # Get the document path
            document_path = pdf_path or kwargs.get('document_path')
            if not document_path:
                return "Error: Document path is required"
            
            # Initialize PDF processor
            pdf_processor = PDFProcessor()
            
            try:
                # Load the document
                doc = pdf_processor.load_document(document_path)
                if not doc:
                    return "Error: Failed to load document"
                
                # Search and replace text in each page
                found = False
                for page in doc:
                    text = page.get_text()
                    if current_title in text:
                        found = True
                        text = text.replace(current_title, new_title)
                        page.set_text(text)
                
                if not found:
                    # If title not found, try to identify it from the document structure
                    analysis = pdf_processor.analyze_document(document_path)
                    title_candidates = []
                    for block in analysis.get('text_blocks', []):
                        if block.get('page_number') == 1:  # Look for title in first page
                            title_candidates.append({
                                'text': block.get('text', '').strip(),
                                'size': block.get('size', 0),
                                'bbox': block.get('bbox', (0, 0, 0, 0))
                            })
                    
                    if title_candidates:
                        # Sort by size (largest first) and vertical position (top first)
                        title_candidates.sort(key=lambda x: (-x['size'], x['bbox'][1]))
                        current_title = title_candidates[0]['text']
                        return self._update_title(document_path, current_title, new_title)
                    
                    return f"Error: Could not find title '{current_title}' in the document"
                
                # Save the document
                output_path = kwargs.get('output_path', document_path)
                doc.save(output_path)
                return f"Successfully changed title from '{current_title}' to '{new_title}'"
                
            except Exception as e:
                return f"Error processing document: {str(e)}"
                
        except Exception as e:
            return f"Error in change_title: {str(e)}"
            
        finally:
            if doc is not None:
                doc.close()
                
    def _update_title(self, pdf_path: str, old_title: str, new_title: str) -> str:
        """Internal method to handle the title update logic"""
        try:
            pdf_processor = PDFProcessor()
            
            # Use replace_text_with_formatting to update the title
            result_path = pdf_processor.replace_text_with_formatting(
                pdf_path=pdf_path,
                old_text=old_title,
                new_text=new_title,
                preserve_formatting=True,
                fuzzy_match=True
            )
            
            # Verify the change was made
            doc = fitz.open(result_path)
            try:
                page = doc[0]
                text_instances = page.search_for(old_title, hit_max=1)
                if text_instances:  # If old title is still found
                    return f"Error: Failed to update the title. The text might be part of an image or vector graphic."
                
                return f"Successfully changed title from '{old_title}' to '{new_title}'. Modified document: {result_path}"
            finally:
                doc.close()
                
        except Exception as e:
            import traceback
            return f"Error updating title: {str(e)}\n{traceback.format_exc()}"

class SwapPagesTool(BaseTool):
    name: str = "swap_pages"
    description: str = "Swap the positions of two pages in the PDF"
    args_schema: Type[BaseModel] = SwapPagesInput
    
    def _run(self, pdf_path: str, page1: int, page2: int) -> str:
        try:
            pdf_processor = PDFProcessor()
            doc = pdf_processor.load_pdf(pdf_path)
            doc.move_page(page1, page2)
            result_path = os.path.join(pdf_processor.temp_dir, f"swapped_{os.path.basename(pdf_path)}")
            doc.save(result_path)
            doc.close()
            return f"Pages swapped successfully. Modified document: {result_path}"
        except Exception as e:
            return f"Error swapping pages: {str(e)}"

class ResizeImagesTool(BaseTool):
    name: str = "resize_images"
    description: str = "Resize all images in the PDF by a scale factor"
    args_schema: Type[BaseModel] = ResizeImagesInput
    
    def _run(self, pdf_path: str, scale_factor: float) -> str:
        pdf_processor = PDFProcessor()
        return pdf_processor.resize_images(pdf_path, scale_factor)

class ExtractPagesTool(BaseTool):
    name: str = "extract_pages"
    description: str = "Extract specific pages to create a new PDF"
    args_schema: Type[BaseModel] = ExtractPagesInput
    
    def _run(self, pdf_path: str, page_numbers: List[int]) -> str:
        pdf_processor = PDFProcessor()
        return pdf_processor.extract_pages(pdf_path, page_numbers)

class RotatePagesTool(BaseTool):
    name: str = "rotate_pages"
    description: str = "Rotate specific pages by a given angle"
    args_schema: Type[BaseModel] = RotatePagesInput
    
    def _run(self, pdf_path: str, page_numbers: List[int], rotation: int) -> str:
        pdf_processor = PDFProcessor()
        return pdf_processor.rotate_pages(pdf_path, page_numbers, rotation)

class AddAnnotationTool(BaseTool):
    name: str = "add_annotation"
    description: str = "Add text annotations to specific locations in the PDF"
    args_schema: Type[BaseModel] = AddAnnotationInput
    
    def _run(self, pdf_path: str, page_number: int, annotation_text: str, x: float, y: float) -> str:
        pdf_processor = PDFProcessor()
        return pdf_processor.add_annotation(pdf_path, page_number, annotation_text, x, y)

class HighlightTextTool(BaseTool):
    name: str = "highlight_text"
    description: str = "Highlight specific text in the PDF document"
    args_schema: Type[BaseModel] = HighlightTextInput
    
    def _run(self, pdf_path: str, text_to_highlight: str, page_numbers: Optional[List[int]] = None) -> str:
        pdf_processor = PDFProcessor()
        return pdf_processor.highlight_text(pdf_path, text_to_highlight, page_numbers)

class AddWatermarkTool(BaseTool):
    name: str = "add_watermark"
    description: str = "Add a watermark to all pages of the PDF. The watermark will be placed diagonally across each page with the specified text and opacity."
    args_schema: Type[BaseModel] = AddWatermarkInput
    
    def _run(self, pdf_path: str, watermark_text: str = "DOCUMENT", opacity: float = 0.3) -> str:
        """
        Add a watermark to all pages of the PDF.
        
        Args:
            pdf_path: Path to the PDF file to watermark
            watermark_text: Text to use as watermark (default: 'DOCUMENT')
            opacity: Opacity of the watermark (0.0 to 1.0, default: 0.3)
            
        Returns:
            str: Path to the watermarked PDF file
        """
        try:
            pdf_processor = PDFProcessor()
            output_path = pdf_processor.add_watermark(pdf_path, watermark_text, opacity)
            return f"Successfully added watermark to {pdf_path}. Watermarked file saved to: {output_path}"
        except Exception as e:
            return f"Error adding watermark: {str(e)}"
        return pdf_processor.add_watermark(pdf_path, watermark_text, opacity)

class RemovePagesTool(BaseTool):
    name: str = "remove_pages"
    description: str = "Remove specific pages from the PDF document"
    args_schema: Type[BaseModel] = RemovePagesInput
    
    def _run(self, pdf_path: str, page_numbers: List[int]) -> str:
        pdf_processor = PDFProcessor()
        return pdf_processor.remove_pages(pdf_path, page_numbers)

class SplitPDFTool(BaseTool):
    name: str = "split_pdf"
    description: str = "Split PDF into multiple documents at specified page numbers"
    args_schema: Type[BaseModel] = SplitPDFInput
    
    def _run(self, pdf_path: str, split_points: List[int]) -> str:
        pdf_processor = PDFProcessor()
        return pdf_processor.split_pdf(pdf_path, split_points)

class MergePDFsTool(BaseTool):
    name: str = "merge_pdfs"
    description: str = "Merge multiple PDF documents into one"
    args_schema: Type[BaseModel] = MergePDFsInput
    
    def _run(self, pdf_paths: List[str], output_name: str = "merged_document.pdf") -> str:
        try:
            pdf_processor = PDFProcessor()
            merged_doc = pdf_processor.load_pdf(pdf_paths[0])
            for pdf_path in pdf_paths[1:]:
                doc = pdf_processor.load_pdf(pdf_path)
                merged_doc.insert_pdf(doc)
                doc.close()
            
            result_path = os.path.join(pdf_processor.temp_dir, output_name)
            merged_doc.save(result_path)
            merged_doc.close()
            return f"PDFs merged successfully. Output: {result_path}"
        except Exception as e:
            return f"Error merging PDFs: {str(e)}"

# Enhanced PDF Tools for Font Preservation and Advanced Manipulation
class ModifyParagraphTool(BaseTool):
    name: str = "modify_paragraph"
    description: str = "Modify specific paragraphs with font style preservation"
    args_schema: Type[BaseModel] = ModifyParagraphInput
    
    def _run(self, pdf_path: str, paragraph_identifier: str, new_content: str, 
             operation: str = "replace", preserve_formatting: bool = True) -> str:
        try:
            pdf_processor = PDFProcessor()
            result_path = pdf_processor.modify_paragraph(
                pdf_path, paragraph_identifier, new_content, operation, preserve_formatting
            )
            return f"Paragraph {operation} completed with font preservation. Modified document: {result_path}"
        except Exception as e:
            return f"Error modifying paragraph: {str(e)}"

class AddContentTool(BaseTool):
    name: str = "add_content"
    description: str = "Add content at specific locations with font style matching"
    args_schema: Type[BaseModel] = AddContentInput
    
    def _run(self, pdf_path: str, content: str, location: str, preserve_formatting: bool = True,
             paragraph_id: Optional[str] = None, page_number: Optional[int] = None,
             x: Optional[float] = None, y: Optional[float] = None) -> str:
        try:
            kwargs = {}
            if paragraph_id:
                kwargs["paragraph_id"] = paragraph_id
            if page_number is not None:
                kwargs["page_number"] = page_number - 1
            if x is not None:
                kwargs["x"] = x
            if y is not None:
                kwargs["y"] = y
                
            result_path = pdf_processor.add_content(
                pdf_path, content, location, preserve_formatting, **kwargs
            )
            return f"Content added successfully with font matching. Modified document: {result_path}"
        except Exception as e:
            return f"Error adding content: {str(e)}"

class GetTextFormattingTool(BaseTool):
    name: str = "get_text_formatting"
    description: str = "Get formatting properties of specific text for analysis"
    args_schema: Type[BaseModel] = GetTextFormattingInput
    
    def _run(self, pdf_path: str, text_sample: str) -> str:
        try:
            pdf_processor = PDFProcessor()
            formatting = pdf_processor._get_text_formatting(pdf_path, text_sample)
            return json.dumps(formatting, indent=2)
        except Exception as e:
            return f"Error getting text formatting: {str(e)}"

class ModifySentenceTool(BaseTool):
    name: str = "modify_sentence"
    description: str = "Modify specific sentences with font style preservation"
    args_schema: Type[BaseModel] = ModifySentenceInput
    
    def _run(self, pdf_path: str, sentence_identifier: str, new_sentence: str,
             operation: str = "replace", preserve_formatting: bool = True) -> str:
        try:
            pdf_processor = PDFProcessor()
            # Use the replace_text_with_formatting method for sentence modification
            if operation == "replace":
                result_path = pdf_processor.replace_text_with_formatting(
                    pdf_path, sentence_identifier, new_sentence, preserve_formatting, fuzzy_match=True
                )
            elif operation == "delete":
                result_path = pdf_processor.replace_text_with_formatting(
                    pdf_path, sentence_identifier, "", preserve_formatting, fuzzy_match=True
                )
            else:  # modify
                result_path = pdf_processor.replace_text_with_formatting(
                    pdf_path, sentence_identifier, new_sentence, preserve_formatting, fuzzy_match=True
                )
            
            return f"Sentence {operation} completed with font preservation. Modified document: {result_path}"
        except Exception as e:
            return f"Error modifying sentence: {str(e)}"

class FuzzySearchTool(BaseTool):
    name: str = "fuzzy_search"
    description: str = "Search for text using fuzzy matching to find similar content"
    args_schema: Type[BaseModel] = FuzzySearchInput
    
    def _run(self, pdf_path: str, search_text: str, threshold: int = 80) -> str:
        try:
            pdf_processor = PDFProcessor()
            doc = pdf_processor.load_pdf(pdf_path)
            matches = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                # Use the fuzzy matching method from our processor
                best_match = pdf_processor._find_best_fuzzy_match(page_text, search_text, threshold)
                if best_match:
                    matches.append({
                        "page": page_num + 1,
                        "match": best_match,
                        "context": page_text[max(0, page_text.find(best_match) - 50):page_text.find(best_match) + len(best_match) + 50]
                    })
            
            doc.close()
            return json.dumps({"search_text": search_text, "matches": matches}, indent=2)
        except Exception as e:
            return f"Error in fuzzy search: {str(e)}"

class FontAnalysisTool(BaseTool):
    name: str = "font_analysis"
    description: str = "Analyze font usage, colors, and style consistency in the document"
    args_schema: Type[BaseModel] = FontAnalysisInput
    
    def _run(self, pdf_path: str, analysis_type: str) -> str:
        try:
            pdf_processor = PDFProcessor()
            analysis = pdf_processor.analyze_document(pdf_path)
            
            if analysis_type == "font_usage":
                return json.dumps({
                    "fonts_used": analysis["fonts_used"],
                    "total_fonts": len(analysis["fonts_used"]),
                    "recommendation": "Consider standardizing to 1-2 fonts for consistency" if len(analysis["fonts_used"]) > 2 else "Good font consistency"
                }, indent=2)
            
            elif analysis_type == "color_analysis":
                return json.dumps({
                    "colors_used": analysis["colors_used"],
                    "total_colors": len(analysis["colors_used"]),
                    "color_consistency": "Good" if len(analysis["colors_used"]) <= 3 else "Consider reducing color variety"
                }, indent=2)
            
            elif analysis_type == "style_consistency":
                return json.dumps({
                    "headings": len(analysis["headings"]),
                    "bullet_points": len(analysis["bullet_points"]),
                    "fonts": len(analysis["fonts_used"]),
                    "consistency_score": "High" if len(analysis["fonts_used"]) <= 2 else "Medium" if len(analysis["fonts_used"]) <= 4 else "Low"
                }, indent=2)
            
            else:
                return json.dumps(analysis, indent=2)
                
        except Exception as e:
            return f"Error in font analysis: {str(e)}"

class BatchOperationTool(BaseTool):
    name: str = "batch_operation"
    description: str = "Perform multiple PDF operations in sequence with consistent formatting"
    args_schema: Type[BaseModel] = BatchOperationInput
    
    def _run(self, pdf_path: str, operations: List[Dict[str, Any]], preserve_formatting: bool = True) -> str:
        try:
            pdf_processor = PDFProcessor()
            current_path = pdf_path
            results = []
            
            for i, operation in enumerate(operations):
                op_type = operation.get("type")
                
                if op_type == "replace_text":
                    current_path = pdf_processor.replace_text_with_formatting(
                        current_path, operation["old_text"], operation["new_text"], 
                        preserve_formatting, operation.get("fuzzy_match", True)
                    )
                    results.append(f"Step {i+1}: Text replacement completed")
                
                elif op_type == "add_content":
                    current_path = pdf_processor.add_content(
                        current_path, operation["content"], operation["location"], 
                        preserve_formatting, **operation.get("kwargs", {})
                    )
                    results.append(f"Step {i+1}: Content addition completed")
                
                elif op_type == "modify_paragraph":
                    current_path = pdf_processor.modify_paragraph(
                        current_path, operation["paragraph_id"], operation["new_content"],
                        operation.get("operation", "replace"), preserve_formatting
                    )
                    results.append(f"Step {i+1}: Paragraph modification completed")
            
            return json.dumps({
                "final_document": current_path,
                "operations_completed": len(operations),
                "results": results
            }, indent=2)
            
        except Exception as e:
            return f"Error in batch operation: {str(e)}"

# Comprehensive Tool Collection - All Available PDF Manipulation Tools
def get_all_pdf_tools():
    """Get all available PDF manipulation tools with enhanced capabilities"""
    return [
        # Core Tools
        AnalyzePDFTool(),
        ExtractTextTool(),
        ReplaceTextTool(),
        AddTextTool(),
        RemoveTextTool(),
        ChangeTitleTool(),
        
        # Page Manipulation Tools
        SwapPagesTool(),
        ExtractPagesTool(),
        RotatePagesTool(),
        RemovePagesTool(),
        SplitPDFTool(),
        MergePDFsTool(),
        
        # Visual Enhancement Tools
        ResizeImagesTool(),
        AddAnnotationTool(),
        HighlightTextTool(),
        AddWatermarkTool(),
        ChangeBackgroundColorTool(),
        
        # Advanced Text & Content Tools
        ModifyParagraphTool(),
        AddContentTool(),
        GetTextFormattingTool(),
        ModifySentenceTool(),
        FuzzySearchTool(),
        FontAnalysisTool(),
        BatchOperationTool()
    ]

def get_tool_categories():
    """Get tools organized by categories for easier navigation"""
    return {
        "text_manipulation": [
            "replace_text", "add_text", "remove_text", "modify_paragraph", 
            "modify_sentence", "add_content"
        ],
        "font_preservation": [
            "replace_text", "modify_paragraph", "add_content", "modify_sentence",
            "get_text_formatting", "font_analysis"
        ],
        "document_analysis": [
            "analyze_pdf", "extract_text", "fuzzy_search", "font_analysis"
        ],
        "page_operations": [
            "swap_pages", "extract_pages", "rotate_pages", "remove_pages",
            "split_pdf", "merge_pdfs"
        ],
        "visual_enhancements": [
            "resize_images", "add_annotation", "highlight_text", "add_watermark"
        ],
        "advanced_operations": [
            "batch_operation", "fuzzy_search", "font_analysis"
        ]
    }

def get_tool_descriptions():
    """Get detailed descriptions of all available tools"""
    return {
        "analyze_pdf": "Comprehensive PDF analysis including structure, fonts, formatting, and content",
        "extract_text": "Extract text content from PDF pages with formatting analysis",
        "replace_text": "Replace specific text with font style preservation and fuzzy matching",
        "add_text": "Add new text to specific locations in the PDF",
        "remove_text": "Remove specific text from the PDF document",
        "modify_paragraph": "Modify specific paragraphs with font style preservation",
        "add_content": "Add content at specific locations with font style matching",
        "get_text_formatting": "Get formatting properties of specific text for analysis",
        "modify_sentence": "Modify specific sentences with font style preservation",
        "fuzzy_search": "Search for text using fuzzy matching to find similar content",
        "font_analysis": "Analyze font usage, colors, and style consistency in the document",
        "batch_operation": "Perform multiple PDF operations in sequence with consistent formatting",
        "change_title": "Change the title of the PDF document",
        "swap_pages": "Swap the positions of two pages in the PDF",
        "extract_pages": "Extract specific pages to create a new PDF",
        "rotate_pages": "Rotate specific pages by a given angle",
        "remove_pages": "Remove specific pages from the PDF document",
        "split_pdf": "Split PDF into multiple documents at specified page numbers",
        "merge_pdfs": "Merge multiple PDF documents into one",
        "resize_images": "Resize all images in the PDF by a scale factor",
        "add_annotation": "Add text annotations to specific locations in the PDF",
        "highlight_text": "Highlight specific text in the PDF document",
        "add_watermark": "Add a watermark to all pages of the PDF"
    }