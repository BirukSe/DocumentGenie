#!/usr/bin/env python3
"""
Test script to verify the fixes for DocumentGenie
"""
import os
import sys
import tempfile
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.tools import ChangeTitleTool
from services.pdf_service import PDFProcessor

def test_change_title_tool():
    """Test the ChangeTitleTool with different input formats"""
    print("🧪 Testing ChangeTitleTool fixes...")
    
    # Create a test PDF
    test_pdf_path = create_test_pdf()
    if not test_pdf_path:
        print("❌ Failed to create test PDF")
        return False
    
    print(f"✅ Created test PDF: {test_pdf_path}")
    
    # Test 1: Direct arguments
    print("\n📝 Test 1: Direct arguments")
    tool = ChangeTitleTool()
    try:
        result = tool._run(test_pdf_path, "Test Document", "Modified Document")
        print(f"✅ Direct arguments test: {result}")
    except Exception as e:
        print(f"❌ Direct arguments test failed: {e}")
    
    # Test 2: JSON string input (simulating agent input)
    print("\n📝 Test 2: JSON string input")
    json_input = json.dumps({
        "pdf_path": test_pdf_path,
        "current_title": "Test Document", 
        "new_title": "JSON Modified Document"
    })
    try:
        result = tool._run(json_input)
        print(f"✅ JSON input test: {result}")
    except Exception as e:
        print(f"❌ JSON input test failed: {e}")
    
    # Test 3: Background color change
    print("\n🎨 Test 3: Background color change")
    processor = PDFProcessor()
    try:
        result = processor.change_background_color(test_pdf_path, "yellow", 0.3)
        if result.get("success"):
            print(f"✅ Background color test: {result['message']}")
        else:
            print(f"❌ Background color test failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Background color test failed: {e}")
    
    # Cleanup
    cleanup_test_files(test_pdf_path)
    print("\n🧹 Cleaned up test files")
    
    print("\n✅ All tests completed!")
    return True

def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='test_fix_')
        os.close(temp_fd)
        
        # Create PDF content
        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, height - 100, "Test Document")
        
        # Add some content
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 150, "This is a test document for DocumentGenie.")
        c.drawString(100, height - 170, "It contains sample text that can be modified.")
        c.drawString(100, height - 190, "The title 'Test Document' can be changed.")
        
        c.save()
        return temp_path
        
    except Exception as e:
        print(f"❌ Failed to create test PDF: {e}")
        return None

def cleanup_test_files(test_pdf_path):
    """Clean up test files"""
    try:
        if test_pdf_path and os.path.exists(test_pdf_path):
            os.unlink(test_pdf_path)
    except:
        pass

if __name__ == "__main__":
    test_change_title_tool()
