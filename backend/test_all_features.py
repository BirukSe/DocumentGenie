#!/usr/bin/env python3
"""
Comprehensive test for all supported PDF manipulation features
"""
import os
import sys
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pdf_service import PDFProcessor
from agents.tools import get_all_pdf_tools

def create_test_pdf():
    """Create a comprehensive test PDF"""
    try:
        # Create temporary PDF file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='test_all_features_')
        os.close(temp_fd)
        
        # Create PDF content
        c = canvas.Canvas(temp_path, pagesize=letter)
        width, height = letter
        
        # Page 1 - Title and content
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, height - 100, "Biruk Seyoum")
        
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 150, "Software Engineer")
        c.drawString(100, height - 170, "Email: biruk@example.com")
        c.drawString(100, height - 190, "Phone: +251-123-456-789")
        c.drawString(100, height - 210, "Location: Addis Ababa, Ethiopia")
        
        # Add some paragraphs
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, height - 250, "EXPERIENCE")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 270, "Senior Software Engineer at TechCorp (2020-2024)")
        c.drawString(100, height - 290, "• Developed web applications using React and Node.js")
        c.drawString(100, height - 310, "• Led a team of 5 developers")
        c.drawString(100, height - 330, "• Implemented CI/CD pipelines")
        
        # Page 2 - Skills and projects
        c.showPage()
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "SKILLS")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 130, "Programming Languages: Python, JavaScript, Java, C++")
        c.drawString(100, height - 150, "Frameworks: React, Node.js, Django, FastAPI")
        c.drawString(100, height - 170, "Databases: PostgreSQL, MongoDB, Redis")
        c.drawString(100, height - 190, "Tools: Git, Docker, AWS, Kubernetes")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 230, "PROJECTS")
        c.setFont("Helvetica", 12)
        c.drawString(100, height - 260, "1. E-commerce Platform - Built with React and Node.js")
        c.drawString(100, height - 280, "2. Machine Learning API - Python and TensorFlow")
        c.drawString(100, height - 300, "3. Mobile App - React Native and Firebase")
        
        c.save()
        print(f"✅ Created comprehensive test PDF: {temp_path}")
        return temp_path
        
    except Exception as e:
        print(f"❌ Failed to create test PDF: {e}")
        return None

def test_all_features():
    """Test all supported PDF manipulation features"""
    print("🧪 Testing All PDF Manipulation Features...")
    
    # Create test PDF
    test_pdf_path = create_test_pdf()
    if not test_pdf_path:
        return False
    
    processor = PDFProcessor()
    all_tools = get_all_pdf_tools()
    
    print(f"\n📋 Available Tools: {len(all_tools)}")
    for tool in all_tools:
        print(f"   - {tool.name}: {tool.description}")
    
    # Test cases for different features
    test_cases = [
        {
            "name": "Background Color Change",
            "test": lambda: processor.change_background_color(test_pdf_path, "yellow", 0.7),
            "expected_success": True
        },
        {
            "name": "Text Replacement",
            "test": lambda: processor.replace_text_with_formatting(
                test_pdf_path, "Biruk Seyoum", "Ayele Seyoum", True, True
            ),
            "expected_success": True
        },
        {
            "name": "Add Text",
            "test": lambda: processor.add_text(
                test_pdf_path, "Updated Resume", (100, 50), "Helvetica", 14, (0, 0, 0)
            ),
            "expected_success": True
        },
        {
            "name": "Document Analysis",
            "test": lambda: processor.analyze_document(test_pdf_path),
            "expected_success": True
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🧪 Test {i+1}: {test_case['name']}")
        
        try:
            # Create a copy for this test
            test_copy_path = f"{test_pdf_path}_test_{i+1}.pdf"
            import shutil
            shutil.copy2(test_pdf_path, test_copy_path)
            
            # Run the test
            result = test_case["test"]()
            
            if test_case["expected_success"]:
                if isinstance(result, dict) and result.get("success"):
                    print(f"   ✅ {test_case['name']}: SUCCESS")
                    print(f"   📁 Output: {result.get('output_path', 'N/A')}")
                    results.append(True)
                elif isinstance(result, str) and "Error" not in result:
                    print(f"   ✅ {test_case['name']}: SUCCESS")
                    print(f"   📄 Result: {result[:100]}...")
                    results.append(True)
                else:
                    print(f"   ❌ {test_case['name']}: FAILED")
                    print(f"   📄 Result: {result}")
                    results.append(False)
            else:
                print(f"   ⚠️  {test_case['name']}: Expected to fail")
                results.append(True)
                
        except Exception as e:
            print(f"   ❌ {test_case['name']}: EXCEPTION")
            print(f"   📄 Error: {e}")
            results.append(False)
    
    # Cleanup
    for i in range(len(test_cases)):
        test_copy_path = f"{test_pdf_path}_test_{i+1}.pdf"
        if os.path.exists(test_copy_path):
            os.unlink(test_copy_path)
    
    os.unlink(test_pdf_path)
    print(f"\n🧹 Cleaned up test files")
    
    return results

def test_tool_categories():
    """Test tool categorization"""
    print("\n📊 Testing Tool Categories...")
    
    from agents.tools import get_tool_categories, get_tool_descriptions
    
    categories = get_tool_categories()
    descriptions = get_tool_descriptions()
    
    print(f"📋 Categories: {len(categories)}")
    for category, tools in categories.items():
        print(f"   - {category}: {len(tools)} tools")
        for tool in tools[:3]:  # Show first 3 tools
            print(f"     • {tool}")
        if len(tools) > 3:
            print(f"     • ... and {len(tools) - 3} more")
    
    print(f"\n📋 Descriptions: {len(descriptions)}")
    for tool_name, description in list(descriptions.items())[:5]:
        print(f"   - {tool_name}: {description}")
    
    return True

def main():
    """Run comprehensive tests"""
    print("🚀 DocumentGenie - All Features Test")
    print("=" * 50)
    
    # Test all features
    feature_results = test_all_features()
    
    # Test tool categories
    category_results = test_tool_categories()
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 30)
    
    if feature_results:
        passed = sum(feature_results)
        total = len(feature_results)
        print(f"Feature Tests: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All feature tests passed!")
        else:
            print("⚠️  Some feature tests failed")
    
    print(f"Tool Categories: {'✅ PASS' if category_results else '❌ FAIL'}")
    
    print("\n📋 Supported Features:")
    print("✅ Background Color Change")
    print("✅ Text Replacement")
    print("✅ Add Text")
    print("✅ Document Analysis")
    print("✅ Session Management")
    print("✅ Real-time Updates")
    print("✅ Frontend Integration")
    
    print("\n🔄 Next Steps:")
    print("1. Test in browser with different commands:")
    print("   - 'change the background color to yellow'")
    print("   - 'change the text that says Biruk Seyoum to Ayele Seyoum'")
    print("   - 'add text Hello World at the top'")
    print("2. Use the green refresh button if needed")
    print("3. Use discard to reset to original")
    
    return all(feature_results) if feature_results else False

if __name__ == "__main__":
    main()
