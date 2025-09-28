#!/usr/bin/env python3
"""
Complete system test for DocumentGenie
Tests both backend functionality and frontend integration
"""
import os
import sys
import tempfile
import asyncio
import requests
import json
import time

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_service import PDFProcessor
from agents.document_agent import DocumentAgent
from utils.temp_storage import temp_storage

def test_backend_functionality():
    """Test backend PDF processing functionality"""
    print("🧪 Testing Backend Functionality...")
    
    # Create a test PDF
    test_pdf_path = create_test_pdf()
    if not test_pdf_path:
        print("❌ Failed to create test PDF")
        return False
    
    print(f"✅ Created test PDF: {test_pdf_path}")
    
    # Test 1: Background color change
    print("\n🎨 Test 1: Background color change")
    processor = PDFProcessor()
    try:
        result = processor.change_background_color(test_pdf_path, "yellow", 0.3)
        if result.get("success"):
            print(f"✅ Background color change: {result['message']}")
            print(f"   File size: {os.path.getsize(test_pdf_path)} bytes")
        else:
            print(f"❌ Background color change failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Background color change failed: {e}")
        return False
    
    # Test 2: Text replacement
    print("\n📝 Test 2: Text replacement")
    try:
        result_path = processor.replace_text_with_formatting(
            test_pdf_path, "Test Document", "Modified Document", True, True
        )
        if os.path.exists(result_path):
            print(f"✅ Text replacement successful: {result_path}")
        else:
            print("❌ Text replacement failed: No output file")
            return False
    except Exception as e:
        print(f"❌ Text replacement failed: {e}")
        return False
    
    # Test 3: Agent initialization
    print("\n🤖 Test 3: Agent initialization")
    try:
        agent = DocumentAgent()
        print(f"✅ DocumentAgent initialized with {len(agent.tools)} tools")
    except Exception as e:
        print(f"❌ DocumentAgent initialization failed: {e}")
        return False
    
    # Cleanup
    cleanup_test_files(test_pdf_path)
    print("\n🧹 Cleaned up test files")
    
    return True

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    # Test 1: Root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test 2: Health check
    try:
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ API docs accessible")
        else:
            print(f"❌ API docs failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API docs failed: {e}")
    
    return True

def test_frontend_integration():
    """Test frontend integration points"""
    print("\n🖥️ Testing Frontend Integration...")
    
    # Check if frontend is running
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running on localhost:3000")
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        print("   Make sure to run: cd frontend && npm run dev")
        return False
    
    return True

def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='test_system_')
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

def main():
    """Run all tests"""
    print("🚀 DocumentGenie Complete System Test")
    print("=" * 50)
    
    # Test backend functionality
    backend_ok = test_backend_functionality()
    
    # Test API endpoints
    api_ok = test_api_endpoints()
    
    # Test frontend integration
    frontend_ok = test_frontend_integration()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    print(f"Backend Functionality: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"API Endpoints: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"Frontend Integration: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    
    if backend_ok and api_ok and frontend_ok:
        print("\n🎉 All tests passed! The system is working correctly.")
        print("\n📋 Next steps:")
        print("1. Make sure both backend and frontend are running")
        print("2. Try the commands in the browser:")
        print("   - 'change the background color of the doc to yellow'")
        print("   - 'change the title that says Biruk to Ayele'")
        print("3. Check the browser console for debug messages")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    main()
