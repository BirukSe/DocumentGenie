# import PyPDF2
# import fitz  # PyMuPDF
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import letter
# import io
# import tempfile
# import os
# import re
# import shutil  # ADD THIS MISSING IMPORT
# import uuid    # ADD THIS MISSING IMPORT
# from typing import Optional, List, Dict, Any, Tuple
# from fuzzywuzzy import fuzz
# import nltk
# from nltk.tokenize import sent_tokenize, word_tokenize

# # Download required NLTK data
# try:
#     nltk.data.find('tokenizers/punkt')
# except LookupError:
#     nltk.download('punkt')

# class PDFProcessor:
#     def __init__(self):
#         self.temp_dir = tempfile.mkdtemp()
        
#     def change_background_color(self, input_path: str, color: str = "yellow", opacity: float = 0.3) -> Dict[str, Any]:
#         """
#         Change the background color of all pages in the PDF.
        
#         Args:
#             input_path: Path to the input PDF file
#             color: Background color (hex format like '#FFFF00' or color name like 'yellow')
#             opacity: Opacity of the background color (0.0 to 1.0)
            
#         Returns:
#             Dict with success status, message, and output path
#         """
#         try:
#             import fitz  # PyMuPDF
#             import tempfile
#             import shutil
            
#             # Check if input file exists
#             if not os.path.exists(input_path):
#                 return {
#                     "success": False,
#                     "error": f"Input file does not exist: {input_path}",
#                     "output_path": None
#                 }
            
#             # Convert color name to hex if needed
#             color_mapping = {
#                 'yellow': '#FFFF00',
#                 'red': '#FF0000',
#                 'blue': '#0000FF',
#                 'green': '#00FF00',
#                 'white': '#FFFFFF',
#                 'black': '#000000',
#                 'gray': '#808080',
#                 'grey': '#808080',
#                 'cyan': '#00FFFF',
#                 'magenta': '#FF00FF'
#             }
            
#             # Convert color name to hex if it's a named color
#             color = color_mapping.get(color.lower(), color)
            
#             # Ensure color starts with # if it's a hex color
#             if not color.startswith('#') and all(c in '0123456789ABCDEFabcdef' for c in color):
#                 color = f"#{color}"
            
#             # Convert hex color to RGB values (0-1 range)
#             if color.startswith('#'):
#                 hex_color = color[1:]
#                 if len(hex_color) == 6:
#                     r = int(hex_color[0:2], 16) / 255.0
#                     g = int(hex_color[2:4], 16) / 255.0
#                     b = int(hex_color[4:6], 16) / 255.0
#                 else:
#                     raise ValueError(f"Invalid hex color format: {color}")
#             else:
#                 raise ValueError(f"Unsupported color format: {color}")
            
#             # CRITICAL FIX: Create a temporary output file first to avoid the "incremental save" error
#             temp_output = None
#             try:
#                 # Create temporary output file
#                 temp_fd, temp_output = tempfile.mkstemp(suffix='.pdf', prefix='bg_modified_')
#                 os.close(temp_fd)  # Close the file descriptor immediately
                
#                 # Open the PDF
#                 doc = fitz.open(input_path)
                
#                 # Process each page
#                 for page_num in range(len(doc)):
#                     page = doc[page_num]
                    
#                     # Get page dimensions
#                     rect = page.rect
                    
#                     # Create a rectangle covering the entire page
#                     background_rect = fitz.Rect(0, 0, rect.width, rect.height)
                    
#                     # Add the background rectangle with specified color and opacity
#                     # Use insert_text with a background color instead of draw_rect for better results
#                     shape = page.new_shape()
#                     shape.draw_rect(background_rect)
#                     shape.fill_color = (r, g, b)
#                     shape.fill_opacity = opacity
#                     shape.commit(overlay=False)  # Put background behind existing content
                
#                 # Save to temporary file first
#                 doc.save(temp_output, garbage=4, deflate=True)
#                 doc.close()
                
#                 # Now copy the temporary file back to the original location
#                 shutil.copy2(temp_output, input_path)
                
#                 # Verify the file was updated correctly
#                 if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
#                     return {
#                         "success": False,
#                         "error": "Failed to update original file or file is empty",
#                         "output_path": None
#                     }
                
#                 return {
#                     "success": True,
#                     "message": f"Successfully changed background color to {color} with {opacity*100}% opacity",
#                     "output_path": input_path  # Return the original path since we updated it in place
#                 }
                
#             finally:
#                 # Clean up temporary file
#                 if temp_output and os.path.exists(temp_output):
#                     try:
#                         os.unlink(temp_output)
#                     except:
#                         pass  # Ignore cleanup errors
            
#         except Exception as e:
#             import traceback
#             error_msg = f"Error changing background color: {str(e)}\n{traceback.format_exc()}"
#             return {
#                 "success": False,
#                 "error": error_msg,
#                 "output_path": None
#             }
    
#     def load_pdf(self, file_path: str) -> fitz.Document:
#         """Load PDF document"""
#         return fitz.open(file_path)
    
#     def analyze_document(self, pdf_path: str) -> Dict[str, Any]:
#         """
#         Comprehensive document analysis with formatting details
        
#         Args:
#             pdf_path: Path to the PDF file to analyze
            
#         Returns:
#             Dict containing analysis results including pages, fonts, colors, and document structure
            
#         Raises:
#             FileNotFoundError: If the PDF file doesn't exist
#             Exception: For any errors during analysis
#         """
#         if not os.path.exists(pdf_path):
#             raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
#         doc = None
#         try:
#             doc = fitz.open(pdf_path)
#             analysis = {
#                 "pages": len(doc),
#                 "page_details": [],
#                 "fonts_used": set(),
#                 "colors_used": set(),
#                 "has_images": False,
#                 "has_tables": False,
#                 "text_blocks": [],
#                 "paragraphs": [],
#                 "bullet_points": [],
#                 "headings": []
#             }
            
#             for page_num in range(len(doc)):
#                 page = doc[page_num]
                
#                 # Handle potential generator objects by converting to list
#                 page_dict = page.get_text("dict")
#                 blocks = list(page_dict.get("blocks", []))  # Ensure blocks is a list, not a generator
#                 images = list(page.get_images())  # Convert generator to list
                
#                 # Convert any generator to list before calculating length
#                 annotations = list(page.annots() or [])  # Handle None case
                
#                 # Check for tables (simple check - could be enhanced)
#                 has_tables = any(block.get('type') == 1 for block in blocks)
                
#                 page_info = {
#                     "page_number": page_num + 1,
#                     "width": page.rect.width,
#                     "height": page.rect.height,
#                     "text_blocks": len(blocks),
#                     "images": len(images),
#                     "annotations": len(annotations),
#                     "has_tables": has_tables
#                 }
                
#                 # Update global analysis flags
#                 if has_tables:
#                     analysis["has_tables"] = True
#                 if images:
#                     analysis["has_images"] = True
                
#                 # Extract text with formatting
#                 for block in blocks:
#                     if "lines" in block:
#                         for line in block["lines"]:
#                             for span in line["spans"]:
#                                 font = span.get("font", "")
#                                 color = span.get("color", 0)
#                                 if font:
#                                     analysis["fonts_used"].add(font)
#                                 if color:
#                                     analysis["colors_used"].add(color)
                                
#                                 text = span.get("text", "").strip()
#                                 if not text:
#                                     continue
                                    
#                                 # Detect headings (larger font size or bold)
#                                 if span.get("size", 0) > 14 or span.get("flags", 0) & 2**4:
#                                     analysis["headings"].append({
#                                         "text": text,
#                                         "page": page_num + 1,
#                                         "font": font,
#                                         "size": span.get("size", 0)
#                                     })
                                
#                                 # Detect bullet points
#                                 if re.match(r'^[\u2022\u25E6\u25AA\u25AB\u25CF\u25CB\*\-\+]\s+', text):
#                                     analysis["bullet_points"].append({
#                                         "text": text,
#                                         "page": page_num + 1,
#                                         "type": "bullet"
#                                     })
#                                 elif re.match(r'^\d+[\.\)]\s+', text):
#                                     analysis["bullet_points"].append({
#                                         "text": text,
#                                         "page": page_num + 1,
#                                         "type": "numbered"
#                                     })
                
#                 analysis["page_details"].append(page_info)
            
#             # Convert sets to lists for JSON serialization
#             analysis["fonts_used"] = sorted(list(analysis["fonts_used"]))
#             analysis["colors_used"] = sorted(list(analysis["colors_used"]))
            
#             return analysis
            
#         except Exception as e:
#             raise Exception(f"Error analyzing PDF: {str(e)}")
            
#         finally:
#             # Ensure the document is always closed
#             if doc is not None:
#                 doc.close()
    
#     def replace_text_with_formatting(self, pdf_path: str, old_text: str, new_text: str, 
#                                    preserve_formatting: bool = True, fuzzy_match: bool = True) -> str:
#         """Replace text while preserving original font style"""
#         doc = fitz.open(pdf_path)
        
#         for page_num in range(len(doc)):
#             page = doc[page_num]
            
#             if fuzzy_match:
#                 # Use fuzzy matching for more flexible text replacement
#                 page_text = page.get_text()
#                 words = word_tokenize(page_text.lower())
#                 old_words = word_tokenize(old_text.lower())
                
#                 # Find best match using sliding window
#                 best_match = self._find_best_fuzzy_match(page_text, old_text)
#                 if best_match:
#                     old_text = best_match
            
#             # Get original formatting before replacement
#             original_formatting = None
#             if preserve_formatting:
#                 original_formatting = self._get_text_formatting(pdf_path, old_text)
            
#             # Find and replace text instances
#             text_instances = page.search_for(old_text)
#             for inst in text_instances:
#                 if original_formatting and preserve_formatting:
#                     self._replace_text_with_formatting(page, inst, new_text, original_formatting)
#                 else:
#                     # Standard replacement without formatting preservation
#                     page.add_redact_annot(inst, new_text)
#                     page.apply_redactions()
        
#         temp_path = os.path.join(self.temp_dir, f"text_replaced_{os.path.basename(pdf_path)}")
#         doc.save(temp_path)
#         doc.close()
#         return temp_path
    
#     def _get_text_formatting(self, pdf_path: str, text: str) -> Dict[str, Any]:
#         """Extract formatting properties from specific text"""
#         doc = fitz.open(pdf_path)
        
#         for page_num in range(len(doc)):
#             page = doc[page_num]
#             blocks = page.get_text("dict")
            
#             for block in blocks.get("blocks", []):
#                 if "lines" in block:
#                     for line in block["lines"]:
#                         for span in line["spans"]:
#                             if text.lower() in span["text"].lower():
#                                 formatting = {
#                                     "font": span.get("font", "helv"),
#                                     "size": span.get("size", 12),
#                                     "color": span.get("color", 0),
#                                     "flags": span.get("flags", 0),
#                                     "bbox": span.get("bbox", [0, 0, 0, 0])
#                                 }
#                                 doc.close()
#                                 return formatting
        
#         doc.close()
#         # Return default formatting if text not found
#         return {
#             "font": "helv",
#             "size": 12,
#             "color": 0,
#             "flags": 0,
#             "bbox": [0, 0, 0, 0]
#         }
    
#     def _replace_text_with_formatting(self, page: fitz.Page, rect: fitz.Rect, new_text: str, formatting: Dict[str, Any]):
#         """Replace text while applying specific formatting"""
#         # Remove old text
#         page.add_redact_annot(rect)
#         page.apply_redactions()
        
#         # Add new text with preserved formatting
#         font_name = formatting.get("font", "helv")
#         font_size = formatting.get("size", 12)
#         color = self._convert_color_to_rgb(formatting.get("color", 0))
#         flags = formatting.get("flags", 0)
        
#         # Insert new text with formatting
#         page.insert_text(
#             rect.tl,  # Top-left point
#             new_text,
#             fontname=font_name,
#             fontsize=font_size,
#             color=color,
#             flags=flags
#         )
    
#     def _convert_color_to_rgb(self, color_int: int) -> Tuple[float, float, float]:
#         """Convert integer color to RGB tuple"""
#         if color_int == 0:
#             return (0, 0, 0)  # Black
        
#         # Extract RGB components from integer
#         r = (color_int >> 16) & 0xFF
#         g = (color_int >> 8) & 0xFF
#         b = color_int & 0xFF
        
#         # Normalize to 0-1 range
#         return (r/255.0, g/255.0, b/255.0)
    
#     def _find_best_fuzzy_match(self, text: str, target: str, threshold: int = 80) -> Optional[str]:
#         """Find best fuzzy match for target text within document text"""
#         words = text.split()
#         target_words = target.split()
#         target_len = len(target_words)
        
#         best_match = None
#         best_ratio = 0
        
#         for i in range(len(words) - target_len + 1):
#             candidate = " ".join(words[i:i + target_len])
#             ratio = fuzz.ratio(candidate.lower(), target.lower())
            
#             if ratio > best_ratio and ratio >= threshold:
#                 best_ratio = ratio
#                 best_match = candidate
        
#         return best_match
    
#     def modify_paragraph(self, pdf_path: str, paragraph_identifier: str, new_content: str, 
#                         operation: str = "replace", preserve_formatting: bool = True) -> str:
#         """Modify specific paragraphs with font style preservation"""
#         doc = fitz.open(pdf_path)
        
#         for page_num in range(len(doc)):
#             page = doc[page_num]
#             page_text = page.get_text()
#             paragraphs = page_text.split('\n\n')
            
#             for paragraph in paragraphs:
#                 if self._paragraph_matches(paragraph, paragraph_identifier):
#                     # Get original paragraph formatting
#                     original_formatting = None
#                     if preserve_formatting:
#                         original_formatting = self._get_paragraph_formatting(pdf_path, paragraph)
                    
#                     if operation == "replace":
#                         self._replace_paragraph_with_formatting(page, paragraph, new_content, original_formatting)
#                     elif operation == "delete":
#                         self._replace_paragraph_with_formatting(page, paragraph, "", original_formatting)
#                     elif operation == "modify":
#                         modified_content = self._modify_paragraph_content(paragraph, new_content)
#                         self._replace_paragraph_with_formatting(page, paragraph, modified_content, original_formatting)
        
#         temp_path = os.path.join(self.temp_dir, f"paragraph_modified_{os.path.basename(pdf_path)}")
#         doc.save(temp_path)
#         doc.close()
#         return temp_path
    
#     def _paragraph_matches(self, paragraph: str, identifier: str) -> bool:
#         """Check if paragraph matches identifier using fuzzy matching"""
#         return fuzz.partial_ratio(paragraph.lower(), identifier.lower()) > 70
    
#     def _get_paragraph_formatting(self, pdf_path: str, paragraph: str) -> Dict[str, Any]:
#         """Get formatting properties for a paragraph (uses first sentence formatting)"""
#         sentences = sent_tokenize(paragraph)
#         if sentences:
#             return self._get_text_formatting(pdf_path, sentences[0][:50])  # Use first 50 chars of first sentence
#         return self._get_text_formatting(pdf_path, paragraph[:50])
    
#     def _replace_paragraph_with_formatting(self, page: fitz.Page, old_paragraph: str, new_paragraph: str, formatting: Optional[Dict[str, Any]]):
#         """Replace paragraph while preserving original formatting"""
#         # Find paragraph instances
#         paragraph_words = old_paragraph.split()[:5]  # Use first 5 words to find paragraph
#         search_text = " ".join(paragraph_words)
#         text_instances = page.search_for(search_text)
        
#         for inst in text_instances:
#             if formatting:
#                 self._replace_text_with_formatting(page, inst, new_paragraph, formatting)
#             else:
#                 page.add_redact_annot(inst, new_paragraph)
#                 page.apply_redactions()
    
#     def _modify_paragraph_content(self, original: str, modification: str) -> str:
#         """Intelligently modify paragraph content based on modification instruction"""
#         # This is a simplified version - in practice, you might use NLP to understand the modification
#         if "add" in modification.lower():
#             return original + " " + modification.replace("add", "").strip()
#         elif "remove" in modification.lower():
#             # Simple removal logic
#             return original.replace(modification.replace("remove", "").strip(), "")
#         else:
#             return modification  # Default to replacement
    
#     def add_content(self, pdf_path: str, content: str, location: str, preserve_formatting: bool = True, **kwargs) -> str:
#         """Add content at specific locations with font style matching"""
#         doc = fitz.open(pdf_path)
        
#         # Get surrounding text formatting for context-aware insertion
#         surrounding_formatting = None
#         if preserve_formatting:
#             surrounding_formatting = self._get_surrounding_formatting(doc, location, **kwargs)
        
#         if location == "beginning":
#             self._add_content_at_beginning(doc, content, surrounding_formatting)
#         elif location == "end":
#             self._add_content_at_end(doc, content, surrounding_formatting)
#         elif location == "after_paragraph":
#             paragraph_id = kwargs.get("paragraph_id", "")
#             self._add_content_after_paragraph(doc, content, paragraph_id, surrounding_formatting)
#         elif location == "page":
#             page_num = kwargs.get("page_number", 0)
#             x = kwargs.get("x", 100)
#             y = kwargs.get("y", 100)
#             self._add_content_to_page(doc, content, page_num, x, y, surrounding_formatting)
        
#         temp_path = os.path.join(self.temp_dir, f"content_added_{os.path.basename(pdf_path)}")
#         doc.save(temp_path)
#         doc.close()
#         return temp_path
    
#     def _get_surrounding_formatting(self, doc: fitz.Document, location: str, **kwargs) -> Dict[str, Any]:
#         """Get formatting from surrounding text for context-aware insertion"""
#         default_formatting = {
#             "font": "helv",
#             "size": 12,
#             "color": 0,
#             "flags": 0
#         }
        
#         try:
#             if location == "after_paragraph":
#                 paragraph_id = kwargs.get("paragraph_id", "")
#                 if paragraph_id:
#                     # Get formatting from the target paragraph
#                     for page_num in range(len(doc)):
#                         page = doc[page_num]
#                         page_text = page.get_text()
#                         if paragraph_id.lower() in page_text.lower():
#                             return self._get_text_formatting_from_page(page, paragraph_id)
            
#             elif location == "beginning" or location == "end":
#                 # Use formatting from first/last paragraph
#                 page_num = 0 if location == "beginning" else len(doc) - 1
#                 if page_num < len(doc):
#                     page = doc[page_num]
#                     page_text = page.get_text()
#                     paragraphs = page_text.split('\n\n')
#                     if paragraphs:
#                         target_paragraph = paragraphs[0] if location == "beginning" else paragraphs[-1]
#                         return self._get_text_formatting_from_page(page, target_paragraph[:50])
        
#         except Exception:
#             pass
        
#         return default_formatting
    
#     def _get_text_formatting_from_page(self, page: fitz.Page, text: str) -> Dict[str, Any]:
#         """Get formatting from specific text on a page"""
#         blocks = page.get_text("dict")
#         for block in blocks.get("blocks", []):
#             if "lines" in block:
#                 for line in block["lines"]:
#                     for span in line["spans"]:
#                         if text.lower() in span["text"].lower():
#                             return {
#                                 "font": span.get("font", "helv"),
#                                 "size": span.get("size", 12),
#                                 "color": span.get("color", 0),
#                                 "flags": span.get("flags", 0)
#                             }
        
#         return {
#             "font": "helv",
#             "size": 12,
#             "color": 0,
#             "flags": 0
#         }
    
#     def _add_content_at_beginning(self, doc: fitz.Document, content: str, formatting: Optional[Dict[str, Any]]):
#         """Add content at the beginning of the document"""
#         if len(doc) > 0:
#             page = doc[0]
#             # Insert at top of first page
#             insert_point = fitz.Point(72, 72)  # 1 inch margins
            
#             if formatting:
#                 page.insert_text(
#                     insert_point,
#                     content,
#                     fontname=formatting.get("font", "helv"),
#                     fontsize=formatting.get("size", 12),
#                     color=self._convert_color_to_rgb(formatting.get("color", 0))
#                 )
#             else:
#                 page.insert_text(insert_point, content)
    
#     def _add_content_at_end(self, doc: fitz.Document, content: str, formatting: Optional[Dict[str, Any]]):
#         """Add content at the end of the document"""
#         if len(doc) > 0:
#             page = doc[-1]
#             # Insert at bottom of last page
#             page_rect = page.rect
#             insert_point = fitz.Point(72, page_rect.height - 72)  # 1 inch from bottom
            
#             if formatting:
#                 page.insert_text(
#                     insert_point,
#                     content,
#                     fontname=formatting.get("font", "helv"),
#                     fontsize=formatting.get("size", 12),
#                     color=self._convert_color_to_rgb(formatting.get("color", 0))
#                 )
#             else:
#                 page.insert_text(insert_point, content)
    
#     def _add_content_after_paragraph(self, doc: fitz.Document, content: str, paragraph_id: str, formatting: Optional[Dict[str, Any]]):
#         """Add content after a specific paragraph"""
#         for page_num in range(len(doc)):
#             page = doc[page_num]
#             page_text = page.get_text()
            
#             if paragraph_id.lower() in page_text.lower():
#                 # Find paragraph location and add content after it
#                 # This is a simplified implementation
#                 paragraphs = page_text.split('\n\n')
#                 for i, paragraph in enumerate(paragraphs):
#                     if paragraph_id.lower() in paragraph.lower():
#                         # Insert content after this paragraph
#                         # For simplicity, insert at end of page - in practice, you'd calculate exact position
#                         insert_point = fitz.Point(72, 200 + i * 50)  # Rough positioning
                        
#                         if formatting:
#                             page.insert_text(
#                                 insert_point,
#                                 content,
#                                 fontname=formatting.get("font", "helv"),
#                                 fontsize=formatting.get("size", 12),
#                                 color=self._convert_color_to_rgb(formatting.get("color", 0))
#                             )
#                         else:
#                             page.insert_text(insert_point, content)
#                         break
    
#     def _add_content_to_page(self, doc: fitz.Document, content: str, page_num: int, x: float, y: float, formatting: Optional[Dict[str, Any]]):
#         """Add content at specific coordinates on a page"""
#         if page_num < len(doc):
#             page = doc[page_num]
#             insert_point = fitz.Point(x, y)
            
#             if formatting:
#                 page.insert_text(
#                     insert_point,
#                     content,
#                     fontname=formatting.get("font", "helv"),
#                     fontsize=formatting.get("size", 12),
#                     color=self._convert_color_to_rgb(formatting.get("color", 0))
#                 )
#             else:
#                 page.insert_text(insert_point, content)
    
#     def add_watermark(self, pdf_path: str, watermark_text: str = "DOCUMENT", opacity: float = 0.3) -> str:
#         """
#         Add a watermark to all pages of the PDF.
        
#         Args:
#             pdf_path: Path to the input PDF file
#             watermark_text: Text to use as watermark (default: 'DOCUMENT')
#             opacity: Opacity of the watermark (0.0 to 1.0, default: 0.3)
            
#         Returns:
#             str: Path to the watermarked PDF file
#         """
#         doc = fitz.open(pdf_path)
        
#         for page_num in range(len(doc)):
#             page = doc[page_num]
            
#             # Get page dimensions
#             page_rect = page.rect
#             width = page_rect.width
#             height = page_rect.height
            
#             # Create a new PDF with the watermark
#             packet = io.BytesIO()
#             c = canvas.Canvas(packet, pagesize=(width, height))
            
#             # Set font and size
#             c.setFont("Helvetica-Bold", 60)
            
#             # Set fill color to light gray with specified opacity
#             c.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)
            
#             # Rotate the text
#             c.rotate(45)
            
#             # Position the text in the center
#             text_width = c.stringWidth(watermark_text, "Helvetica-Bold", 60)
#             x = (width / 3.5) - (text_width / 2)
#             y = height / 3.5
            
#             # Add the text
#             c.drawString(x, y, watermark_text)
            
#             # Save the watermark
#             c.save()
            
#             # Move to the beginning of the StringIO buffer
#             packet.seek(0)
#             watermark = fitz.open("pdf", packet.read())
            
#             # Get the first page of the watermark
#             watermark_page = watermark[0]
            
#             # Merge the watermark with the current page
#             page.show_pdf_page(page_rect, watermark, 0)
            
#             # Clean up
#             watermark.close()
        
#         # Save the watermarked PDF
#         output_path = os.path.join(self.temp_dir, f"watermarked_{os.path.basename(pdf_path)}")
#         doc.save(output_path)
#         doc.close()
        
#         return output_path

# # Maintain backward compatibility
# PDFProcessor = PDFProcessor
import os
import tempfile
import shutil
import fitz  # PyMuPDF
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="pdf_processor_")
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def change_background_color(self, input_path: str, color: str = "yellow", opacity: float = 0.7) -> Dict[str, Any]:
        """
        Change the background color of all pages in the PDF.
        FIXED: Handles PyMuPDF save limitations properly.
        """
        doc = None
        temp_output = None
        
        try:
            # Validate input
            if not input_path or not os.path.exists(input_path):
                return {
                    "success": False,
                    "error": f"Input file does not exist: {input_path}",
                    "output_path": None
                }
            
            logger.info(f"Processing background color change for: {input_path}")
            logger.info(f"File size: {os.path.getsize(input_path)} bytes")
            
            # Color mapping and validation
            color_mapping = {
                'yellow': '#FFFF00', 'red': '#FF0000', 'blue': '#0000FF', 
                'green': '#00FF00', 'white': '#FFFFFF', 'black': '#000000',
                'gray': '#808080', 'grey': '#808080', 'cyan': '#00FFFF', 
                'magenta': '#FF00FF', 'orange': '#FFA500', 'purple': '#800080'
            }
            
            # Convert color name to hex
            original_color = color
            color = color_mapping.get(color.lower(), color)
            
            # Ensure hex format
            if not color.startswith('#') and all(c in '0123456789ABCDEFabcdef' for c in color):
                color = f"#{color}"
            
            # Convert to RGB (0-1 range)
            if color.startswith('#') and len(color) == 7:
                try:
                    hex_color = color[1:]
                    r = int(hex_color[0:2], 16) / 255.0
                    g = int(hex_color[2:4], 16) / 255.0
                    b = int(hex_color[4:6], 16) / 255.0
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid hex color format: {color}",
                        "output_path": None
                    }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported color format: {color}. Use hex (#RRGGBB) or color name.",
                    "output_path": None
                }
            
            # Validate opacity
            if not (0.0 <= opacity <= 1.0):
                return {
                    "success": False,
                    "error": f"Opacity must be between 0.0 and 1.0, got {opacity}",
                    "output_path": None
                }
            
            # Create temporary output file
            temp_fd, temp_output = tempfile.mkstemp(suffix='.pdf', prefix='bg_temp_', dir=self.temp_dir)
            os.close(temp_fd)  # Close file descriptor immediately
            
            logger.info(f"Created temporary file: {temp_output}")
            
            # Open and process the PDF
            doc = fitz.open(input_path)
            logger.info(f"Opened PDF with {doc.page_count} pages")
            
            # Process each page
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Get page dimensions
                rect = page.rect
                logger.debug(f"Page {page_num + 1} dimensions: {rect.width}x{rect.height}")
                
                # Create background rectangle covering the entire page
                background_rect = fitz.Rect(0, 0, rect.width, rect.height)
                
                # Method 1: Use draw_rect for reliable background (most compatible)
                try:
                    # Draw filled rectangle as background
                    # page.draw_rect(background_rect, color=(r, g, b), fill=(r, g, b), width=0)
                    page.draw_rect(
    background_rect,
    fill=(r, g, b),
    overlay=True,
    fill_opacity=0.5   # experiment with 0.3–0.7
)

                    logger.debug(f"Page {page_num + 1}: Drew background rectangle")
                except Exception as e:
                    logger.warning(f"Page {page_num + 1}: draw_rect failed: {e}")
                    
                    # Fallback: Use shape drawing
                    try:
                        shape = page.new_shape()
                        shape.draw_rect(background_rect)
                        shape.fill_color = (r, g, b)
                        shape.fill_opacity = max(opacity, 0.5)  # Ensure minimum visibility
                        shape.stroke_opacity = 0  # No border
                        shape.commit(overlay=False)
                        logger.debug(f"Page {page_num + 1}: Used shape fallback")
                    except Exception as e2:
                        logger.error(f"Page {page_num + 1}: Both methods failed: {e2}")
                        
                        # Last resort: Use insert_textbox with background
                        try:
                            # Create a text box that covers the entire page as background
                            text_rect = fitz.Rect(0, 0, rect.width, rect.height)
                            page.insert_textbox(
                                text_rect, 
                                "",  # Empty text
                                color=(r, g, b),
                                fill=(r, g, b),
                                align=fitz.TEXT_ALIGN_LEFT
                            )
                            logger.debug(f"Page {page_num + 1}: Used textbox fallback")
                        except Exception as e3:
                            logger.error(f"Page {page_num + 1}: All methods failed: {e3}")
            
            logger.info("Background color applied to all pages")
            
            # Save to temporary file first (this avoids the incremental save error)
            doc.save(temp_output, garbage=4, deflate=True, clean=True)
            doc.close()
            doc = None  # Clear reference
            
            logger.info(f"Saved temporary file: {os.path.getsize(temp_output)} bytes")
            
            # Verify temp file was created successfully
            if not os.path.exists(temp_output) or os.path.getsize(temp_output) == 0:
                return {
                    "success": False,
                    "error": "Failed to create temporary output file or file is empty",
                    "output_path": None
                }
            
            # Copy back to original location
            shutil.copy2(temp_output, input_path)
            logger.info(f"Copied back to original location: {input_path}")
            
            # Verify final file
            if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
                return {
                    "success": False,
                    "error": "Failed to update original file",
                    "output_path": None
                }
            
            logger.info(f"Successfully changed background color to {original_color}")
            
            return {
                "success": True,
                "message": f"Successfully changed background color to {original_color} with {opacity*100:.1f}% opacity",
                "output_path": input_path
            }
            
        except Exception as e:
            logger.error(f"Error in change_background_color: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error changing background color: {str(e)}",
                "output_path": None
            }
            
        finally:
            # Clean up resources
            if doc is not None:
                try:
                    doc.close()
                except:
                    pass
            
            # Clean up temporary file
            if temp_output and os.path.exists(temp_output):
                try:
                    os.unlink(temp_output)
                    logger.debug(f"Cleaned up temporary file: {temp_output}")
                except:
                    logger.warning(f"Failed to clean up temporary file: {temp_output}")
    
    def load_pdf(self, pdf_path: str):
        """Load PDF document with error handling"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            return fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
            raise
    
    def add_text(self, pdf_path: str, text: str, position: tuple, font_name: str = "helv", 
                 font_size: int = 12, color: tuple = (0, 0, 0)) -> str:
        """Add text to a specific position in the PDF"""
        doc = None
        try:
            doc = self.load_pdf(pdf_path)
            
            # Add text to first page by default
            if doc.page_count > 0:
                page = doc[0]  # First page
                page.insert_text(
                    position,  # (x, y) coordinates
                    text,
                    fontname=font_name,
                    fontsize=font_size,
                    color=color
                )
            
            # Save to temporary file
            temp_path = os.path.join(self.temp_dir, f"text_added_{os.path.basename(pdf_path)}")
            doc.save(temp_path, garbage=4, deflate=True)
            return temp_path
            
        except Exception as e:
            logger.error(f"Error adding text: {str(e)}")
            raise
        finally:
            if doc is not None:
                doc.close()

    def analyze_document(self, pdf_path: str) -> Dict[str, Any]:
        """Analyze PDF document structure and content"""
        try:
            doc = self.load_pdf(pdf_path)
            
            analysis = {
                "pages": doc.page_count,
                "fonts_used": [],
                "colors_used": [],
                "has_images": False,
                "has_tables": False,
                "headings": [],
                "text_blocks": []
            }
            
            # Basic analysis for first few pages
            for page_num in range(min(3, doc.page_count)):
                page = doc[page_num]
                
                # Check for images
                if page.get_images():
                    analysis["has_images"] = True
                
                # Get text blocks for structure analysis
                blocks = page.get_text("dict")
                for block in blocks.get("blocks", []):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line.get("spans", []):
                                # Track fonts
                                font = span.get("font", "")
                                if font and font not in analysis["fonts_used"]:
                                    analysis["fonts_used"].append(font)
                                
                                # Track text blocks
                                text = span.get("text", "").strip()
                                if text and len(text) > 10:
                                    analysis["text_blocks"].append({
                                        "text": text[:100],  # First 100 chars
                                        "font": font,
                                        "size": span.get("size", 0),
                                        "page_number": page_num + 1,
                                        "bbox": span.get("bbox", (0, 0, 0, 0))
                                    })
            
            doc.close()
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            return {"error": str(e), "pages": 0, "fonts_used": [], "colors_used": []}
    
    def _get_text_formatting(self, pdf_path: str, text: str) -> Dict[str, Any]:
        """Extract formatting properties from specific text"""
        doc = None
        try:
            doc = self.load_pdf(pdf_path)
            
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
                                    return formatting
            
            # Return default formatting if text not found
            return {
                "font": "helv",
                "size": 12,
                "color": 0,
                "flags": 0,
                "bbox": [0, 0, 0, 0]
            }
        except Exception as e:
            logger.error(f"Error getting text formatting: {str(e)}")
            return {
                "font": "helv",
                "size": 12,
                "color": 0,
                "flags": 0,
                "bbox": [0, 0, 0, 0]
            }
        finally:
            if doc is not None:
                doc.close()
    
    def _convert_color_to_rgb(self, color_int: int) -> tuple:
        """Convert integer color to RGB tuple"""
        if color_int == 0:
            return (0, 0, 0)  # Black
        
        # Extract RGB components from integer
        r = (color_int >> 16) & 0xFF
        g = (color_int >> 8) & 0xFF
        b = color_int & 0xFF
        
        # Normalize to 0-1 range
        return (r/255.0, g/255.0, b/255.0)
    
    def replace_text_with_formatting(self, pdf_path: str, old_text: str, new_text: str, 
                                   preserve_formatting: bool = True, fuzzy_match: bool = True) -> str:
        """Replace text while preserving original font style"""
        doc = None
        try:
            doc = self.load_pdf(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                if fuzzy_match:
                    # Use fuzzy matching for more flexible text replacement
                    page_text = page.get_text()
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
            
            # Save to temporary file
            temp_path = os.path.join(self.temp_dir, f"text_replaced_{os.path.basename(pdf_path)}")
            doc.save(temp_path, garbage=4, deflate=True)
            return temp_path
            
        except Exception as e:
            logger.error(f"Error replacing text: {str(e)}")
            raise
        finally:
            if doc is not None:
                doc.close()
    
    def _replace_text_with_formatting(self, page, rect, new_text: str, formatting: Dict[str, Any]):
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
        try:
            # Try with flags parameter first
            page.insert_text(
                rect.tl,  # Top-left point
                new_text,
                fontname=font_name,
                fontsize=font_size,
                color=color,
                flags=flags
            )
        except TypeError:
            # Fallback without flags parameter
            page.insert_text(
                rect.tl,  # Top-left point
                new_text,
                fontname=font_name,
                fontsize=font_size,
                color=color
            )
    
    def _find_best_fuzzy_match(self, text: str, target: str, threshold: int = 80) -> Optional[str]:
        """Find best fuzzy match for target text within document text"""
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            # Fallback to simple string matching if fuzzywuzzy not available
            if target.lower() in text.lower():
                return target
            return None
        
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

    def __del__(self):
        """Cleanup temporary directory on deletion"""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass