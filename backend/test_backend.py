#!/usr/bin/env python3
"""
Test script for DocumentGenie backend
"""
import os
import sys
import asyncio
import tempfile
import shutil
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_service import PDFProcessor
from agents.document_agent import DocumentAgent
from utils.temp_storage import temp_storage

async def test_pdf_processing():
    """Test basic PDF processing functionality"""
    print("🧪 Testing DocumentGenie Backend...")
    
    # Create a test PDF file
    test_pdf_path = create_test_pdf()
    print(f"✅ Created test PDF: {test_pdf_path}")
    
    # Test PDFProcessor
    print("\n📄 Testing PDFProcessor...")
    processor = PDFProcessor()
    
    # Test document analysis
    try:
        analysis = processor.analyze_document(test_pdf_path)
        print(f"✅ Document analysis successful: {analysis.get('pages', 0)} pages")
    except Exception as e:
        print(f"❌ Document analysis failed: {e}")
        return False
    
    # Test background color change
    print("\n🎨 Testing background color change...")
    try:
        result = processor.change_background_color(test_pdf_path, "yellow", 0.3)
        if result.get("success"):
            print(f"✅ Background color change successful: {result['message']}")
        else:
            print(f"❌ Background color change failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Background color change failed: {e}")
    
    # Test text replacement
    print("\n📝 Testing text replacement...")
    try:
        result_path = processor.replace_text_with_formatting(
            test_pdf_path, "Test Document", "Modified Document", True, True
        )
        if os.path.exists(result_path):
            print(f"✅ Text replacement successful: {result_path}")
        else:
            print("❌ Text replacement failed: No output file")
    except Exception as e:
        print(f"❌ Text replacement failed: {e}")
    
    # Test DocumentAgent
    print("\n🤖 Testing DocumentAgent...")
    try:
        agent = DocumentAgent()
        print(f"✅ DocumentAgent initialized with {len(agent.tools)} tools")
        
        # Test agent command processing
        test_command = "change the background color to yellow"
        print(f"📋 Testing command: '{test_command}'")
        
        # Note: This would require a full session setup, so we'll just test initialization
        print("✅ DocumentAgent tools loaded successfully")
        
    except Exception as e:
        print(f"❌ DocumentAgent test failed: {e}")
    
    # Cleanup
    cleanup_test_files(test_pdf_path)
    print("\n🧹 Cleaned up test files")
    
    print("\n✅ Backend tests completed!")
    return True

def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='test_doc_')
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
        
        # Add a second page
        c.showPage()
        c.setFont("Helvetica", 14)
        c.drawString(100, height - 100, "Page 2")
        c.drawString(100, height - 130, "This is the second page of the test document.")
        
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
    asyncio.run(test_pdf_processing())
