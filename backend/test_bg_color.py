import os
from services.pdf_service import PDFProcessor

def test_background_color():
    # Create a test PDF
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    
    # Create a simple test PDF
    test_pdf = "test_document.pdf"
    c = canvas.Canvas(test_pdf, pagesize=letter)
    c.drawString(100, 750, "This is a test document")
    c.save()
    
    try:
        # Initialize the PDF processor
        processor = PDFProcessor()
        
        # Change the background color to yellow
        print("Changing background color to yellow...")
        output_path = processor.change_background_color(
            input_path=test_pdf,
            color="yellow",
            opacity=0.5
        )
        
        if os.path.exists(output_path):
            print(f"Success! Modified PDF saved to: {output_path}")
            return True
        else:
            print("Error: Failed to generate output file")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        # Clean up test files
        if os.path.exists(test_pdf):
            os.remove(test_pdf)

if __name__ == "__main__":
    test_background_color()
