#!/usr/bin/env python3
"""
Visual test for background color - creates a PDF and applies background color
"""
import os
import sys
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_service import PDFProcessor

def create_visual_test_pdf():
    """Create a PDF specifically for visual testing"""
    try:
        # Create temporary PDF file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='visual_test_')
        os.close(temp_fd)
        
        # Create PDF content with clear text
        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, height - 100, "VISUAL TEST DOCUMENT")
        
        # Add some content
        c.setFont("Helvetica", 14)
        c.drawString(100, height - 150, "This document will have a YELLOW background.")
        c.drawString(100, height - 180, "If you can see this text clearly, the background is working.")
        c.drawString(100, height - 210, "The background should be bright yellow.")
        
        # Add a second page
        c.showPage()
        c.setFont("Helvetica", 16)
        c.drawString(100, height - 100, "PAGE 2 - YELLOW BACKGROUND")
        c.drawString(100, height - 130, "This page should also have yellow background.")
        c.drawString(100, height - 160, "Both pages should be clearly yellow.")
        
        c.save()
        print(f"✅ Created visual test PDF: {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"❌ Failed to create visual test PDF: {e}")
        return None

def main():
    """Create a visual test PDF with yellow background"""
    print("🎨 Creating Visual Background Test...")
    
    # Create test PDF
    test_pdf_path = create_visual_test_pdf()
    if not test_pdf_path:
        return
    
    try:
        # Apply yellow background
        processor = PDFProcessor()
        result = processor.change_background_color(test_pdf_path, "yellow", 0.8)
        
        if result.get("success"):
            print(f"✅ Applied yellow background successfully!")
            print(f"📁 Output file: {test_pdf_path}")
            print(f"📊 File size: {os.path.getsize(test_pdf_path)} bytes")
            print(f"\n🔍 Open this file to verify the yellow background is visible:")
            print(f"   {test_pdf_path}")
            print(f"\n💡 If the background is clearly yellow, the fix is working!")
        else:
            print(f"❌ Failed to apply background: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
