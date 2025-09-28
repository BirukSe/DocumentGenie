import PyPDF2
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import tempfile
import os
import re
from typing import Optional, List, Dict, Any, Tuple
from fuzzywuzzy import fuzz
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class PDFProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def load_pdf(self, file_path: str) -> fitz.Document:
        """Load PDF document"""
        return fitz.open(file_path)
    
    def analyze_document(self, pdf_path: str) -> Dict[str, Any]:
        """Comprehensive document analysis with formatting details"""
        doc = fitz.open(pdf_path)
        analysis = {
            "pages": len(doc),
            "page_details": [],
            "fonts_used": set(),
            "colors_used": set(),
            "has_images": False,
            "has_tables": False,
            "text_blocks": [],
            "paragraphs": [],
            "bullet_points": [],
            "headings": []
        }
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_dict = page.get_text("dict")
            
            page_info = {
                "page_number": page_num + 1,
                "width": page.rect.width,
                "height": page.rect.height,
                "text_blocks": len(page_dict.get("blocks", [])),
                "images": len(page.get_images()),
                "annotations": len(page.annots())
            }
            
            # Extract text with formatting
            for block in page_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            analysis["fonts_used"].add(span.get("font", ""))
                            analysis["colors_used"].add(span.get("color", 0))
                            
                            text = span.get("text", "").strip()
                            if text:
                                # Detect headings (larger font size or bold)
                                if span.get("size", 0) > 14 or span.get("flags", 0) & 2**4:
                                    analysis["headings"].append({
                                        "text": text,
                                        "page": page_num + 1,
                                        "font": span.get("font", ""),
                                        "size": span.get("size", 0)
                                    })
                                
                                # Detect bullet points
                                if re.match(r'^[\u2022\u25E6\u25AA\u25AB\u25CF\u25CB\*\-\+]\s+', text):
                                    analysis["bullet_points"].append({
                                        "text": text,
                                        "page": page_num + 1,
                                        "type": "bullet"
                                    })
                                elif re.match(r'^\d+[\.\)]\s+', text):
                                    analysis["bullet_points"].append({
                                        "text": text,
                                        "page": page_num + 1,
                                        "type": "numbered"
                                    })
            
            if page.get_images():
                analysis["has_images"] = True
            
            analysis["page_details"].append(page_info)
        
        # Convert sets to lists for JSON serialization
        analysis["fonts_used"] = list(analysis["fonts_used"])
        analysis["colors_used"] = list(analysis["colors_used"])
        
        doc.close()
        return analysis
    
    def replace_text_with_formatting(self, pdf_path: str, old_text: str, new_text: str, 
                                   preserve_formatting: bool = True, fuzzy_match: bool = True) -> str:
        """Replace text while preserving original font style"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            if fuzzy_match:
                # Use fuzzy matching for more flexible text replacement
                page_text = page.get_text()
                words = word_tokenize(page_text.lower())
                old_words = word_tokenize(old_text.lower())
                
                # Find best match using sliding window
                best_match = self._find_best_fuzzy_match(page_text, old_text)
                if best_match:
                    old_text = best_match
            
            # Get original formatting before replacement
            original_formatting = None
            if preserve_formatting:
                original_formatting = self._get_text_formatting(pdf_path, old_text)
            
            # Find and replace text instances
            text_instances = page.search_for(old_text)
            for inst in text_instances:
                if original_formatting and preserve_formatting:
                    self._replace_text_with_formatting(page, inst, new_text, original_formatting)
                else:
                    # Standard replacement without formatting preservation
                    page.add_redact_annot(inst, new_text)
                    page.apply_redactions()
        
        temp_path = os.path.join(self.temp_dir, f"text_replaced_{os.path.basename(pdf_path)}")
        doc.save(temp_path)
        doc.close()
        return temp_path
    
    def _get_text_formatting(self, pdf_path: str, text: str) -> Dict[str, Any]:
        """Extract formatting properties from specific text"""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")
            
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if text.lower() in span["text"].lower():
                                formatting = {
                                    "font": span.get("font", "helv"),
                                    "size": span.get("size", 12),
                                    "color": span.get("color", 0),
                                    "flags": span.get("flags", 0),
                                    "bbox": span.get("bbox", [0, 0, 0, 0])
                                }
                                doc.close()
                                return formatting
        
        doc.close()
        # Return default formatting if text not found
        return {
            "font": "helv",
            "size": 12,
            "color": 0,
            "flags": 0,
            "bbox": [0, 0, 0, 0]
        }
    
    def _replace_text_with_formatting(self, page: fitz.Page, rect: fitz.Rect, new_text: str, formatting: Dict[str, Any]):
        """Replace text while applying specific formatting"""
        # Remove old text
        page.add_redact_annot(rect)
        page.apply_redactions()
        
        # Add new text with preserved formatting
        font_name = formatting.get("font", "helv")
        font_size = formatting.get("size", 12)
        color = self._convert_color_to_rgb(formatting.get("color", 0))
        flags = formatting.get("flags", 0)
        
        # Insert new text with formatting
        page.insert_text(
            rect.tl,  # Top-left point
            new_text,
            fontname=font_name,
            fontsize=font_size,
            color=color,
            flags=flags
        )
    
    def _convert_color_to_rgb(self, color_int: int) -> Tuple[float, float, float]:
        """Convert integer color to RGB tuple"""
        if color_int == 0:
            return (0, 0, 0)  # Black
        
        # Extract RGB components from integer
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        
        # Normalize to 0-1 range
        return (r/255.0, g/255.0, b/255.0)
    
    def _find_best_fuzzy_match(self, text: str, target: str, threshold: int = 80) -> Optional[str]:
        """Find best fuzzy match for target text within document text"""
        words = text.split()
        target_words = target.split()
        target_len = len(target_words)
        
        best_match = None
        best_ratio = 0
        
        for i in range(len(words) - target_len + 1):
            candidate = " ".join(words[i:i + target_len])
            ratio = fuzz.ratio(candidate.lower(), target.lower())
            
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = candidate
        
        return best_match
    
    def modify_paragraph(self, pdf_path: str, paragraph_identifier: str, new_content: str, 
                        operation: str = "replace", preserve_formatting: bool = True) -> str:
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
    
    def _paragraph_matches(self, paragraph: str, identifier: str) -> bool:
        """Check if paragraph matches identifier using fuzzy matching"""
        return fuzz.partial_ratio(paragraph.lower(), identifier.lower()) > 70
    
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
                page.apply_redactions()
    
    def _modify_paragraph_content(self, original: str, modification: str) -> str:
        """Intelligently modify paragraph content based on modification instruction"""
        # This is a simplified version - in practice, you might use NLP to understand the modification
        if "add" in modification.lower():
            return original + " " + modification.replace("add", "").strip()
        elif "remove" in modification.lower():
            # Simple removal logic
            return original.replace(modification.replace("remove", "").strip(), "")
        else:
            return modification  # Default to replacement
    
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
        elif location == "page":
            page_num = kwargs.get("page_number", 0)
            x = kwargs.get("x", 100)
            y = kwargs.get("y", 100)
            self._add_content_to_page(doc, content, page_num, x, y, surrounding_formatting)
        
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
            if location == "after_paragraph":
                paragraph_id = kwargs.get("paragraph_id", "")
                if paragraph_id:
                    # Get formatting from the target paragraph
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        page_text = page.get_text()
                        if paragraph_id.lower() in page_text.lower():
                            return self._get_text_formatting_from_page(page, paragraph_id)
            
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
    
    def _add_content_at_beginning(self, doc: fitz.Document, content: str, formatting: Optional[Dict[str, Any]]):
        """Add content at the beginning of the document"""
        if len(doc) > 0:
            page = doc[0]
            # Insert at top of first page
            insert_point = fitz.Point(72, 72)  # 1 inch margins
            
            if formatting:
                page.insert_text(
                    insert_point,
                    content,
                    fontname=formatting.get("font", "helv"),
                    fontsize=formatting.get("size", 12),
                    color=self._convert_color_to_rgb(formatting.get("color", 0))
                )
            else:
                page.insert_text(insert_point, content)
    
    def _add_content_at_end(self, doc: fitz.Document, content: str, formatting: Optional[Dict[str, Any]]):
        """Add content at the end of the document"""
        if len(doc) > 0:
            page = doc[-1]
            # Insert at bottom of last page
            page_rect = page.rect
            insert_point = fitz.Point(72, page_rect.height - 72)  # 1 inch from bottom
            
            if formatting:
                page.insert_text(
                    insert_point,
                    content,
                    fontname=formatting.get("font", "helv"),
                    fontsize=formatting.get("size", 12),
                    color=self._convert_color_to_rgb(formatting.get("color", 0))
                )
            else:
                page.insert_text(insert_point, content)
    
    def _add_content_after_paragraph(self, doc: fitz.Document, content: str, paragraph_id: str, formatting: Optional[Dict[str, Any]]):
        """Add content after a specific paragraph"""
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()
            
            if paragraph_id.lower() in page_text.lower():
                # Find paragraph location and add content after it
                # This is a simplified implementation
                paragraphs = page_text.split('\n\n')
                for i, paragraph in enumerate(paragraphs):
                    if paragraph_id.lower() in paragraph.lower():
                        # Insert content after this paragraph
                        # For simplicity, insert at end of page - in practice, you'd calculate exact position
                        insert_point = fitz.Point(72, 200 + i * 50)  # Rough positioning
                        
                        if formatting:
                            page.insert_text(
                                insert_point,
                                content,
                                fontname=formatting.get("font", "helv"),
                                fontsize=formatting.get("size", 12),
                                color=self._convert_color_to_rgb(formatting.get("color", 0))
                            )
                        else:
                            page.insert_text(insert_point, content)
                        break
    
    def _add_content_to_page(self, doc: fitz.Document, content: str, page_num: int, x: float, y: float, formatting: Optional[Dict[str, Any]]):
        """Add content at specific coordinates on a page"""
        if page_num < len(doc):
            page = doc[page_num]
            insert_point = fitz.Point(x, y)
            
            if formatting:
                page.insert_text(
                    insert_point,
                    content,
                    fontname=formatting.get("font", "helv"),
                    fontsize=formatting.get("size", 12),
                    color=self._convert_color_to_rgb(formatting.get("color", 0))
                )
            else:
                page.insert_text(insert_point, content)
    
    def add_watermark(self, pdf_path: str, watermark_text: str = "DOCUMENT", opacity: float = 0.3) -> str:
        """
        Add a watermark to all pages of the PDF.
        
        Args:
            pdf_path: Path to the input PDF file
            watermark_text: Text to use as watermark (default: 'DOCUMENT')
            opacity: Opacity of the watermark (0.0 to 1.0, default: 0.3)
            
        Returns:
            str: Path to the watermarked PDF file
        """
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get page dimensions
            page_rect = page.rect
            width = page_rect.width
            height = page_rect.height
            
            # Create a new PDF with the watermark
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(width, height))
            
            # Set font and size
            c.setFont("Helvetica-Bold", 60)
            
            # Set fill color to light gray with specified opacity
            c.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)
            
            # Rotate the text
            c.rotate(45)
            
            # Position the text in the center
            text_width = c.stringWidth(watermark_text, "Helvetica-Bold", 60)
            x = (width / 3.5) - (text_width / 2)
            y = height / 3.5
            
            # Add the text
            c.drawString(x, y, watermark_text)
            
            # Save the watermark
            c.save()
            
            # Move to the beginning of the StringIO buffer
            packet.seek(0)
            watermark = fitz.open("pdf", packet.read())
            
            # Get the first page of the watermark
            watermark_page = watermark[0]
            
            # Merge the watermark with the current page
            page.show_pdf_page(page_rect, watermark, 0)
            
            # Clean up
            watermark.close()
        
        # Save the watermarked PDF
        output_path = os.path.join(self.temp_dir, f"watermarked_{os.path.basename(pdf_path)}")
        doc.save(output_path)
        doc.close()
        
        return output_path

# Maintain backward compatibility
PDFProcessor = PDFProcessor
        