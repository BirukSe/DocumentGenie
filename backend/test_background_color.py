import os
import sys
from services.pdf_service import PDFProcessor

def test_change_background_color():
    # Get the test PDF path from command line or use a default
    if len(sys.argv) > 1:
        input_pdf = sys.argv[1]
    else:
        print("Please provide the path to a PDF file as an argument")
        return
    
    if not os.path.exists(input_pdf):
        print(f"Error: File not found: {input_pdf}")
        return
    
    try:
        # Initialize the PDF processor
        processor = PDFProcessor()
        
        # Test changing background to yellow
        print(f"Changing background color of {input_pdf} to yellow...")
        output_path = processor.change_background_color(
            input_path=input_pdf,
            color="yellow",
            opacity=0.3
        )
        
        print(f"Success! Modified PDF saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_change_background_color()
