#!/usr/bin/env python3
"""
Test script specifically for background color functionality
"""
import os
import sys
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_service import PDFProcessor

def create_test_pdf():
    """Create a simple test PDF with white background"""
    try:
        # Create temporary PDF file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='test_bg_')
        os.close(temp_fd)
        
        # Create PDF content
        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, height - 100, "Test Document")
        
        # Add some content
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 150, "This is a test document for background color testing.")
        c.drawString(100, height - 170, "The background should change to yellow.")
        c.drawString(100, height - 190, "This text should be visible on the yellow background.")
        
        # Add a second page
        c.showPage()
        c.setFont("Helvetica", 14)
        c.drawString(100, height - 100, "Page 2")
        c.drawString(100, height - 130, "This is the second page.")
        c.drawString(100, height - 150, "Both pages should have yellow background.")
        
        c.save()
        print(f"✅ Created test PDF: {temp_path}")
        print(f"   File size: {os.path.getsize(temp_path)} bytes")
        return temp_path
        
    except Exception as e:
        print(f"❌ Failed to create test PDF: {e}")
        return None

def test_background_color():
    """Test background color change functionality"""
    print("🎨 Testing Background Color Change...")
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    if not test_pdf_path:
        return False
    
    try:
        # Initialize processor
        processor = PDFProcessor()
        
        # Test different colors and opacities
        test_cases = [
            {"color": "yellow", "opacity": 0.7, "description": "Yellow with 70% opacity"},
            {"color": "red", "opacity": 0.5, "description": "Red with 50% opacity"},
            {"color": "blue", "opacity": 0.8, "description": "Blue with 80% opacity"},
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n🧪 Test {i+1}: {test_case['description']}")
            
            # Create a copy for this test
            test_copy_path = f"{test_pdf_path}_test_{i+1}.pdf"
            import shutil
            shutil.copy2(test_pdf_path, test_copy_path)
            
            # Apply background color
            result = processor.change_background_color(
                test_copy_path, 
                test_case["color"], 
                test_case["opacity"]
            )
            
            if result.get("success"):
                print(f"   ✅ Success: {result['message']}")
                print(f"   📁 Output: {test_copy_path}")
                print(f"   📊 File size: {os.path.getsize(test_copy_path)} bytes")
            else:
                print(f"   ❌ Failed: {result.get('error')}")
                return False
        
        # Cleanup
        for i in range(len(test_cases)):
            test_copy_path = f"{test_pdf_path}_test_{i+1}.pdf"
            if os.path.exists(test_copy_path):
                os.unlink(test_copy_path)
        
        os.unlink(test_pdf_path)
        print(f"\n🧹 Cleaned up test files")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run background color tests"""
    print("🚀 Background Color Test")
    print("=" * 40)
    
    success = test_background_color()
    
    if success:
        print("\n🎉 Background color tests passed!")
        print("\n📋 The fixes should now work:")
        print("1. Higher opacity (0.7 instead of 0.3)")
        print("2. Multiple fallback methods for background application")
        print("3. Better error handling and logging")
        print("\n🔄 Try the command again in the browser:")
        print("   'change the background color of the doc to yellow'")
    else:
        print("\n❌ Background color tests failed!")
        print("   Check the error messages above for details.")

if __name__ == "__main__":
    main()